"""
GraphRAG Engine

Combines vector search with knowledge graph for enhanced RAG.
"""

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple

from mcard import MCard

from ..config import RAGConfig, DEFAULT_RAG_CONFIG
from ..vector import MCardVectorStore, VectorSearchResult
from ..embeddings import OllamaEmbeddingProvider
from .extractor import GraphExtractor, ExtractionResult
from .store import GraphStore, store_extraction_result

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# GraphRAG Response
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class GraphRAGResponse:
    """Response from GraphRAG query."""
    answer: str
    sources: List[str]  # Source MCard hashes
    entities: List[Dict[str, Any]]  # Relevant entities
    relationships: List[Dict[str, Any]]  # Relevant relationships
    graph_context: str  # Graph traversal context
    vector_context: str  # Vector search context
    confidence: float
    metadata: Optional[Dict[str, Any]] = None


# ─────────────────────────────────────────────────────────────────────────────
# System Prompts
# ─────────────────────────────────────────────────────────────────────────────

GRAPHRAG_SYSTEM_PROMPT = """You are a helpful assistant that answers questions using both document context and a knowledge graph.

You have access to:
1. DOCUMENT CONTEXT: Relevant text passages from the knowledge base
2. GRAPH CONTEXT: Entities and their relationships from the knowledge graph

Use both sources to provide comprehensive, accurate answers.
- Cite sources [1], [2], etc. for document context
- Reference entities by name when using graph information
- If the graph shows relationships that help answer the question, describe them

Be thorough but concise. Acknowledge if information is incomplete."""


GRAPH_QUERY_PROMPT = """Question: {question}

=== DOCUMENT CONTEXT ===
{vector_context}

=== KNOWLEDGE GRAPH ===
Entities: {entities}
Relationships: {relationships}

Please provide a comprehensive answer using both the document context and knowledge graph information."""


# ─────────────────────────────────────────────────────────────────────────────
# GraphRAG Engine
# ─────────────────────────────────────────────────────────────────────────────

class GraphRAGEngine:
    """
    GraphRAG Engine combining vector search with knowledge graphs.
    
    Features:
    - Entity extraction from MCard content
    - Knowledge graph storage and traversal
    - Multi-hop reasoning across entities
    - Combined vector + graph context for LLM
    
    Usage:
        from mcard.rag.graph import GraphRAGEngine
        
        engine = GraphRAGEngine(vector_db_path=':memory:')
        
        # Index with graph extraction
        engine.index(mcard)
        
        # Query with graph context
        response = engine.query("How does MCard relate to PTR?")
    """
    
    def __init__(
        self,
        config: RAGConfig = None,
        vector_db_path: str = None,
        graph_db_path: str = None,
        llm_model: str = 'gemma3:latest'
    ):
        """
        Initialize GraphRAG engine.
        
        Args:
            config: RAG configuration
            vector_db_path: Path to vector database
            graph_db_path: Path to graph database (default: same as vector)
            llm_model: LLM model for generation
        """
        self.config = config or DEFAULT_RAG_CONFIG
        self.llm_model = llm_model
        
        # Initialize embedding provider
        self.embedder = OllamaEmbeddingProvider(
            model=self.config.embedding_model,
            base_url=self.config.ollama_base_url
        )
        
        # Initialize vector store
        self.vector_store = MCardVectorStore(
            db_path=vector_db_path,
            config=self.config,
            embedding_provider=self.embedder
        )
        
        # Initialize graph store (same DB or separate)
        graph_path = graph_db_path or vector_db_path or ':memory:'
        self.graph_store = GraphStore(db_path=graph_path)
        
        # Initialize extractor
        self.extractor = GraphExtractor(model=llm_model)
        
        logger.info(f"Initialized GraphRAG engine")
    
    def index(
        self, 
        mcard: MCard, 
        extract_graph: bool = True,
        force: bool = False
    ) -> Dict[str, int]:
        """
        Index an MCard with optional graph extraction.
        
        Args:
            mcard: MCard to index
            extract_graph: Extract entities and relationships
            force: Re-index even if exists
            
        Returns:
            Dict with indexing stats
        """
        stats = {'vectors': 0, 'entities': 0, 'relationships': 0}
        
        # Get content
        content = mcard.get_content()
        if isinstance(content, bytes):
            try:
                content = content.decode('utf-8')
            except UnicodeDecodeError:
                logger.warning(f"Cannot decode MCard {mcard.hash[:8]}")
                return stats
        
        # Vector indexing
        if force or not self.vector_store.is_indexed(mcard.hash):
            stats['vectors'] = self.vector_store.index(mcard)
        
        # Graph extraction
        if extract_graph and (force or not self.graph_store.is_extracted(mcard.hash)):
            logger.debug(f"Extracting graph from {mcard.hash[:8]}...")
            
            result = self.extractor.extract(content)
            
            if result.success:
                entity_count, rel_count = store_extraction_result(
                    self.graph_store, result, mcard.hash
                )
                stats['entities'] = entity_count
                stats['relationships'] = rel_count
                logger.debug(f"Extracted {entity_count} entities, {rel_count} relationships")
            else:
                logger.warning(f"Graph extraction failed: {result.error}")
        
        return stats
    
    def detect_and_summarize_communities(self) -> int:
        """
        Detect communities and generate summaries.
        
        Returns:
            Number of communities summarized
        """
        from .community import detect_communities, CommunitySummarizer
        
        logger.info("Detecting communities...")
        communities = detect_communities(self.graph_store)
        
        if not communities:
            logger.info("No communities detected.")
            return 0
            
        logger.info(f"Summarizing {len(communities)} communities...")
        summarizer = CommunitySummarizer(self.graph_store, model=self.llm_model)
        count = summarizer.summarize_and_store(communities)
        
        logger.info(f"Generated {count} community summaries.")
        return count
    
    def _get_vector_context(self, query: str, k: int) -> Tuple[str, List[str]]:
        """Get vector search context."""
        results = self.vector_store.hybrid_search(query, k)
        
        context_parts = []
        sources = []
        
        for i, result in enumerate(results):
            chunk = result.chunk_text or f"[Content from {result.hash[:8]}]"
            context_parts.append(f"[{i+1}] {chunk}")
            sources.append(result.hash)
        
        return "\n\n".join(context_parts), sources
    
    def _get_graph_context(
        self, 
        query: str,
        source_hashes: List[str] = None
    ) -> Tuple[List[Dict], List[Dict]]:
        """
        Get relevant graph context.
        
        Searches for entities mentioned in the query and finds related entities.
        """
        entities = []
        relationships = []
        seen_entity_ids: Set[int] = set()
        
        # Search for entities matching query terms
        for word in query.split():
            if len(word) > 3:
                found = self.graph_store.search_entities(word, limit=5)
                for entity in found:
                    if entity['id'] not in seen_entity_ids:
                        seen_entity_ids.add(entity['id'])
                        entities.append(entity)
                        
                        # Get relationships
                        rels_out = self.graph_store.get_relationships_from(entity['id'])
                        rels_in = self.graph_store.get_relationships_to(entity['id'])
                        
                        for rel in rels_out:
                            relationships.append({
                                'source': entity['name'],
                                'relationship': rel['relationship'],
                                'target': rel['target_name']
                            })
                        
                        for rel in rels_in:
                            relationships.append({
                                'source': rel['source_name'],
                                'relationship': rel['relationship'],
                                'target': entity['name']
                            })
        
        # Also get entities from source documents
        if source_hashes:
            for hash_val in source_hashes[:3]:  # Limit
                source_entities = self.graph_store.get_entities_by_source(hash_val)
                for entity in source_entities:
                    if entity['id'] not in seen_entity_ids:
                        seen_entity_ids.add(entity['id'])
                        entities.append(entity)
        
        return entities, relationships
    
    def query(
        self,
        question: str,
        k: int = 5,
        use_graph: bool = True
    ) -> GraphRAGResponse:
        """
        Query with GraphRAG: vector search + graph context.
        
        Args:
            question: User question
            k: Number of vector results
            use_graph: Include graph context
            
        Returns:
            GraphRAGResponse with answer and sources
        """
        # Get vector context
        vector_context, sources = self._get_vector_context(question, k)
        
        # Get graph context
        entities = []
        relationships = []
        graph_context = ""
        
        if use_graph:
            entities, relationships = self._get_graph_context(question, sources)
            
            if entities:
                entity_strs = [f"{e['name']} ({e['type']})" for e in entities[:10]]
                rel_strs = [f"{r['source']} --{r['relationship']}-> {r['target']}" 
                           for r in relationships[:15]]
                
                graph_context = f"Entities: {', '.join(entity_strs)}\n"
                graph_context += f"Relationships:\n" + "\n".join(rel_strs)
        
        # Generate answer
        if not vector_context and not entities:
            return GraphRAGResponse(
                answer="I couldn't find relevant information.",
                sources=[],
                entities=[],
                relationships=[],
                graph_context="",
                vector_context="",
                confidence=0.0
            )
        
        # Build prompt
        entity_str = ", ".join(f"{e['name']} ({e['type']})" for e in entities) if entities else "None found"
        rel_str = "\n".join(
            f"  - {r['source']} --{r['relationship']}-> {r['target']}"
            for r in relationships
        ) if relationships else "None found"
        
        prompt = GRAPH_QUERY_PROMPT.format(
            question=question,
            vector_context=vector_context or "No document context available.",
            entities=entity_str,
            relationships=rel_str
        )
        
        # Call LLM
        try:
            from mcard.ptr.core.llm import chat_monad
            
            response = chat_monad(
                prompt=prompt,
                system_prompt=GRAPHRAG_SYSTEM_PROMPT,
                model=self.llm_model,
                temperature=0.3,
                max_tokens=1500
            ).unsafe_run()
            
            if response.is_right():
                answer = response.value.get('content', str(response.value))
            else:
                answer = f"Error generating response: {response.value}"
                
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            answer = f"Error: {e}"
        
        # Calculate confidence
        vec_results = self.vector_store.search(question, k)
        avg_score = sum(r.score for r in vec_results) / len(vec_results) if vec_results else 0
        graph_boost = 0.1 if entities else 0
        
        return GraphRAGResponse(
            answer=answer,
            sources=sources,
            entities=entities,
            relationships=relationships,
            graph_context=graph_context,
            vector_context=vector_context,
            confidence=min(avg_score + graph_boost, 1.0),
            metadata={
                'model': self.llm_model,
                'entity_count': len(entities),
                'relationship_count': len(relationships),
            }
        )
    
    def explore_entity(self, entity_name: str, hops: int = 2) -> Dict[str, Any]:
        """
        Explore an entity and its neighborhood.
        
        Args:
            entity_name: Entity to explore
            hops: Traversal depth
            
        Returns:
            Dict with entity info and related entities
        """
        # Try exact match first
        entity = self.graph_store.get_entity_by_name(entity_name)
        
        # If not found, try fuzzy search
        if not entity:
            candidates = self.graph_store.search_entities(entity_name, limit=1)
            if candidates:
                entity = candidates[0]
                # Update outgoing/incoming/related to use the found entity name/id
        
        if not entity:
            return {'error': f"Entity '{entity_name}' not found"}
        
        related = self.graph_store.find_related(entity['name'], hops=hops)
        
        return {
            'entity': entity,
            'related': related,
            'outgoing': self.graph_store.get_relationships_from(entity['id']),
            'incoming': self.graph_store.get_relationships_to(entity['id']),
        }
    
    def find_connection(self, source: str, target: str) -> Optional[List[str]]:
        """Find path between two entities."""
        return self.graph_store.find_path(source, target)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get engine statistics."""
        return {
            'vector_count': self.vector_store.count(),
            'unique_mcards': self.vector_store.count_unique(),
            'graph': self.graph_store.get_stats(),
            'llm_model': self.llm_model,
            'embedding_model': self.config.embedding_model,
        }
