"""
PCard Identity - Evolutionary Identity Management for Cubical Logic Models

This module defines the PCard class, which represents the persistent, upgradable identity
of a Cubical Logic Model (CLM). It manages the trajectory of evolution by pointing to
immutable PCardSnapshots (versions).
"""

import logging
import time
import uuid
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

import yaml
from mcard import MCard


@dataclass
class PCardState:
    """State of a PCard Identity at a specific point in time."""
    version: int
    head: str  # Hash of the current PCardSnapshot MCard
    previous: Optional[str] = None  # Hash of the previous PCardState (provenance)
    timestamp: float = field(default_factory=time.time)


@dataclass
class PCardContract:
    """Contract rules governing the PCard's evolution."""
    upgradability: str = "uups"  # e.g., "uups", "immutable", "dao-vote"
    rules: List[str] = field(default_factory=list)


@dataclass
class PCardMetadata:
    """Metadata for the PCard Identity."""
    id: str  # Unique persistent identifier (UUID or Genesis Hash)
    owner: str  # Public key or DID of the owner
    created_at: float = field(default_factory=time.time)
    description: Optional[str] = None


class PCardIdentity:
    """
    Represents the persistent identity of a Cubical Logic Model.
    
    A PCardIdentity maintains a stable reference (ID) while its internal logic
    (PCardSnapshot) evolves over time through a trajectory of upgrades.
    """

    def __init__(
        self, 
        metadata: PCardMetadata, 
        state: PCardState, 
        contract: PCardContract
    ):
        self.metadata = metadata
        self.state = state
        self.contract = contract
        self.logger = logging.getLogger(__name__)

    @classmethod
    def create_genesis(
        cls, 
        snapshot_hash: str, 
        owner: str, 
        pcard_id: Optional[str] = None,
        description: Optional[str] = None
    ) -> 'PCardIdentity':
        """
        Create a new PCard Identity (Genesis) pointing to an initial snapshot.
        
        Args:
            snapshot_hash: MCard hash of the initial PCardSnapshot (v1).
            owner: Owner identifier.
            pcard_id: Optional custom ID (defaults to new UUID).
            description: Optional description.
            
        Returns:
            New PCardIdentity instance.
        """
        pcard_id = pcard_id or str(uuid.uuid4())
        
        metadata = PCardMetadata(
            id=pcard_id,
            owner=owner,
            description=description
        )
        
        state = PCardState(
            version=1,
            head=snapshot_hash,
            previous=None
        )
        
        contract = PCardContract()
        
        return cls(metadata, state, contract)

    def upgrade(self, new_snapshot_hash: str) -> None:
        """
        Upgrade the PCard to a new snapshot version.
        
        Args:
            new_snapshot_hash: MCard hash of the new PCardSnapshot.
        """
        # In a real implementation, we would verify contract rules here
        # e.g., check if new snapshot is compatible with abstract spec
        
        # Create new state
        new_state = PCardState(
            version=self.state.version + 1,
            head=new_snapshot_hash,
            previous=self.state.head  # Link to previous head for simple lineage
        )
        
        self.state = new_state
        self.logger.info(f"PCard {self.metadata.id} upgraded to version {self.state.version}")

    def fork(self, owner: str, description: Optional[str] = None) -> 'PCardIdentity':
        """
        Fork this PCard Identity to create a new independent identity.
        
        The new PCard starts with the current snapshot but has a new ID and owner.
        
        Args:
            owner: Owner of the new forked PCard.
            description: Optional description for the fork.
            
        Returns:
            New PCardIdentity instance (the fork).
        """
        new_id = str(uuid.uuid4())
        
        metadata = PCardMetadata(
            id=new_id,
            owner=owner,
            description=description or f"Fork of {self.metadata.id}"
        )
        
        # Fork starts at version 1, pointing to the same head
        state = PCardState(
            version=1,
            head=self.state.head,
            previous=None # New lineage starts here (could link to parent in metadata)
        )
        
        contract = PCardContract() # Default contract
        
        self.logger.info(f"PCard {self.metadata.id} forked to {new_id}")
        return PCardIdentity(metadata, state, contract)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "type": "PCard",
            "metadata": {
                "id": self.metadata.id,
                "owner": self.metadata.owner,
                "created_at": self.metadata.created_at,
                "description": self.metadata.description
            },
            "state": {
                "version": self.state.version,
                "head": self.state.head,
                "previous": self.state.previous,
                "timestamp": self.state.timestamp
            },
            "contract": {
                "upgradability": self.contract.upgradability,
                "rules": self.contract.rules
            }
        }

    def to_yaml(self) -> str:
        """Convert to YAML string."""
        return yaml.safe_dump(self.to_dict(), default_flow_style=False)

    @classmethod
    def from_yaml(cls, yaml_content: str) -> 'PCardIdentity':
        """Load from YAML content."""
        data = yaml.safe_load(yaml_content)
        
        if data.get("type") != "PCard":
            raise ValueError("Invalid YAML: type must be 'PCard'")
            
        metadata_data = data.get("metadata", {})
        metadata = PCardMetadata(
            id=metadata_data.get("id"),
            owner=metadata_data.get("owner"),
            created_at=metadata_data.get("created_at", time.time()),
            description=metadata_data.get("description")
        )
        
        state_data = data.get("state", {})
        state = PCardState(
            version=state_data.get("version"),
            head=state_data.get("head"),
            previous=state_data.get("previous"),
            timestamp=state_data.get("timestamp", time.time())
        )
        
        contract_data = data.get("contract", {})
        contract = PCardContract(
            upgradability=contract_data.get("upgradability", "uups"),
            rules=contract_data.get("rules", [])
        )
        
        return cls(metadata, state, contract)
