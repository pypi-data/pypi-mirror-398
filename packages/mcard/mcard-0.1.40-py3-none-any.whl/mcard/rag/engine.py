"""
MCard RAG Engine

Main interface for Retrieval-Augmented Generation over MCard collections.
"""

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from mcard import MCard
from mcard.model.card_collection import CardCollection

from .config import RAGConfig, DEFAULT_RAG_CONFIG
from .embeddings import OllamaEmbeddingProvider
from .vector import MCardVectorStore, VectorSearchResult

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# RAG Response
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class RAGResponse:
    """Response from a RAG query."""
    answer: str
    sources: List[str]  # Source MCard hashes
    source_chunks: List[str]  # Relevant text chunks
    confidence: float
    metadata: Optional[Dict[str, Any]] = None


# ─────────────────────────────────────────────────────────────────────────────
# RAG Engine
# ─────────────────────────────────────────────────────────────────────────────

class MCardRAGEngine:
    """
    Retrieval-Augmented Generation engine for MCard collections.
    
    Combines semantic vector search with LLM generation to provide
    context-aware answers grounded in MCard content.
    
    Usage:
        from mcard import default_collection
        from mcard.rag import MCardRAGEngine
        
        # Initialize
        rag = MCardRAGEngine(default_collection)
        
        # Index content
        rag.index_all()
        
        # Query
        response = rag.query("What is the Cubical Logic Model?")
        print(response.answer)
        print(f"Sources: {response.sources}")
    """
    
    def __init__(
        self,
        collection: CardCollection = None,
        config: RAGConfig = None,
        vector_db_path: str = None
    ):
        """
        Initialize RAG engine.
        
        Args:
            collection: MCard collection for storage (uses default if None)
            config: RAG configuration
            vector_db_path: Path to vector database (None = in-memory)
        """
        from mcard import default_collection as _default_collection
        
        self.collection = collection or _default_collection
        self.config = config or DEFAULT_RAG_CONFIG
        
        # Initialize embedding provider
        self.embedder = OllamaEmbeddingProvider(
            model=self.config.embedding_model,
            base_url=self.config.ollama_base_url
        )
        
        # Initialize vector store
        self.vector_store = MCardVectorStore(
            db_path=vector_db_path or self.config.vector_db_path,
            config=self.config,
            embedding_provider=self.embedder
        )
        
        # LLM for generation (lazy loaded)
        self._llm = None
        
        logger.info(f"Initialized RAG engine with model {self.config.embedding_model}")
    
    @property
    def llm(self):
        """Lazy-load LLM runtime."""
        if self._llm is None:
            from mcard.ptr.core.llm import LLMRuntime
            self._llm = LLMRuntime()
        return self._llm
    
    def index(self, mcard: MCard) -> bool:
        """
        Index a single MCard for semantic search.
        
        Args:
            mcard: MCard to index
            
        Returns:
            True if indexed successfully
        """
        try:
            count = self.vector_store.index(mcard)
            return count > 0
        except Exception as e:
            logger.error(f"Failed to index MCard {mcard.hash[:8]}: {e}")
            return False
    
    def index_all(self, force: bool = False) -> Dict[str, int]:
        """
        Index all MCards in the collection.
        
        Args:
            force: Re-index even if already indexed
            
        Returns:
            Dictionary with 'indexed', 'skipped', 'failed' counts
        """
        stats = {'indexed': 0, 'skipped': 0, 'failed': 0}
        
        # Get all cards from collection
        page = self.collection.get_all_cards()
        
        for mcard in page.items:
            if not force and self.vector_store.is_indexed(mcard.hash):
                stats['skipped'] += 1
                continue
            
            if self.index(mcard):
                stats['indexed'] += 1
            else:
                stats['failed'] += 1
        
        logger.info(f"Indexing complete: {stats}")
        return stats
    
    def search(
        self,
        query: str,
        k: int = None,
        hybrid: bool = True
    ) -> List[VectorSearchResult]:
        """
        Search for relevant MCards.
        
        Args:
            query: Search query
            k: Number of results
            hybrid: Use hybrid (vector + FTS) search
            
        Returns:
            List of search results with scores
        """
        k = k or self.config.top_k
        
        if hybrid and self.config.enable_hybrid_search:
            return self.vector_store.hybrid_search(query, k)
        else:
            return self.vector_store.search(query, k)
    
    def query(
        self,
        question: str,
        k: int = None,
        system_prompt: str = None,
        model: str = None
    ) -> RAGResponse:
        """
        Query with RAG: search for context and generate answer.
        
        Args:
            question: User question
            k: Number of context chunks
            system_prompt: Custom system prompt
            model: LLM model to use
            
        Returns:
            RAGResponse with answer and sources
        """
        k = k or self.config.top_k
        
        # Search for relevant context
        results = self.search(question, k)
        
        if not results:
            return RAGResponse(
                answer="I couldn't find relevant information in the knowledge base.",
                sources=[],
                source_chunks=[],
                confidence=0.0
            )
        
        # Assemble context
        context_parts = []
        for i, result in enumerate(results):
            chunk = result.chunk_text or f"[Content from {result.hash[:8]}]"
            context_parts.append(f"[{i+1}] {chunk}")
        
        context = "\n\n".join(context_parts)
        
        # Generate answer
        default_system = """You are a helpful assistant that answers questions based on the provided context.
Use the context to provide accurate, relevant answers.
If the context doesn't contain enough information to fully answer the question, say so.
Always cite the source numbers [1], [2], etc. when using information from the context."""
        
        prompt = f"""Context:
{context}

Question: {question}

Please provide a comprehensive answer based on the context above."""
        
        try:
            from mcard.ptr.core.llm import chat_monad
            
            response = chat_monad(
                prompt=prompt,
                system_prompt=system_prompt or default_system,
                model=model or 'gemma3:latest',
                temperature=0.3,
                max_tokens=1000
            ).unsafe_run()
            
            if response.is_right():
                answer = response.value.get('content', str(response.value))
            else:
                answer = f"Error generating response: {response.value}"
                
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            answer = f"Error: {e}"
        
        # Calculate confidence based on top scores
        avg_score = sum(r.score for r in results) / len(results) if results else 0
        
        return RAGResponse(
            answer=answer,
            sources=[r.hash for r in results],
            source_chunks=[r.chunk_text or "" for r in results],
            confidence=avg_score,
            metadata={
                'model': model or 'gemma3:latest',
                'num_sources': len(results),
                'scores': [r.score for r in results]
            }
        )
    
    def get_info(self) -> Dict[str, Any]:
        """Get RAG engine information."""
        return {
            'config': {
                'embedding_model': self.config.embedding_model,
                'top_k': self.config.top_k,
                'chunk_size': self.config.chunk_size,
                'hybrid_search': self.config.enable_hybrid_search,
            },
            'vector_store': self.vector_store.get_info(),
            'embedder_available': self.embedder.validate_connection(),
        }
