"""
Handle-Aware Vector Store for Semantic Versioning

Extends MCardVectorStore to enable semantic similarity detection
across MCard versions linked to handles.

Key Features:
- Link MCards to handles during indexing
- Compare versions within a handle by semantic similarity
- Filter searches by handle
- Sort version history by distance to current or query
- Automatic upgrade type classification based on semantic delta

See: docs/architecture/Handle_Vector_Similarity_Design.md
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from mcard import MCard

from .schema import HANDLE_VECTOR_SCHEMAS
from .store import (
    MCardVectorStore,
    VectorSearchResult,
    cosine_similarity,
    euclidean_distance,
    deserialize_vector,
)

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Data Classes
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class HandleVersion:
    """A version in a handle's history with embedding info."""
    hash: str
    version_order: int      # 0 = current, 1 = previous, etc.
    is_current: bool
    created_at: str
    parent_hash: Optional[str] = None
    embedding_id: Optional[int] = None
    semantic_delta: Optional[float] = None
    upgrade_type: Optional[str] = None
    
    @property
    def has_embedding(self) -> bool:
        return self.embedding_id is not None


@dataclass
class VersionSimilarityResult:
    """Result from version similarity comparison."""
    hash: str
    version_order: int
    similarity_to_current: float    # Cosine similarity to current version
    distance_to_current: float      # Euclidean distance to current version
    similarity_to_query: Optional[float] = None  # If query provided
    parent_hash: Optional[str] = None
    upgrade_type: Optional[str] = None


# ─────────────────────────────────────────────────────────────────────────────
# Upgrade Type Classification
# ─────────────────────────────────────────────────────────────────────────────

def classify_upgrade_type(semantic_delta: float) -> str:
    """
    Classify upgrade type based on semantic similarity to parent.
    
    Thresholds:
    - >= 0.95: trivial (formatting, typo fixes)
    - 0.85 - 0.94: minor (small edits, clarifications)
    - 0.70 - 0.84: major (significant content changes)
    - < 0.70: breaking (major semantic drift)
    
    Args:
        semantic_delta: Cosine similarity to parent version
        
    Returns:
        Upgrade type string: 'trivial', 'minor', 'major', or 'breaking'
    """
    if semantic_delta >= 0.95:
        return 'trivial'
    elif semantic_delta >= 0.85:
        return 'minor'
    elif semantic_delta >= 0.70:
        return 'major'
    else:
        return 'breaking'


# ─────────────────────────────────────────────────────────────────────────────
# Handle-Aware Vector Store
# ─────────────────────────────────────────────────────────────────────────────

class HandleVectorStore(MCardVectorStore):
    """
    Extended vector store with handle-aware version similarity.
    
    This class implements the Handle-Hash Duality pattern with semantic
    awareness, enabling:
    
    - Version tracking via handles
    - Semantic similarity detection across versions
    - Intelligent upgrade classification
    - Cross-version semantic search
    
    Architecture:
    - Handles remain stable identifiers (Proxy Pattern)
    - Hashes reference immutable content (Content-Addressing)
    - Embeddings enable semantic understanding (Vector Search)
    
    Usage:
        store = HandleVectorStore(db_path="vectors.db")
        
        # Index with handle association
        store.index_with_handle(mcard, handle="my_document")
        
        # Get versions sorted by similarity to current
        versions = store.get_versions_by_similarity("my_document")
        
        # Find versions similar to a query
        versions = store.search_handle_versions("my_document", "machine learning")
        
        # Compute all pairwise distances
        distances = store.compute_version_distances("my_document")
    
    See Also:
        - MCardVectorStore: Base vector store implementation
        - docs/architecture/Handle_Vector_Similarity_Design.md
        - docs/architecture/Handle-Hash_Duality_and_Scale-Free_Architecture.md
    """
    
    def __init__(self, *args, **kwargs):
        """
        Initialize HandleVectorStore.
        
        Inherits all arguments from MCardVectorStore and adds
        handle-version tables for semantic versioning.
        """
        super().__init__(*args, **kwargs)
        self._init_handle_tables()
    
    def _init_handle_tables(self):
        """Create handle-vector bridge tables for semantic versioning."""
        cursor = self.conn.cursor()
        
        # Create handle-version-vector bridge table
        cursor.execute(HANDLE_VECTOR_SCHEMAS['handle_version_vectors'])
        
        # Create indexes (split by semicolons and execute each)
        for statement in HANDLE_VECTOR_SCHEMAS['handle_version_vectors_indexes'].split(';'):
            statement = statement.strip()
            if statement:
                cursor.execute(statement)
        
        # Create similarity cache table
        cursor.execute(HANDLE_VECTOR_SCHEMAS['similarity_cache'])
        cursor.execute(HANDLE_VECTOR_SCHEMAS['similarity_cache_index'])
        
        self.conn.commit()
        logger.debug("Initialized handle-vector bridge tables")
    
    # ─────────────────────────────────────────────────────────────────────────
    # Indexing with Handle Association
    # ─────────────────────────────────────────────────────────────────────────
    
    def index_with_handle(
        self, 
        mcard: MCard, 
        handle: str,
        is_current: bool = True,
        chunk: bool = True
    ) -> int:
        """
        Index an MCard and associate it with a handle.
        
        This method:
        1. Indexes the MCard content with embeddings (via base class)
        2. Links the MCard hash to the handle with version tracking
        3. Computes semantic delta from parent version (if exists)
        4. Classifies the upgrade type based on similarity
        
        Args:
            mcard: MCard to index
            handle: Handle name to associate with
            is_current: Whether this is the current version
            chunk: Whether to chunk long content
            
        Returns:
            Number of vectors indexed (0 if content couldn't be indexed)
            
        Example:
            >>> doc_v1 = create_mcard("Introduction to ML...")
            >>> store.index_with_handle(doc_v1, handle="ml_intro")
            1
            >>> doc_v2 = create_mcard("Introduction to ML with more detail...")
            >>> store.index_with_handle(doc_v2, handle="ml_intro")
            1
        """
        # Standard indexing (generates embeddings)
        indexed = self.index(mcard, chunk=chunk)
        
        if indexed == 0:
            logger.warning(f"MCard {mcard.hash[:8]} could not be indexed, skipping handle link")
            return 0
        
        cursor = self.conn.cursor()
        now = datetime.now(timezone.utc).isoformat()
        
        # Get embedding ID for this hash (chunk 0)
        cursor.execute("""
            SELECT id FROM mcard_vector_metadata 
            WHERE hash = ? AND chunk_index = 0 LIMIT 1
        """, (mcard.hash,))
        row = cursor.fetchone()
        embedding_id = row[0] if row else None
        
        # Get current version info for calculating semantic delta
        parent_hash = None
        semantic_delta = None
        upgrade_type = None
        
        if is_current:
            # Get the current version before updating
            cursor.execute("""
                SELECT hash, embedding_id FROM handle_version_vectors 
                WHERE handle = ? AND is_current = TRUE LIMIT 1
            """, (handle,))
            current_row = cursor.fetchone()
            
            if current_row:
                parent_hash = current_row[0]
                parent_embedding_id = current_row[1]
                
                # Calculate semantic delta if both have embeddings
                if embedding_id and parent_embedding_id:
                    new_embedding = self._get_embedding(mcard.hash)
                    parent_embedding = self._get_embedding(parent_hash)
                    
                    if new_embedding and parent_embedding:
                        semantic_delta = cosine_similarity(new_embedding, parent_embedding)
                        upgrade_type = classify_upgrade_type(semantic_delta)
                        logger.debug(
                            f"Semantic delta for {handle}: {semantic_delta:.4f} ({upgrade_type})"
                        )
            
            # Shift existing versions down
            cursor.execute("""
                UPDATE handle_version_vectors 
                SET version_order = version_order + 1, is_current = FALSE
                WHERE handle = ?
            """, (handle,))
            version_order = 0
        else:
            # Append as non-current version
            cursor.execute("""
                SELECT COALESCE(MAX(version_order), -1) + 1 
                FROM handle_version_vectors 
                WHERE handle = ?
            """, (handle,))
            version_order = cursor.fetchone()[0]
        
        # Insert version record
        cursor.execute("""
            INSERT OR REPLACE INTO handle_version_vectors 
            (handle, hash, parent_hash, version_order, is_current, 
             embedding_id, semantic_delta_from_parent, upgrade_type, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            handle, mcard.hash, parent_hash, version_order, is_current,
            embedding_id, semantic_delta, upgrade_type, now
        ))
        
        self.conn.commit()
        logger.info(
            f"Indexed MCard {mcard.hash[:8]} for handle '{handle}' "
            f"(v{version_order}, current={is_current}, type={upgrade_type})"
        )
        return indexed
    
    # ─────────────────────────────────────────────────────────────────────────
    # Version Retrieval
    # ─────────────────────────────────────────────────────────────────────────
    
    def get_handle_versions(self, handle: str) -> List[HandleVersion]:
        """
        Get all versions for a handle.
        
        Args:
            handle: Handle name to query
            
        Returns:
            List of HandleVersion objects, ordered by version_order (0 = current)
            
        Example:
            >>> versions = store.get_handle_versions("ml_intro")
            >>> for v in versions:
            ...     print(f"v{v.version_order}: {v.hash[:8]} ({v.upgrade_type})")
            v0: abc12345 (None)  # current
            v1: def67890 (minor)
            v2: xyz11223 (major)
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT hash, version_order, is_current, embedding_id, created_at,
                   parent_hash, semantic_delta_from_parent, upgrade_type
            FROM handle_version_vectors
            WHERE handle = ?
            ORDER BY version_order
        """, (handle,))
        
        return [
            HandleVersion(
                hash=row[0],
                version_order=row[1],
                is_current=bool(row[2]),
                embedding_id=row[3],
                created_at=row[4],
                parent_hash=row[5],
                semantic_delta=row[6],
                upgrade_type=row[7],
            )
            for row in cursor.fetchall()
        ]
    
    def get_handle_version_hashes(self, handle: str) -> List[str]:
        """
        Get all version hashes for a handle.
        
        Args:
            handle: Handle name to query
            
        Returns:
            List of hashes, ordered by version_order
        """
        versions = self.get_handle_versions(handle)
        return [v.hash for v in versions]
    
    def get_current_version(self, handle: str) -> Optional[HandleVersion]:
        """
        Get the current version for a handle.
        
        Args:
            handle: Handle name to query
            
        Returns:
            HandleVersion for current version, or None if handle not found
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT hash, version_order, is_current, embedding_id, created_at,
                   parent_hash, semantic_delta_from_parent, upgrade_type
            FROM handle_version_vectors
            WHERE handle = ? AND is_current = TRUE
            LIMIT 1
        """, (handle,))
        
        row = cursor.fetchone()
        if not row:
            return None
        
        return HandleVersion(
            hash=row[0],
            version_order=row[1],
            is_current=bool(row[2]),
            embedding_id=row[3],
            created_at=row[4],
            parent_hash=row[5],
            semantic_delta=row[6],
            upgrade_type=row[7],
        )
    
    # ─────────────────────────────────────────────────────────────────────────
    # Semantic Similarity Operations
    # ─────────────────────────────────────────────────────────────────────────
    
    def get_versions_by_similarity(
        self,
        handle: str,
        reference_hash: str = None,
        metric: str = 'cosine'
    ) -> List[VersionSimilarityResult]:
        """
        Get versions for a handle, sorted by similarity to a reference.
        
        Args:
            handle: Handle name
            reference_hash: Hash to compare against (default: current version)
            metric: 'cosine' (higher = more similar) or 'euclidean' (lower = more similar)
            
        Returns:
            List of VersionSimilarityResult, sorted by similarity
            
        Example:
            >>> versions = store.get_versions_by_similarity("ml_intro")
            >>> for v in versions:
            ...     print(f"v{v.version_order}: sim={v.similarity_to_current:.4f}")
            v0: sim=1.0000  (current - self-similarity)
            v1: sim=0.8234  (most similar to current)
            v2: sim=0.6521  (least similar)
        """
        versions = self.get_handle_versions(handle)
        
        if not versions:
            return []
        
        # Determine reference hash
        if reference_hash is None:
            for v in versions:
                if v.is_current:
                    reference_hash = v.hash
                    break
            if reference_hash is None and versions:
                reference_hash = versions[0].hash
        
        # Get reference embedding
        ref_embedding = self._get_embedding(reference_hash)
        if ref_embedding is None:
            logger.warning(f"No embedding found for reference hash {reference_hash[:8]}")
            return []
        
        # Calculate similarities
        results = []
        for v in versions:
            if v.hash == reference_hash:
                # Self-similarity
                similarity = 1.0
                distance = 0.0
            else:
                v_embedding = self._get_embedding(v.hash)
                if v_embedding is None:
                    logger.debug(f"Skipping version {v.hash[:8]} - no embedding")
                    continue
                
                similarity = cosine_similarity(ref_embedding, v_embedding)
                distance = euclidean_distance(ref_embedding, v_embedding)
            
            results.append(VersionSimilarityResult(
                hash=v.hash,
                version_order=v.version_order,
                similarity_to_current=similarity,
                distance_to_current=distance,
                parent_hash=v.parent_hash,
                upgrade_type=v.upgrade_type,
            ))
        
        # Sort by similarity (descending) or distance (ascending)
        if metric == 'cosine':
            results.sort(key=lambda x: x.similarity_to_current, reverse=True)
        else:
            results.sort(key=lambda x: x.distance_to_current)
        
        return results
    
    def search_handle_versions(
        self,
        handle: str,
        query: str,
        k: int = None
    ) -> List[VersionSimilarityResult]:
        """
        Search within a handle's versions by semantic query.
        
        Useful for finding which version of a document best matches
        a specific concept or topic.
        
        Args:
            handle: Handle name to filter by
            query: Search query text
            k: Number of results (default from config)
            
        Returns:
            List of VersionSimilarityResult with query similarity scores
            
        Example:
            >>> results = store.search_handle_versions("ml_intro", "neural networks")
            >>> for r in results:
            ...     print(f"v{r.version_order}: query_sim={r.similarity_to_query:.4f}")
            v0: query_sim=0.8923  (current version mentions neural networks)
            v1: query_sim=0.4123  (mentions AI but not directly)
        """
        k = k or self.config.top_k
        
        # Get version hashes for this handle
        version_hashes = self.get_handle_version_hashes(handle)
        if not version_hashes:
            return []
        
        # Search with hash filter (uses base class method)
        results = self.search(query, k=k, filter_hashes=version_hashes)
        
        # Get version info for enrichment
        versions = {v.hash: v for v in self.get_handle_versions(handle)}
        
        # Enrich results with version info
        enriched = []
        for r in results:
            v = versions.get(r.hash)
            if v:
                enriched.append(VersionSimilarityResult(
                    hash=r.hash,
                    version_order=v.version_order,
                    similarity_to_current=0.0,  # Not computed in this method
                    distance_to_current=0.0,    # Not computed in this method
                    similarity_to_query=r.score,
                    parent_hash=v.parent_hash,
                    upgrade_type=v.upgrade_type,
                ))
        
        return enriched
    
    def compute_version_distances(
        self, 
        handle: str,
        cache: bool = True
    ) -> Dict[Tuple[str, str], float]:
        """
        Compute pairwise cosine similarities between all versions of a handle.
        
        Optionally caches results in the version_similarity_cache table.
        
        Args:
            handle: Handle name
            cache: Whether to cache computed similarities
            
        Returns:
            Dict mapping (hash_a, hash_b) tuple to cosine similarity
            
        Example:
            >>> distances = store.compute_version_distances("ml_intro")
            >>> for (h1, h2), sim in sorted(distances.items()):
            ...     print(f"{h1[:8]} <-> {h2[:8]}: {sim:.4f}")
        """
        versions = self.get_handle_versions(handle)
        embeddings: Dict[str, List[float]] = {}
        
        for v in versions:
            emb = self._get_embedding(v.hash)
            if emb:
                embeddings[v.hash] = emb
        
        distances: Dict[Tuple[str, str], float] = {}
        hashes = list(embeddings.keys())
        now = datetime.now(timezone.utc).isoformat()
        
        cursor = self.conn.cursor()
        
        for i, h1 in enumerate(hashes):
            for h2 in hashes[i:]:
                if h1 == h2:
                    sim = 1.0
                else:
                    sim = cosine_similarity(embeddings[h1], embeddings[h2])
                    dist = euclidean_distance(embeddings[h1], embeddings[h2])
                    
                    # Cache the result
                    if cache:
                        try:
                            cursor.execute("""
                                INSERT OR REPLACE INTO version_similarity_cache
                                (handle, hash_a, hash_b, similarity_score, distance_euclidean, computed_at)
                                VALUES (?, ?, ?, ?, ?, ?)
                            """, (handle, h1, h2, sim, dist, now))
                        except Exception as e:
                            logger.warning(f"Failed to cache similarity for {h1[:8]}<->{h2[:8]}: {e}")
                
                distances[(h1, h2)] = sim
                distances[(h2, h1)] = sim
        
        if cache:
            self.conn.commit()
        
        return distances
    
    # ─────────────────────────────────────────────────────────────────────────
    # Embedding Retrieval (Internal)
    # ─────────────────────────────────────────────────────────────────────────
    
    def _get_embedding(self, hash: str, chunk_index: int = 0) -> Optional[List[float]]:
        """
        Get embedding vector for a hash.
        
        Args:
            hash: MCard hash
            chunk_index: Chunk index (default 0 for first/whole chunk)
            
        Returns:
            Embedding vector as list of floats, or None if not found
        """
        cursor = self.conn.cursor()
        
        # Get metadata ID
        cursor.execute("""
            SELECT id FROM mcard_vector_metadata 
            WHERE hash = ? AND chunk_index = ?
        """, (hash, chunk_index))
        row = cursor.fetchone()
        
        if not row:
            return None
        
        metadata_id = row[0]
        
        # Get embedding from appropriate table
        if self.has_vec_extension:
            cursor.execute("""
                SELECT embedding FROM mcard_vec WHERE metadata_id = ?
            """, (metadata_id,))
        else:
            cursor.execute("""
                SELECT embedding FROM mcard_embeddings WHERE metadata_id = ?
            """, (metadata_id,))
        
        row = cursor.fetchone()
        if row:
            return deserialize_vector(row[0])
        return None
    
    # ─────────────────────────────────────────────────────────────────────────
    # Utility Methods
    # ─────────────────────────────────────────────────────────────────────────
    
    def list_handles(self) -> List[str]:
        """
        List all handles with indexed versions.
        
        Returns:
            List of unique handle names
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT DISTINCT handle FROM handle_version_vectors ORDER BY handle")
        return [row[0] for row in cursor.fetchall()]
    
    def count_versions(self, handle: str) -> int:
        """
        Count versions for a handle.
        
        Args:
            handle: Handle name
            
        Returns:
            Number of versions
        """
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM handle_version_vectors WHERE handle = ?",
            (handle,)
        )
        return cursor.fetchone()[0]
    
    def delete_handle(self, handle: str) -> int:
        """
        Delete all version records for a handle.
        
        Note: This only removes the handle-version associations,
        not the underlying MCard embeddings.
        
        Args:
            handle: Handle name
            
        Returns:
            Number of version records deleted
        """
        cursor = self.conn.cursor()
        
        # Delete similarity cache
        cursor.execute(
            "DELETE FROM version_similarity_cache WHERE handle = ?",
            (handle,)
        )
        
        # Delete version records
        cursor.execute(
            "DELETE FROM handle_version_vectors WHERE handle = ?",
            (handle,)
        )
        deleted = cursor.rowcount
        
        self.conn.commit()
        logger.info(f"Deleted {deleted} version records for handle '{handle}'")
        return deleted
    
    def get_info(self) -> Dict[str, Any]:
        """Get extended vector store information including handle stats."""
        info = super().get_info()
        
        # Add handle-specific stats
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(DISTINCT handle) FROM handle_version_vectors")
        info['handle_count'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM handle_version_vectors")
        info['version_count'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM version_similarity_cache")
        info['cached_similarities'] = cursor.fetchone()[0]
        
        return info
