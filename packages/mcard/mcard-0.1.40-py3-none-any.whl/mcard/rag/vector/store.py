"""
MCard Vector Store

SQLite-based vector storage for MCard semantic search.
Supports sqlite-vec extension for optimized KNN queries,
with fallback to brute-force similarity when extension unavailable.
"""

import json
import logging
import sqlite3
import struct
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from mcard import MCard

from ..config import RAGConfig, DEFAULT_RAG_CONFIG
from ..embeddings import EmbeddingProvider, OllamaEmbeddingProvider
from .schema import VECTOR_SCHEMAS, get_vec0_schema

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Vector Serialization Utilities
# ─────────────────────────────────────────────────────────────────────────────

def serialize_vector(vector: List[float]) -> bytes:
    """
    Serialize a float vector to bytes for SQLite storage.
    
    Uses little-endian float32 format compatible with sqlite-vec.
    """
    return struct.pack(f'<{len(vector)}f', *vector)


def deserialize_vector(blob: bytes) -> List[float]:
    """
    Deserialize bytes back to a float vector.
    """
    count = len(blob) // 4  # 4 bytes per float32
    return list(struct.unpack(f'<{count}f', blob))


def cosine_similarity(a: List[float], b: List[float]) -> float:
    """
    Calculate cosine similarity between two vectors.
    
    Returns a value between -1 and 1, where 1 means identical direction.
    """
    if len(a) != len(b):
        raise ValueError(f"Vector length mismatch: {len(a)} vs {len(b)}")
    
    dot_product = sum(x * y for x, y in zip(a, b))
    norm_a = sum(x * x for x in a) ** 0.5
    norm_b = sum(x * x for x in b) ** 0.5
    
    if norm_a == 0 or norm_b == 0:
        return 0.0
    
    return dot_product / (norm_a * norm_b)


def euclidean_distance(a: List[float], b: List[float]) -> float:
    """Calculate Euclidean (L2) distance between two vectors."""
    if len(a) != len(b):
        raise ValueError(f"Vector length mismatch: {len(a)} vs {len(b)}")
    
    return sum((x - y) ** 2 for x, y in zip(a, b)) ** 0.5


# ─────────────────────────────────────────────────────────────────────────────
# Search Result
# ─────────────────────────────────────────────────────────────────────────────

class VectorSearchResult:
    """Result from a vector similarity search."""
    
    def __init__(
        self,
        hash: str,
        score: float,
        chunk_index: int = 0,
        chunk_text: Optional[str] = None,
        metadata: Optional[Dict] = None
    ):
        self.hash = hash
        self.score = score  # Similarity score (higher = more similar)
        self.chunk_index = chunk_index
        self.chunk_text = chunk_text
        self.metadata = metadata or {}
    
    def __repr__(self):
        return f"VectorSearchResult(hash={self.hash[:8]}..., score={self.score:.4f})"


# ─────────────────────────────────────────────────────────────────────────────
# MCard Vector Store
# ─────────────────────────────────────────────────────────────────────────────

class MCardVectorStore:
    """
    Vector storage for MCard embeddings.
    
    Features:
    - Automatic embedding generation via Ollama
    - sqlite-vec extension for optimized KNN (with fallback)
    - Chunking for long documents
    - Full-text search for hybrid retrieval
    
    Usage:
        store = MCardVectorStore(db_path="vectors.db")
        
        # Index an MCard
        store.index(mcard)
        
        # Search similar content
        results = store.search("What is MCard?", k=5)
        for result in results:
            print(f"{result.hash}: {result.score}")
    """
    
    def __init__(
        self,
        db_path: str = None,
        config: RAGConfig = None,
        embedding_provider: EmbeddingProvider = None
    ):
        """
        Initialize vector store.
        
        Args:
            db_path: Path to SQLite database (None = in-memory)
            config: RAG configuration
            embedding_provider: Custom embedding provider (default: Ollama)
        """
        self.config = config or DEFAULT_RAG_CONFIG
        self.db_path = db_path or ':memory:'
        
        # Initialize embedding provider
        if embedding_provider:
            self.embedder = embedding_provider
        else:
            self.embedder = OllamaEmbeddingProvider(
                model=self.config.embedding_model,
                base_url=self.config.ollama_base_url
            )
        
        # Initialize database
        self.conn = self._init_database()
        self.has_vec_extension = self._try_load_vec_extension()
    
    def _init_database(self) -> sqlite3.Connection:
        """Initialize SQLite connection and create tables."""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        cursor = conn.cursor()
        
        # Create metadata and fallback tables
        cursor.execute(VECTOR_SCHEMAS['metadata'])
        cursor.execute(VECTOR_SCHEMAS['metadata_index'])
        cursor.execute(VECTOR_SCHEMAS['embeddings'])
        
        # Create FTS table for hybrid search
        if self.config.enable_hybrid_search:
            cursor.execute(VECTOR_SCHEMAS['fts'])
        
        conn.commit()
        logger.debug(f"Initialized vector store at {self.db_path}")
        return conn
    
    def _try_load_vec_extension(self) -> bool:
        """Try to load sqlite-vec extension."""
        try:
            import sqlite_vec
            
            self.conn.enable_load_extension(True)
            sqlite_vec.load(self.conn)
            
            # Create vec0 virtual table
            schema = get_vec0_schema(self.embedder.dimensions)
            self.conn.execute(schema)
            self.conn.commit()
            
            logger.info(f"sqlite-vec extension loaded (dimensions: {self.embedder.dimensions})")
            return True
            
        except ImportError:
            logger.warning("sqlite-vec not installed. Using fallback similarity search. "
                         "Install with: pip install sqlite-vec")
            return False
        except Exception as e:
            logger.warning(f"Failed to load sqlite-vec: {e}. Using fallback.")
            return False
    
    def _chunk_text(self, text: str) -> List[str]:
        """
        Split text into overlapping chunks.
        
        Args:
            text: Input text
            
        Returns:
            List of text chunks
        """
        if len(text) <= self.config.chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + self.config.chunk_size
            
            # Try to break at sentence boundary
            if end < len(text):
                # Look for sentence end within last 20% of chunk
                search_start = int(end - self.config.chunk_size * 0.2)
                for sep in ['. ', '.\n', '!\n', '?\n', '\n\n']:
                    pos = text.rfind(sep, search_start, end)
                    if pos > start:
                        end = pos + len(sep)
                        break
            
            chunks.append(text[start:end].strip())
            start = end - self.config.chunk_overlap
        
        return [c for c in chunks if c]  # Filter empty
    
    def index(self, mcard: MCard, chunk: bool = True) -> int:
        """
        Index an MCard with its embedding(s).
        
        Args:
            mcard: MCard to index
            chunk: Whether to chunk long content
            
        Returns:
            Number of vectors indexed
        """
        # Get content as text
        content = mcard.get_content()
        if isinstance(content, bytes):
            try:
                content = content.decode('utf-8')
            except UnicodeDecodeError:
                logger.warning(f"Cannot decode MCard {mcard.hash[:8]} as text, skipping")
                return 0
        
        content = str(content).strip()
        if not content:
            logger.warning(f"MCard {mcard.hash[:8]} has empty content, skipping")
            return 0
        
        # Chunk if needed
        if chunk and len(content) > self.config.chunk_size:
            chunks = self._chunk_text(content)
        else:
            chunks = [content]
        
        # Generate embeddings
        try:
            embeddings = self.embedder.embed_batch(chunks)
        except Exception as e:
            logger.error(f"Failed to generate embeddings for {mcard.hash[:8]}: {e}")
            return 0
        
        now = datetime.now(timezone.utc).isoformat()
        indexed = 0
        cursor = self.conn.cursor()
        
        for i, (chunk_text, embedding) in enumerate(zip(chunks, embeddings)):
            try:
                # Insert metadata
                cursor.execute("""
                    INSERT OR REPLACE INTO mcard_vector_metadata 
                    (hash, model_name, dimensions, chunk_index, chunk_total, chunk_text, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    mcard.hash,
                    self.embedder.model_name,
                    len(embedding),
                    i,
                    len(chunks),
                    chunk_text[:500] if len(chunk_text) > 500 else chunk_text,
                    now
                ))
                
                metadata_id = cursor.lastrowid
                embedding_blob = serialize_vector(embedding)
                
                # Insert into vec0 or fallback table
                if self.has_vec_extension:
                    cursor.execute("""
                        INSERT INTO mcard_vec (metadata_id, embedding)
                        VALUES (?, ?)
                    """, (metadata_id, embedding_blob))
                else:
                    cursor.execute("""
                        INSERT OR REPLACE INTO mcard_embeddings (metadata_id, embedding)
                        VALUES (?, ?)
                    """, (metadata_id, embedding_blob))
                
                indexed += 1
                
            except Exception as e:
                logger.error(f"Failed to index chunk {i} of {mcard.hash[:8]}: {e}")
        
        # Index in FTS for hybrid search
        if self.config.enable_hybrid_search:
            try:
                cursor.execute("""
                    INSERT OR REPLACE INTO mcard_fts (hash, content)
                    VALUES (?, ?)
                """, (mcard.hash, content[:10000]))  # Limit FTS content
            except Exception as e:
                logger.warning(f"FTS indexing failed for {mcard.hash[:8]}: {e}")
        
        self.conn.commit()
        logger.debug(f"Indexed {indexed} vectors for MCard {mcard.hash[:8]}")
        return indexed
    
    def search(
        self,
        query: str,
        k: int = None,
        filter_hashes: List[str] = None
    ) -> List[VectorSearchResult]:
        """
        Search for similar MCards by semantic similarity.
        
        Args:
            query: Search query text
            k: Number of results (default from config)
            filter_hashes: Optional list of hashes to include
            
        Returns:
            List of VectorSearchResult sorted by similarity (descending)
        """
        k = k or self.config.top_k
        
        # Generate query embedding
        try:
            query_embedding = self.embedder.embed(query)
        except Exception as e:
            logger.error(f"Failed to embed query: {e}")
            return []
        
        if self.has_vec_extension:
            return self._search_vec0(query_embedding, k, filter_hashes)
        else:
            return self._search_fallback(query_embedding, k, filter_hashes)
    
    def _search_vec0(
        self,
        query_embedding: List[float],
        k: int,
        filter_hashes: List[str] = None
    ) -> List[VectorSearchResult]:
        """Search using sqlite-vec KNN."""
        query_blob = serialize_vector(query_embedding)
        
        cursor = self.conn.cursor()
        
        # KNN query using vec0 'k' constraint in a CTE for better optimization
        sql = """
            WITH matches AS (
                SELECT metadata_id, distance
                FROM mcard_vec
                WHERE embedding MATCH ?
                AND k = ?
            )
            SELECT 
                m.hash,
                m.chunk_index,
                m.chunk_text,
                matches.distance
            FROM matches
            JOIN mcard_vector_metadata m ON matches.metadata_id = m.id
            ORDER BY matches.distance
        """
        
        cursor.execute(sql, (query_blob, k * 2))  # Request more for post-filtering
        rows = cursor.fetchall()
        
        # Convert distance to similarity and deduplicate by hash
        results = []
        seen_hashes = set()
        
        for hash_val, chunk_idx, chunk_text, distance in rows:
            if filter_hashes and hash_val not in filter_hashes:
                continue
            if hash_val in seen_hashes and len(results) >= k:
                continue
            
            # Convert L2 distance to similarity score
            similarity = 1.0 / (1.0 + distance)
            
            if hash_val not in seen_hashes:
                seen_hashes.add(hash_val)
                results.append(VectorSearchResult(
                    hash=hash_val,
                    score=similarity,
                    chunk_index=chunk_idx,
                    chunk_text=chunk_text
                ))
            
            if len(results) >= k:
                break
        
        return results
    
    def _search_fallback(
        self,
        query_embedding: List[float],
        k: int,
        filter_hashes: List[str] = None
    ) -> List[VectorSearchResult]:
        """Search using brute-force similarity calculation."""
        cursor = self.conn.cursor()
        
        # Get all embeddings
        sql = """
            SELECT m.hash, m.chunk_index, m.chunk_text, e.embedding
            FROM mcard_embeddings e
            JOIN mcard_vector_metadata m ON e.metadata_id = m.id
        """
        
        if filter_hashes:
            placeholders = ','.join('?' * len(filter_hashes))
            sql += f" WHERE m.hash IN ({placeholders})"
            cursor.execute(sql, filter_hashes)
        else:
            cursor.execute(sql)
        
        # Calculate similarities
        candidates = []
        for hash_val, chunk_idx, chunk_text, embedding_blob in cursor.fetchall():
            embedding = deserialize_vector(embedding_blob)
            similarity = cosine_similarity(query_embedding, embedding)
            candidates.append((hash_val, chunk_idx, chunk_text, similarity))
        
        # Sort by similarity and deduplicate
        candidates.sort(key=lambda x: x[3], reverse=True)
        
        results = []
        seen_hashes = set()
        
        for hash_val, chunk_idx, chunk_text, similarity in candidates:
            if hash_val not in seen_hashes:
                seen_hashes.add(hash_val)
                results.append(VectorSearchResult(
                    hash=hash_val,
                    score=similarity,
                    chunk_index=chunk_idx,
                    chunk_text=chunk_text
                ))
            
            if len(results) >= k:
                break
        
        return results
    
    def hybrid_search(
        self,
        query: str,
        k: int = None,
        vector_weight: float = 0.7
    ) -> List[VectorSearchResult]:
        """
        Hybrid search combining vector similarity and full-text search.
        
        Args:
            query: Search query
            k: Number of results
            vector_weight: Weight for vector similarity (0-1)
            
        Returns:
            Combined and re-ranked results
        """
        k = k or self.config.top_k
        fts_weight = 1.0 - vector_weight
        
        # Vector search
        vector_results = self.search(query, k * 2)
        vector_scores = {r.hash: r.score * vector_weight for r in vector_results}
        
        # FTS search
        fts_scores = {}
        if self.config.enable_hybrid_search:
            cursor = self.conn.cursor()
            try:
                # Prepare FTS query - escape special characters and use OR
                fts_query = ' OR '.join(
                    f'"{word}"' for word in query.split() 
                    if word and len(word) > 1
                )
                if not fts_query:
                    fts_query = f'"{query}"'
                
                cursor.execute("""
                    SELECT hash, bm25(mcard_fts) as score
                    FROM mcard_fts
                    WHERE mcard_fts MATCH ?
                    ORDER BY score
                    LIMIT ?
                """, (fts_query, k * 2))
                
                for hash_val, score in cursor.fetchall():
                    # Normalize BM25 score (lower is better)
                    fts_scores[hash_val] = (1.0 / (1.0 - score)) * fts_weight
                    
            except Exception as e:
                logger.warning(f"FTS search failed: {e}")
        
        # Combine scores
        all_hashes = set(vector_scores.keys()) | set(fts_scores.keys())
        combined = []
        
        for hash_val in all_hashes:
            v_score = vector_scores.get(hash_val, 0)
            f_score = fts_scores.get(hash_val, 0)
            total = v_score + f_score
            
            # Get chunk info from vector results
            chunk_text = None
            for r in vector_results:
                if r.hash == hash_val:
                    chunk_text = r.chunk_text
                    break
            
            combined.append(VectorSearchResult(
                hash=hash_val,
                score=total,
                chunk_text=chunk_text,
                metadata={'vector_score': v_score, 'fts_score': f_score}
            ))
        
        # Sort and return top k
        combined.sort(key=lambda x: x.score, reverse=True)
        return combined[:k]
    
    def is_indexed(self, hash: str) -> bool:
        """Check if an MCard is already indexed."""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT 1 FROM mcard_vector_metadata WHERE hash = ? LIMIT 1",
            (hash,)
        )
        return cursor.fetchone() is not None
    
    def delete(self, hash: str) -> int:
        """Delete all vectors for an MCard."""
        cursor = self.conn.cursor()
        
        # Get metadata IDs
        cursor.execute(
            "SELECT id FROM mcard_vector_metadata WHERE hash = ?",
            (hash,)
        )
        ids = [row[0] for row in cursor.fetchall()]
        
        if not ids:
            return 0
        
        # Delete from all tables
        placeholders = ','.join('?' * len(ids))
        
        if self.has_vec_extension:
            cursor.execute(f"DELETE FROM mcard_vec WHERE metadata_id IN ({placeholders})", ids)
        else:
            cursor.execute(f"DELETE FROM mcard_embeddings WHERE metadata_id IN ({placeholders})", ids)
        
        cursor.execute(f"DELETE FROM mcard_vector_metadata WHERE id IN ({placeholders})", ids)
        
        if self.config.enable_hybrid_search:
            cursor.execute("DELETE FROM mcard_fts WHERE hash = ?", (hash,))
        
        self.conn.commit()
        return len(ids)
    
    def count(self) -> int:
        """Get total number of indexed vectors."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM mcard_vector_metadata")
        return cursor.fetchone()[0]
    
    def count_unique(self) -> int:
        """Get number of unique MCards indexed."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(DISTINCT hash) FROM mcard_vector_metadata")
        return cursor.fetchone()[0]
    
    def get_info(self) -> Dict[str, Any]:
        """Get vector store information."""
        return {
            'db_path': self.db_path,
            'embedding_model': self.embedder.model_name,
            'dimensions': self.embedder.dimensions,
            'has_vec_extension': self.has_vec_extension,
            'vector_count': self.count(),
            'unique_mcards': self.count_unique(),
            'hybrid_search_enabled': self.config.enable_hybrid_search,
        }
