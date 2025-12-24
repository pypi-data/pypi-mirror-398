"""
Community Detection and Summarization

Label Propagation Algorithm (LPA) for community detection
and LLM-based hierarchical summarization.
"""

import json
import logging
import random
import re
from collections import Counter, defaultdict
from typing import Any, Dict, List, Optional, Set, Tuple

from .store import GraphStore

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Community Detection
# ─────────────────────────────────────────────────────────────────────────────

def detect_communities(store: GraphStore, max_iter: int = 20) -> List[List[int]]:
    """
    Detect communities using asynchronous Label Propagation.
    
    Args:
        store: GraphStore instance
        max_iter: Maximum iterations
        
    Returns:
        List of communities, where each community is a list of entity IDs
    """
    logger.info("Starting community detection (LPA)...")
    
    # 1. Build Adjacency List
    adj = defaultdict(list)
    nodes = set()
    
    cursor = store.conn.cursor()
    cursor.execute("SELECT source_entity_id, target_entity_id FROM graph_relationships")
    
    rows = cursor.fetchall()
    for src, tgt in rows:
        adj[src].append(tgt)
        adj[tgt].append(src)  # Undirected for community detection
        nodes.add(src)
        nodes.add(tgt)
        
    node_list = list(nodes)
    if not node_list:
        logger.warning("No nodes found for community detection")
        return []
    
    logger.debug(f"Graph size: {len(nodes)} nodes, {len(rows)} edges")

    # 2. Initialize Labels
    labels = {node: node for node in nodes}
    
    # 3. Propagate Labels
    for i in range(max_iter):
        changes = 0
        random.shuffle(node_list)
        
        for node in node_list:
            if not adj[node]:
                continue
                
            neighbor_labels = [labels[neighbor] for neighbor in adj[node]]
            if not neighbor_labels:
                continue
                
            # Find most frequent label (ties broken randomly)
            counts = Counter(neighbor_labels)
            max_freq = counts.most_common(1)[0][1]
            best_labels = [lbl for lbl, count in counts.items() if count == max_freq]
            new_label = random.choice(best_labels)
            
            if labels[node] != new_label:
                labels[node] = new_label
                changes += 1
        
        logger.debug(f"LPA Iteration {i+1}: {changes} changes")
        if changes == 0:
            logger.info(f"LPA converged after {i+1} iterations")
            break
            
    # 4. Group Communities
    communities = defaultdict(list)
    for node, label in labels.items():
        communities[label].append(node)
        
    result = list(communities.values())
    logger.info(f"Detected {len(result)} communities")
    
    # Sort for deterministic output (by size desc, then first ID)
    result.sort(key=lambda c: (-len(c), min(c)))
    
    return result


# ─────────────────────────────────────────────────────────────────────────────
# Community Summarization
# ─────────────────────────────────────────────────────────────────────────────

SUMMARIZE_SYSTEM_PROMPT = """You are an expert graph analyst.
Your task is to summarize a "community" of related entities from a knowledge graph.
Focus on the common themes, purposes, or technologies that connect these entities.
Synthesize the descriptions into a cohesive whole."""

SUMMARIZE_USER_PROMPT = """Analyze the following list of entities and their descriptions which form a community in a knowledge graph.
Create a Title and valid JSON Summary.

--- BEGIN ENTITY LIST ---
{entity_text}
--- END ENTITY LIST ---

Requirement:
- Provide a short Title.
- Provide a detailed Summary of common themes.
- Output MUST be valid JSON in the format:
{{
  "title": "Community Title",
  "summary": "Detailed summary..."
}}
"""

class CommunitySummarizer:
    """Summarizes graph communities using LLM."""
    
    def __init__(self, store: GraphStore, model: str = 'gemma3:latest'):
        self.store = store
        self.model = model
    
    def summarize_and_store(self, communities: List[List[int]]) -> int:
        """
        Summarize communities and store them in the DB.
        
        Returns:
            Count of summaries generated
        """
        count = 0
        
        for comm_ids in communities:
            # Prepare context
            entity_text = self._prepare_context(comm_ids)
            if not entity_text:
                continue
                
            try:
                title, summary = self._generate_summary(entity_text)
                self.store.add_community(title, summary, comm_ids)
                count += 1
                logger.info(f"Generated community: {title}")
            except Exception as e:
                logger.error(f"Failed to summarize community: {e}")
                
        return count
        
    def _prepare_context(self, ids: List[int]) -> str:
        lines = []
        for eid in ids[:30]:  # Limit context size
            ent = self.store.get_entity_by_id(eid)
            if ent:
                lines.append(f"- {ent['name']} ({ent['type']}): {ent['description']}")
        return "\n".join(lines)
    
    def _generate_summary(self, entity_text: str) -> Tuple[str, str]:
        from mcard.ptr.core.llm import chat_monad
        
        prompt = SUMMARIZE_USER_PROMPT.format(entity_text=entity_text)
        
        result = chat_monad(
            prompt=prompt,
            system_prompt=SUMMARIZE_SYSTEM_PROMPT,
            model=self.model,
            temperature=0.3,
            max_tokens=1000
        ).unsafe_run()
        
        if result.is_left():
            raise RuntimeError(f"LLM failure: {result.value}")
            
        content = result.value.get('content', str(result.value))
        
        # Parse JSON
        json_match = re.search(r'\{[\s\S]*\}', content)
        if json_match:
            try:
                data = json.loads(json_match.group())
                return data.get('title', 'Unknown Community'), data.get('summary', '')
            except json.JSONDecodeError:
                pass
                
        # Fallback if no JSON
        return "Community Summary", content[:500]
