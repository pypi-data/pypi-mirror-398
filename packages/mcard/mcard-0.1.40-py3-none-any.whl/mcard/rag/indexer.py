"""
Persistent Vector Indexer

Manages automatic indexing of MCards into the vector store,
with persistent storage alongside the main MCard database.
"""

import logging
import os
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set

from mcard import MCard
from mcard.model.card_collection import CardCollection

from .config import RAGConfig, DEFAULT_RAG_CONFIG
from .embeddings import OllamaEmbeddingProvider
from .vector import MCardVectorStore

logger = logging.getLogger(__name__)


class PersistentIndexer:
    """
    Manages persistent vector indexing for MCard collections.
    
    Features:
    - Automatic indexing when MCards are added
    - Persistent vector database alongside MCard database
    - Background indexing for large collections
    - Index status tracking
    
    Usage:
        from mcard.rag import PersistentIndexer
        
        indexer = PersistentIndexer()  # Uses default collection
        
        # Index all existing content
        stats = indexer.index_all()
        
        # Search
        results = indexer.search("query")
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls, *args, **kwargs):
        """Singleton pattern for global indexer."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(
        self,
        collection: CardCollection = None,
        config: RAGConfig = None,
        vector_db_path: str = None,
        auto_index: bool = False
    ):
        """
        Initialize persistent indexer.
        
        Args:
            collection: MCard collection (uses default if None)
            config: RAG configuration
            vector_db_path: Path to vector database (auto-derived if None)
            auto_index: Automatically index new MCards
        """
        if self._initialized:
            return
            
        from mcard import default_collection
        
        self.collection = collection or default_collection
        self.config = config or DEFAULT_RAG_CONFIG
        self.auto_index = auto_index
        
        # Derive vector DB path from MCard DB path
        if vector_db_path is None:
            mcard_db_path = self._get_mcard_db_path()
            if mcard_db_path and mcard_db_path != ':memory:':
                base_path = Path(mcard_db_path)
                vector_db_path = str(base_path.parent / f"{base_path.stem}_vectors.db")
            else:
                vector_db_path = ':memory:'
        
        self.vector_db_path = vector_db_path
        
        # Initialize embedding provider
        self.embedder = OllamaEmbeddingProvider(
            model=self.config.embedding_model,
            base_url=self.config.ollama_base_url
        )
        
        # Initialize vector store
        self.vector_store = MCardVectorStore(
            db_path=self.vector_db_path,
            config=self.config,
            embedding_provider=self.embedder
        )
        
        # Track indexing state
        self._indexing_in_progress = False
        self._indexed_hashes: Set[str] = set()
        self._load_indexed_hashes()
        
        self._initialized = True
        logger.info(f"PersistentIndexer initialized: {self.vector_db_path}")
    
    def _get_mcard_db_path(self) -> Optional[str]:
        """Get the path of the MCard database."""
        try:
            if hasattr(self.collection, 'engine'):
                engine = self.collection.engine
                if hasattr(engine, 'connection') and hasattr(engine.connection, 'db_path'):
                    return engine.connection.db_path
        except Exception:
            pass
        return None
    
    def _load_indexed_hashes(self):
        """Load the set of already-indexed hashes."""
        try:
            cursor = self.vector_store.conn.cursor()
            cursor.execute("SELECT DISTINCT hash FROM mcard_vector_metadata")
            self._indexed_hashes = {row[0] for row in cursor.fetchall()}
            logger.debug(f"Loaded {len(self._indexed_hashes)} indexed hashes")
        except Exception as e:
            logger.warning(f"Failed to load indexed hashes: {e}")
            self._indexed_hashes = set()
    
    def is_indexed(self, hash: str) -> bool:
        """Check if an MCard is already indexed."""
        return hash in self._indexed_hashes or self.vector_store.is_indexed(hash)
    
    def index_mcard(self, mcard: MCard, force: bool = False) -> bool:
        """
        Index a single MCard.
        
        Args:
            mcard: MCard to index
            force: Re-index even if already indexed
            
        Returns:
            True if indexed successfully
        """
        if not force and self.is_indexed(mcard.hash):
            logger.debug(f"MCard {mcard.hash[:8]} already indexed, skipping")
            return True
        
        try:
            count = self.vector_store.index(mcard)
            if count > 0:
                self._indexed_hashes.add(mcard.hash)
                logger.debug(f"Indexed MCard {mcard.hash[:8]} ({count} vectors)")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to index MCard {mcard.hash[:8]}: {e}")
            return False
    
    def index_all(
        self,
        force: bool = False,
        progress_callback: Callable[[int, int], None] = None,
        batch_size: int = 50
    ) -> Dict[str, int]:
        """
        Index all MCards in the collection.
        
        Args:
            force: Re-index even if already indexed
            progress_callback: Optional callback(current, total)
            batch_size: Number of cards to process at once
            
        Returns:
            Dictionary with 'indexed', 'skipped', 'failed', 'total' counts
        """
        if self._indexing_in_progress:
            logger.warning("Indexing already in progress")
            return {'indexed': 0, 'skipped': 0, 'failed': 0, 'total': 0, 'status': 'busy'}
        
        self._indexing_in_progress = True
        stats = {'indexed': 0, 'skipped': 0, 'failed': 0, 'total': 0}
        
        try:
            # Get all cards
            all_cards = self.collection.get_all_mcards_raw()
            stats['total'] = len(all_cards)
            
            for i, mcard in enumerate(all_cards):
                if not force and self.is_indexed(mcard.hash):
                    stats['skipped'] += 1
                elif self.index_mcard(mcard, force=force):
                    stats['indexed'] += 1
                else:
                    stats['failed'] += 1
                
                # Progress callback
                if progress_callback and (i + 1) % 10 == 0:
                    progress_callback(i + 1, stats['total'])
            
            logger.info(f"Indexing complete: {stats}")
            
        finally:
            self._indexing_in_progress = False
        
        return stats
    
    def search(
        self,
        query: str,
        k: int = None,
        hybrid: bool = True
    ) -> List[Any]:
        """
        Search for similar MCards.
        
        Args:
            query: Search query
            k: Number of results
            hybrid: Use hybrid (vector + FTS) search
            
        Returns:
            List of VectorSearchResult
        """
        if hybrid and self.config.enable_hybrid_search:
            return self.vector_store.hybrid_search(query, k)
        else:
            return self.vector_store.search(query, k)
    
    def delete(self, hash: str) -> bool:
        """Delete an MCard from the index."""
        count = self.vector_store.delete(hash)
        if count > 0:
            self._indexed_hashes.discard(hash)
            return True
        return False
    
    def clear(self):
        """Clear the entire vector index."""
        cursor = self.vector_store.conn.cursor()
        cursor.execute("DELETE FROM mcard_vector_metadata")
        cursor.execute("DELETE FROM mcard_embeddings")
        if self.config.enable_hybrid_search:
            cursor.execute("DELETE FROM mcard_fts")
        self.vector_store.conn.commit()
        self._indexed_hashes.clear()
        logger.info("Vector index cleared")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get indexer statistics."""
        return {
            'vector_db_path': self.vector_db_path,
            'embedding_model': self.embedder.model_name,
            'dimensions': self.embedder.dimensions,
            'indexed_count': len(self._indexed_hashes),
            'vector_count': self.vector_store.count(),
            'unique_mcards': self.vector_store.count_unique(),
            'has_vec_extension': self.vector_store.has_vec_extension,
            'hybrid_search_enabled': self.config.enable_hybrid_search,
            'indexing_in_progress': self._indexing_in_progress,
        }
    
    @classmethod
    def reset_instance(cls):
        """Reset the singleton instance (for testing)."""
        with cls._lock:
            cls._instance = None


# ─────────────────────────────────────────────────────────────────────────────
# Global Convenience Functions
# ─────────────────────────────────────────────────────────────────────────────

_default_indexer: Optional[PersistentIndexer] = None


def get_indexer(
    collection: CardCollection = None,
    config: RAGConfig = None
) -> PersistentIndexer:
    """
    Get or create the default persistent indexer.
    
    Args:
        collection: Optional collection override
        config: Optional configuration override
        
    Returns:
        PersistentIndexer instance
    """
    global _default_indexer
    
    if _default_indexer is None:
        _default_indexer = PersistentIndexer(
            collection=collection,
            config=config
        )
    
    return _default_indexer


def semantic_search(query: str, k: int = 5) -> List[Any]:
    """
    Convenience function for semantic search.
    
    Args:
        query: Search query
        k: Number of results
        
    Returns:
        List of VectorSearchResult
    """
    return get_indexer().search(query, k)


def index_mcard(mcard: MCard, force: bool = False) -> bool:
    """
    Convenience function to index an MCard.
    
    Args:
        mcard: MCard to index
        force: Re-index if exists
        
    Returns:
        True if indexed
    """
    return get_indexer().index_mcard(mcard, force)
