"""
Graph Extractor

Extracts entities and relationships from MCard content using LLM.
"""

import json
import logging
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Data Classes
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class Entity:
    """Represents an entity extracted from text."""
    name: str
    type: str  # CONCEPT, TECHNOLOGY, PERSON, ORGANIZATION, etc.
    description: str = ""
    id: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'type': self.type,
            'description': self.description,
        }


@dataclass
class Relationship:
    """Represents a relationship between two entities."""
    source: str  # Entity name
    target: str  # Entity name
    relationship: str  # Verb/action connecting them
    description: str = ""
    weight: float = 1.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'source': self.source,
            'target': self.target,
            'relationship': self.relationship,
            'description': self.description,
        }


@dataclass
class ExtractionResult:
    """Result from entity/relationship extraction."""
    entities: List[Entity] = field(default_factory=list)
    relationships: List[Relationship] = field(default_factory=list)
    success: bool = True
    error: Optional[str] = None


# ─────────────────────────────────────────────────────────────────────────────
# Extraction Prompts
# ─────────────────────────────────────────────────────────────────────────────

EXTRACTION_SYSTEM_PROMPT = """You are an expert at extracting structured information from text.
Given a text, identify:
1. ENTITIES: Named concepts, technologies, people, organizations, or things
2. RELATIONSHIPS: How entities relate to each other

Respond ONLY with valid JSON in this format:
{
  "entities": [
    {"name": "EntityName", "type": "CONCEPT|TECHNOLOGY|PERSON|ORGANIZATION|OTHER", "description": "Brief description"}
  ],
  "relationships": [
    {"source": "Entity1", "target": "Entity2", "relationship": "verb phrase", "description": "Optional context"}
  ]
}

Entity types:
- CONCEPT: Abstract ideas, methodologies, patterns (e.g., "content-addressable storage")
- TECHNOLOGY: Systems, libraries, frameworks (e.g., "SQLite", "Python")  
- PERSON: People names
- ORGANIZATION: Companies, groups
- OTHER: Anything else

Keep entity names concise but unique. Use present tense for relationships."""


EXTRACTION_USER_PROMPT = """Extract entities and relationships from this text:

---
{content}
---

Remember: Return ONLY valid JSON."""


# ─────────────────────────────────────────────────────────────────────────────
# Graph Extractor
# ─────────────────────────────────────────────────────────────────────────────

class GraphExtractor:
    """
    Extracts entities and relationships from text using LLM.
    
    Usage:
        extractor = GraphExtractor(model='gemma3:latest')
        result = extractor.extract("MCard is a Python library...")
        
        for entity in result.entities:
            print(f"{entity.name} ({entity.type})")
            
        for rel in result.relationships:
            print(f"{rel.source} --{rel.relationship}-> {rel.target}")
    """
    
    def __init__(
        self,
        model: str = 'gemma3:latest',
        temperature: float = 0.1,
        max_retries: int = 2
    ):
        """
        Initialize graph extractor.
        
        Args:
            model: LLM model to use
            temperature: Low for consistent extraction
            max_retries: Retries on parse failure
        """
        self.model = model
        self.temperature = temperature
        self.max_retries = max_retries
    
    def extract(self, content: str) -> ExtractionResult:
        """
        Extract entities and relationships from content.
        
        Args:
            content: Text to extract from
            
        Returns:
            ExtractionResult with entities and relationships
        """
        if not content or not content.strip():
            return ExtractionResult(success=False, error="Empty content")
        
        # Truncate if too long
        max_chars = 6000
        if len(content) > max_chars:
            content = content[:max_chars] + "\n[...truncated...]"
        
        # Call LLM for extraction
        for attempt in range(self.max_retries + 1):
            try:
                result = self._call_llm(content)
                parsed = self._parse_response(result)
                if parsed.entities or parsed.relationships:
                    return parsed
            except Exception as e:
                logger.warning(f"Extraction attempt {attempt + 1} failed: {e}")
                if attempt == self.max_retries:
                    return ExtractionResult(success=False, error=str(e))
        
        return ExtractionResult(success=False, error="No entities extracted")
    
    def _call_llm(self, content: str) -> str:
        """Call LLM for extraction."""
        from mcard.ptr.core.llm import chat_monad
        
        prompt = EXTRACTION_USER_PROMPT.format(content=content)
        
        result = chat_monad(
            prompt=prompt,
            system_prompt=EXTRACTION_SYSTEM_PROMPT,
            model=self.model,
            temperature=self.temperature,
            max_tokens=2000
        ).unsafe_run()
        
        if result.is_left():
            raise RuntimeError(f"LLM call failed: {result.value}")
        
        return result.value.get('content', str(result.value))
    
    def _parse_response(self, response: str) -> ExtractionResult:
        """Parse LLM response into structured data."""
        # Try to extract JSON from response
        json_match = re.search(r'\{[\s\S]*\}', response)
        if not json_match:
            raise ValueError("No JSON found in response")
        
        json_str = json_match.group()
        
        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            # Try to fix common issues
            json_str = self._clean_json(json_str)
            data = json.loads(json_str)
        
        entities = []
        for e in data.get('entities', []):
            if isinstance(e, dict) and 'name' in e:
                entities.append(Entity(
                    name=e.get('name', '').strip(),
                    type=e.get('type', 'OTHER').upper(),
                    description=e.get('description', '').strip()
                ))
        
        relationships = []
        for r in data.get('relationships', []):
            if isinstance(r, dict) and 'source' in r and 'target' in r:
                relationships.append(Relationship(
                    source=r.get('source', '').strip(),
                    target=r.get('target', '').strip(),
                    relationship=r.get('relationship', 'relates_to').strip(),
                    description=r.get('description', '').strip()
                ))
        
        return ExtractionResult(
            entities=entities,
            relationships=relationships,
            success=True
        )
    
    def _clean_json(self, json_str: str) -> str:
        """Try to clean up malformed JSON."""
        # Remove trailing commas
        json_str = re.sub(r',\s*([}\]])', r'\1', json_str)
        # Remove control characters
        json_str = re.sub(r'[\x00-\x1f]', '', json_str)
        return json_str
    
    def extract_batch(
        self, 
        contents: List[str]
    ) -> List[ExtractionResult]:
        """
        Extract from multiple texts.
        
        Args:
            contents: List of texts
            
        Returns:
            List of ExtractionResults
        """
        return [self.extract(content) for content in contents]
