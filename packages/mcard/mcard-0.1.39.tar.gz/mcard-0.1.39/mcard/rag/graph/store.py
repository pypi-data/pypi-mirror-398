"""
Graph Store

SQLite-based knowledge graph storage with traversal capabilities.
"""

import json
import logging
import sqlite3
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set, Tuple

from .schema import GRAPH_SCHEMAS
from .extractor import Entity, Relationship, ExtractionResult

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Graph Store
# ─────────────────────────────────────────────────────────────────────────────

class GraphStore:
    """
    SQLite-based storage for knowledge graph.
    
    Features:
    - Entity and relationship storage
    - Graph traversal (BFS)
    - Multi-hop pathfinding
    - Community management
    
    Usage:
        store = GraphStore(db_path="graph.db")
        
        # Add entities
        entity_id = store.add_entity(entity, source_hash)
        
        # Add relationships
        store.add_relationship(source_id, target_id, "relates_to", source_hash)
        
        # Find related entities
        related = store.find_related("MCard", hops=2)
    """
    
    def __init__(self, db_path: str = ':memory:'):
        """
        Initialize graph store.
        
        Args:
            db_path: Path to SQLite database
        """
        self.db_path = db_path
        self.conn = self._init_database()
    
    def _init_database(self) -> sqlite3.Connection:
        """Initialize SQLite connection and create tables."""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        cursor = conn.cursor()
        
        # Create all graph tables
        for name, schema in GRAPH_SCHEMAS.items():
            cursor.execute(schema)
        
        conn.commit()
        logger.debug(f"Initialized graph store at {self.db_path}")
        return conn
    
    # ─────────────────────────────────────────────────────────────────────────
    # Entity Operations
    # ─────────────────────────────────────────────────────────────────────────
    
    def add_entity(
        self, 
        entity: Entity, 
        source_hash: str,
        embedding: bytes = None
    ) -> int:
        """
        Add an entity to the graph.
        
        Args:
            entity: Entity to add
            source_hash: Source MCard hash
            embedding: Optional entity embedding
            
        Returns:
            Entity ID
        """
        now = datetime.now(timezone.utc).isoformat()
        cursor = self.conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO graph_entities (name, type, description, source_hash, embedding, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                entity.name,
                entity.type,
                entity.description,
                source_hash,
                embedding,
                now
            ))
            self.conn.commit()
            return cursor.lastrowid
            
        except sqlite3.IntegrityError:
            # Entity already exists, get its ID
            cursor.execute("""
                SELECT id FROM graph_entities 
                WHERE name = ? AND type = ? AND source_hash = ?
            """, (entity.name, entity.type, source_hash))
            row = cursor.fetchone()
            return row[0] if row else -1
    
    def get_entity_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Get entity by name (case-insensitive)."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT id, name, type, description, source_hash, created_at
            FROM graph_entities
            WHERE LOWER(name) = LOWER(?)
            LIMIT 1
        """, (name,))
        
        row = cursor.fetchone()
        if row:
            return {
                'id': row[0],
                'name': row[1],
                'type': row[2],
                'description': row[3],
                'source_hash': row[4],
                'created_at': row[5]
            }
        return None
    
    def get_entity_by_id(self, entity_id: int) -> Optional[Dict[str, Any]]:
        """Get entity by ID."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT id, name, type, description, source_hash, created_at
            FROM graph_entities
            WHERE id = ?
        """, (entity_id,))
        
        row = cursor.fetchone()
        if row:
            return {
                'id': row[0],
                'name': row[1],
                'type': row[2],
                'description': row[3],
                'source_hash': row[4],
                'created_at': row[5]
            }
        return None
    
    def search_entities(
        self, 
        query: str, 
        type_filter: str = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Search entities by name pattern."""
        cursor = self.conn.cursor()
        
        if type_filter:
            cursor.execute("""
                SELECT id, name, type, description, source_hash
                FROM graph_entities
                WHERE name LIKE ? AND type = ?
                LIMIT ?
            """, (f"%{query}%", type_filter, limit))
        else:
            cursor.execute("""
                SELECT id, name, type, description, source_hash
                FROM graph_entities
                WHERE name LIKE ?
                LIMIT ?
            """, (f"%{query}%", limit))
        
        return [
            {'id': r[0], 'name': r[1], 'type': r[2], 'description': r[3], 'source_hash': r[4]}
            for r in cursor.fetchall()
        ]
    
    def get_entities_by_source(self, source_hash: str) -> List[Dict[str, Any]]:
        """Get all entities from a source MCard."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT id, name, type, description
            FROM graph_entities
            WHERE source_hash = ?
        """, (source_hash,))
        
        return [
            {'id': r[0], 'name': r[1], 'type': r[2], 'description': r[3]}
            for r in cursor.fetchall()
        ]
    
    # ─────────────────────────────────────────────────────────────────────────
    # Community Operations
    # ─────────────────────────────────────────────────────────────────────────
    
    def add_community(
        self,
        title: str,
        summary: str,
        member_ids: List[int],
        level: int = 0,
        parent_id: Optional[int] = None,
        embedding: bytes = None
    ) -> int:
        """Add a community summary."""
        now = datetime.now(timezone.utc).isoformat()
        cursor = self.conn.cursor()
        
        cursor.execute("""
            INSERT INTO graph_communities 
            (title, summary, member_entity_ids, level, parent_community_id, embedding, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            title,
            summary,
            json.dumps(member_ids),
            level,
            parent_id,
            embedding,
            now
        ))
        
        self.conn.commit()
        return cursor.lastrowid

    def get_communities(self, level: int = 0) -> List[Dict[str, Any]]:
        """Get communities by level."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT id, title, summary, member_entity_ids, level
            FROM graph_communities
            WHERE level = ?
        """, (level,))
        
        results = []
        for row in cursor.fetchall():
            results.append({
                'id': row[0],
                'title': row[1],
                'summary': row[2],
                'member_ids': json.loads(row[3]) if row[3] else [],
                'level': row[4]
            })
        return results

    # ─────────────────────────────────────────────────────────────────────────
    # Relationship Operations
    # ─────────────────────────────────────────────────────────────────────────
    
    def add_relationship(
        self,
        source_entity_id: int,
        target_entity_id: int,
        relationship: str,
        source_hash: str,
        description: str = "",
        weight: float = 1.0
    ) -> int:
        """
        Add a relationship between entities.
        
        Args:
            source_entity_id: Source entity ID
            target_entity_id: Target entity ID
            relationship: Relationship type/verb
            source_hash: Source MCard hash
            description: Optional description
            weight: Relationship weight
            
        Returns:
            Relationship ID
        """
        now = datetime.now(timezone.utc).isoformat()
        cursor = self.conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO graph_relationships 
                (source_entity_id, target_entity_id, relationship, description, weight, source_hash, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                source_entity_id,
                target_entity_id,
                relationship,
                description,
                weight,
                source_hash,
                now
            ))
            self.conn.commit()
            return cursor.lastrowid
            
        except sqlite3.IntegrityError:
            # Relationship already exists
            return -1
    
    def get_relationships_from(self, entity_id: int) -> List[Dict[str, Any]]:
        """Get outgoing relationships from an entity."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT r.id, r.relationship, r.description, r.weight,
                   e.id, e.name, e.type
            FROM graph_relationships r
            JOIN graph_entities e ON r.target_entity_id = e.id
            WHERE r.source_entity_id = ?
        """, (entity_id,))
        
        return [
            {
                'rel_id': r[0],
                'relationship': r[1],
                'description': r[2],
                'weight': r[3],
                'target_id': r[4],
                'target_name': r[5],
                'target_type': r[6]
            }
            for r in cursor.fetchall()
        ]
    
    def get_relationships_to(self, entity_id: int) -> List[Dict[str, Any]]:
        """Get incoming relationships to an entity."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT r.id, r.relationship, r.description, r.weight,
                   e.id, e.name, e.type
            FROM graph_relationships r
            JOIN graph_entities e ON r.source_entity_id = e.id
            WHERE r.target_entity_id = ?
        """, (entity_id,))
        
        return [
            {
                'rel_id': r[0],
                'relationship': r[1],
                'description': r[2],
                'weight': r[3],
                'source_id': r[4],
                'source_name': r[5],
                'source_type': r[6]
            }
            for r in cursor.fetchall()
        ]
    
    # ─────────────────────────────────────────────────────────────────────────
    # Graph Traversal
    # ─────────────────────────────────────────────────────────────────────────
    
    def find_related(
        self, 
        entity_name: str, 
        hops: int = 2,
        direction: str = 'both'
    ) -> List[Dict[str, Any]]:
        """
        Find entities within N hops of a given entity.
        
        Args:
            entity_name: Starting entity name
            hops: Maximum traversal depth
            direction: 'outgoing', 'incoming', or 'both'
            
        Returns:
            List of related entities with their paths
        """
        # Find starting entity
        start = self.get_entity_by_name(entity_name)
        if not start:
            return []
        
        visited: Set[int] = {start['id']}
        results = []
        frontier = [(start['id'], 0, [start['name']])]  # (id, depth, path)
        
        while frontier:
            current_id, depth, path = frontier.pop(0)
            
            if depth >= hops:
                continue
            
            # Get adjacent entities
            neighbors = []
            
            if direction in ('outgoing', 'both'):
                for rel in self.get_relationships_from(current_id):
                    neighbors.append((
                        rel['target_id'],
                        rel['target_name'],
                        rel['relationship'],
                        'outgoing'
                    ))
            
            if direction in ('incoming', 'both'):
                for rel in self.get_relationships_to(current_id):
                    neighbors.append((
                        rel['source_id'],
                        rel['source_name'],
                        rel['relationship'],
                        'incoming'
                    ))
            
            for neighbor_id, neighbor_name, rel, dir in neighbors:
                if neighbor_id not in visited:
                    visited.add(neighbor_id)
                    new_path = path + [f"--{rel}->", neighbor_name]
                    
                    entity = self.get_entity_by_id(neighbor_id)
                    if entity:
                        results.append({
                            'entity': entity,
                            'depth': depth + 1,
                            'path': new_path,
                            'relationship': rel
                        })
                    
                    frontier.append((neighbor_id, depth + 1, new_path))
        
        return results
    
    def find_path(
        self, 
        source_name: str, 
        target_name: str,
        max_depth: int = 4
    ) -> Optional[List[str]]:
        """
        Find shortest path between two entities.
        
        Args:
            source_name: Starting entity name
            target_name: Target entity name
            max_depth: Maximum path length
            
        Returns:
            List of entity names in path, or None if no path
        """
        source = self.get_entity_by_name(source_name)
        target = self.get_entity_by_name(target_name)
        
        if not source or not target:
            return None
        
        if source['id'] == target['id']:
            return [source_name]
        
        # BFS for shortest path
        visited = {source['id']}
        queue = [(source['id'], [source['name']])]
        
        while queue:
            current_id, path = queue.pop(0)
            
            if len(path) > max_depth:
                continue
            
            for rel in self.get_relationships_from(current_id):
                neighbor_id = rel['target_id']
                
                if neighbor_id == target['id']:
                    return path + [f"--{rel['relationship']}->", target_name]
                
                if neighbor_id not in visited:
                    visited.add(neighbor_id)
                    queue.append((
                        neighbor_id, 
                        path + [f"--{rel['relationship']}->", rel['target_name']]
                    ))
        
        return None
    
    # ─────────────────────────────────────────────────────────────────────────
    # Extraction Tracking
    # ─────────────────────────────────────────────────────────────────────────
    
    def mark_extracted(self, source_hash: str, entity_count: int, rel_count: int):
        """Mark a source as having been extracted."""
        now = datetime.now(timezone.utc).isoformat()
        cursor = self.conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO graph_extractions 
            (hash, entity_count, relationship_count, extracted_at)
            VALUES (?, ?, ?, ?)
        """, (source_hash, entity_count, rel_count, now))
        
        self.conn.commit()
    
    def is_extracted(self, source_hash: str) -> bool:
        """Check if a source has been extracted."""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT 1 FROM graph_extractions WHERE hash = ?",
            (source_hash,)
        )
        return cursor.fetchone() is not None
    
    # ─────────────────────────────────────────────────────────────────────────
    # Statistics
    # ─────────────────────────────────────────────────────────────────────────
    
    def count_entities(self) -> int:
        """Get total entity count."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM graph_entities")
        return cursor.fetchone()[0]
    
    def count_relationships(self) -> int:
        """Get total relationship count."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM graph_relationships")
        return cursor.fetchone()[0]
    
    def count_extractions(self) -> int:
        """Get count of extracted sources."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM graph_extractions")
        return cursor.fetchone()[0]
    
    def get_entity_types(self) -> Dict[str, int]:
        """Get counts by entity type."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT type, COUNT(*) FROM graph_entities
            GROUP BY type
            ORDER BY COUNT(*) DESC
        """)
        return {row[0]: row[1] for row in cursor.fetchall()}
    
    def get_stats(self) -> Dict[str, Any]:
        """Get graph statistics."""
        return {
            'entity_count': self.count_entities(),
            'relationship_count': self.count_relationships(),
            'extraction_count': self.count_extractions(),
            'entity_types': self.get_entity_types(),
        }
    
    def clear(self):
        """Clear all graph data."""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM graph_relationships")
        cursor.execute("DELETE FROM graph_entities")
        cursor.execute("DELETE FROM graph_communities")
        cursor.execute("DELETE FROM graph_extractions")
        self.conn.commit()
        logger.info("Graph store cleared")


# ─────────────────────────────────────────────────────────────────────────────
# Batch Operations
# ─────────────────────────────────────────────────────────────────────────────

def store_extraction_result(
    store: GraphStore,
    result: ExtractionResult,
    source_hash: str
) -> Tuple[int, int]:
    """
    Store an extraction result in the graph.
    
    Args:
        store: GraphStore instance
        result: ExtractionResult from GraphExtractor
        source_hash: Source MCard hash
        
    Returns:
        Tuple of (entity_count, relationship_count) stored
    """
    if not result.success:
        return 0, 0
    
    entity_map = {}  # name -> id
    
    # Add entities
    for entity in result.entities:
        entity_id = store.add_entity(entity, source_hash)
        if entity_id > 0:
            entity_map[entity.name.lower()] = entity_id
    
    # Add relationships
    rel_count = 0
    for rel in result.relationships:
        source_id = entity_map.get(rel.source.lower())
        target_id = entity_map.get(rel.target.lower())
        
        if source_id and target_id:
            rel_id = store.add_relationship(
                source_id, target_id,
                rel.relationship,
                source_hash,
                rel.description
            )
            if rel_id > 0:
                rel_count += 1
    
    # Mark as extracted
    store.mark_extracted(source_hash, len(entity_map), rel_count)
    
    return len(entity_map), rel_count
