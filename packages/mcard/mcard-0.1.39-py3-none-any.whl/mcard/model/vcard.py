"""VCard Model (Application Plane) - Implementation of Arena + Action.

This module defines the VCard, which represents the sovereign decision layer
in the MVP Cards architecture. VCard is the IO Monad that manages all side effects.

Categorical Role:
    - Applicative Functor (<*>): Applies PCard functions with side effects.
    - UPTV Role: Token/Evidence container and Gateway.

DOTS Vocabulary Role: Arena + Action
====================================

VCard is both:
- **Arena**: The interface type defining what can interact (subject_did, capabilities, external_refs)
- **Action**: The morphism where interactions (PCards) act on systems (MCards) to produce new systems

Empty Schema Principle:
=======================
VCard IS an MCard. It has no additional schema fields. Its "VCard-ness" comes
from its structured YAML content (Abstract/Concrete/Balanced logic mapped to policies).

The Four Roles (Content Sections):
1. Identity & Credential Container (The "Who") -> `identity`
2. Verification Hub (The "Rules") -> `verification`
3. Side Effect Manager (The "Bridge") -> `external_refs`
4. Input/Output Gatekeeper (The "Gate") -> `gatekeeper`

See Also:
    - docs/VCard_Impl.md
"""

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Optional, Dict, List, Any, Union, cast
from datetime import datetime
import json
import yaml
import hashlib

from mcard.model.card import MCard
from mcard.model.hash.validator import HashAlgorithm
from mcard.model.dots import (
    create_vcard_dots_metadata, 
    DOTSMetadata
)


class CapabilityScope(Enum):
    """Scope of a capability token."""
    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"
    ADMIN = "admin"
    DELEGATE = "delegate"


class GatekeeperDirection(Enum):
    """Direction of gatekeeper authorization."""
    INGRESS = "ingress"  # Content entering the PKC
    EGRESS = "egress"    # Content leaving the PKC


@dataclass
class Capability:
    """A capability token defining authorized actions."""
    capability_id: str
    actor_did: str
    scope: CapabilityScope
    resource_pattern: str  # Regex or glob pattern for resources
    expires_at: Optional[datetime] = None
    constraints: Dict[str, Any] = field(default_factory=dict)
    transferable: bool = False
    
    def is_valid(self) -> bool:
        """Check if the capability is still valid."""
        if self.expires_at is None:
            return True
        # Simple naive check; in production use timezone-aware UTC
        return datetime.now() < self.expires_at
    
    def matches_resource(self, resource_hash: str) -> bool:
        """Check if this capability applies to a resource."""
        import re
        return bool(re.match(self.resource_pattern, resource_hash))
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "id": self.capability_id,
            "actor": self.actor_did,
            "scope": self.scope.value,
            "resource_pattern": self.resource_pattern,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "transferable": self.transferable,
            "constraints": self.constraints
        }


@dataclass
class ExternalRef:
    """A verified external reference managed by VCard (IO Monad)."""
    uri: str
    content_hash: str
    status: str  # "verified", "pending", "stale", "invalid"
    signature: Optional[str] = None
    last_verified: Optional[datetime] = None
    qos_metrics: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "uri": self.uri,
            "content_hash": self.content_hash,
            "status": self.status,
            "qos": self.qos_metrics
        }


@dataclass
class GatekeeperEvent:
    """An ingress or egress gatekeeper event."""
    direction: GatekeeperDirection
    timestamp: datetime
    source_did: Optional[str]  # For ingress
    destination_did: Optional[str]  # For egress
    content_hash: str
    authorized: bool
    capability_used: Optional[str] = None
    signature: Optional[str] = None


# =============================================================================
# Functional Helpers (The Preferred API)
# =============================================================================

def is_vcard(card: MCard) -> bool:
    """Check if an MCard contains VCard content."""
    try:
        content = yaml.safe_load(card.get_content(as_text=True))
        # Support both JSON-style (root keys) and VCard-root style
        if isinstance(content, dict):
             if 'vcard' in content and content['vcard'].get('type') == 'authentication-authorization':
                 return True
             if content.get('type') == 'VCard': # Legacy/Direct JSON support
                 return True
        return False
    except Exception:
        return False

def create_vcard_content(
    subject_did: str,
    controller_pubkeys: List[str],
    capabilities: List[Capability],
    external_refs: List[ExternalRef],
    pcard_refs: Optional[List[Dict[str, Any]]] = None,
    gatekeeper_config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Generate the standard VCard content structure."""
    
    # Normalize pcard_refs if likely passed as list of strings or dicts
    final_pcard_refs = pcard_refs or []
    
    # Construct the canonical VCard YAML Structure as per docs/VCard_Impl.md
    return {
        'vcard': {
            'version': '1.0',
            'type': 'authentication-authorization',
            'identity': {
                'subject_did': subject_did,
                'controller_pubkeys': controller_pubkeys,
                'issued_at': datetime.utcnow().isoformat()
            },
            'verification': {
                'pcard_refs': final_pcard_refs
            },
            # Map capability objects to list of dicts if needed, or store in gatekeeper
            # Note: The doc puts capabilities in `gatekeeper.capabilities`
            'gatekeeper': gatekeeper_config or {
                'ingress_policies': [],
                'egress_policies': [],
                'capabilities': [c.to_dict() for c in capabilities]
            },
            'external_refs': [r.to_dict() for r in external_refs]
        }
    }

def get_pcard_refs(vcard: MCard) -> List[str]:
    """Extract PCard reference hashes from VCard."""
    content = _parse_vcard_content(vcard)
    refs = content.get('verification', {}).get('pcard_refs', [])
    # Return just hashes if they are dicts
    return [r['hash'] if isinstance(r, dict) else r for r in refs]

def get_subject_did(vcard: MCard) -> Optional[str]:
    """Extract subject DID from VCard."""
    content = _parse_vcard_content(vcard)
    return content.get('identity', {}).get('subject_did') or content.get('subject_did')

def create_vcard(
    subject_did: str,
    controller_pubkeys: List[str],
    capabilities: Optional[List[Capability]] = None,
    external_refs: Optional[List[ExternalRef]] = None
) -> MCard:
    """Functional factory to create a VCard (returns VCard instance which IS MCard)."""
    return VCard(
        subject_did=subject_did,
        controller_pubkeys=controller_pubkeys,
        capabilities=capabilities,
        external_refs=external_refs
    )

def _parse_vcard_content(card: MCard) -> Dict[str, Any]:
    """Internal helper to parse VCard content, verifying structure."""
    raw = yaml.safe_load(card.get_content(as_text=True))
    if 'vcard' in raw:
        return raw['vcard']
    # Fallback to direct dict (Legacy/JSON compat)
    return raw


# =============================================================================
# VCard Class (MCard View / Wrapper)
# =============================================================================

class VCard(MCard):
    """VCard - The Application Plane unit (Arena + Action).
    
    Compatible wrapper that behaves like an MCard but provides VCard-specific
    application logic.
    
    IMPORTANT: While MCard content is immutable (and thus the .hash attribute 
    refers to the INITIAL content), this Python object allows in-memory mutation 
    of capabilities and logs to support runtime Gatekeeper logic.
    """
    
    def __init__(
        self,
        subject_did: Union[str, bytes],
        controller_pubkeys: Optional[List[str]] = None,
        capabilities: Optional[List[Capability]] = None,
        external_refs: Optional[List[ExternalRef]] = None,
        hash_function: Union[str, HashAlgorithm] = "sha256",
        # Support for wrapping existing content
        content_only: bool = False 
    ):
        """Initialize a VCard.
        
        This constructor is overloaded to support:
        1. Creating NEW VCard: pass subject_did, keys, etc.
        2. Wrapping EXISTING content: pass content as first arg.
        """
        
        # Check if we are creating from scratch or wrapping
        is_creation = controller_pubkeys is not None
        
        self._gatekeeper_log: List[GatekeeperEvent] = []
        self._export_manifest: List[str] = []

        if is_creation:
            # Creation Mode
            full_content_dict = create_vcard_content(
                subject_did=cast(str, subject_did),
                controller_pubkeys=controller_pubkeys or [],
                capabilities=capabilities or [],
                external_refs=external_refs or []
            )
            
            # Use inner dict for initial state
            initial_data = full_content_dict['vcard']
            
            # Serialize to JSON for MCard storage (Immutable Base)
            final_content = json.dumps(full_content_dict, sort_keys=True)
            super().__init__(final_content, hash_function)
        else:
            # Wrapping Mode (subject_did is actually content)
            super().__init__(subject_did, hash_function)
            initial_data = _parse_vcard_content(self)
        
        # Initialize Mutable State from Content
        self._initialize_mutable_state(initial_data)

    def _initialize_mutable_state(self, data: Dict[str, Any]):
        """Hydrate mutable lists from parsed content dictionary."""
        # 1. Identity
        self._subject_did = data.get('identity', {}).get('subject_did') or data.get('subject_did', '')
        self._controller_pubkeys = data.get('identity', {}).get('controller_pubkeys') or data.get('controller_pubkeys', [])

        # 2. Capabilities
        raw_caps = data.get('gatekeeper', {}).get('capabilities') or data.get('capabilities', [])
        self._capabilities: List[Capability] = []
        for c in raw_caps:
            try:
                if isinstance(c, dict):
                    self._capabilities.append(Capability(
                        capability_id=c['id'],
                        actor_did=c['actor'],
                        scope=CapabilityScope(c['scope']),
                        resource_pattern=c['resource_pattern'],
                        expires_at=datetime.fromisoformat(c['expires_at']) if c.get('expires_at') else None,
                        transferable=c.get('transferable', False),
                        constraints=c.get('constraints', {})
                    ))
            except Exception:
                continue 

        # 3. External Refs (including PCard refs)
        raw_refs = data.get('external_refs', [])
        self._external_refs: List[ExternalRef] = []
        for r in raw_refs:
            if isinstance(r, dict):
                self._external_refs.append(ExternalRef(
                    uri=r.get('uri', ''),
                    content_hash=r.get('content_hash', ''),
                    status=r.get('status', 'pending'),
                    qos_metrics=r.get('qos', {})
                ))
        
        # 4. PCard Refs (Verification) -> Merged into External Refs conceptually or tracked?
        # The docs says PCard refs are in verification block.
        # But old test 'add_pcard_reference' expects them to be retrievable.
        # We will parse them but `add_pcard_reference` typically adds to external refs 
        # or we keep a separate list? The doc says "references PCards as procedures".
        # Let's check `get_pcard_references` implementation below.
        
        # We will trust `_external_refs` to hold all refs including pcards if they were stored there.
        # But if they are in `verification.pcard_refs`, we should probably track them too.
        self._pcard_refs_hashes = [
            r['hash'] if isinstance(r, dict) else r 
            for r in data.get('verification', {}).get('pcard_refs', [])
        ]


    # =========================================================================
    # Role 1: Identity & Credential Container
    # =========================================================================
    
    @property
    def subject_did(self) -> str:
        return self._subject_did

    @property
    def controller_pubkeys(self) -> List[str]:
        return self._controller_pubkeys

    @property
    def capabilities(self) -> List[Capability]:
        return self._capabilities

    def add_capability(self, capability: Capability) -> None:
        """Add a new capability to this VCard (Runtime Memory Only)."""
        self._capabilities.append(capability)
    
    def get_valid_capabilities(self) -> List[Capability]:
        """Get all currently valid capabilities."""
        return [c for c in self._capabilities if c.is_valid()]

    # =========================================================================
    # Role 2: Verification Hub
    # =========================================================================
    
    def add_pcard_reference(self, pcard_hash: str) -> None:
        """Register a PCard for verification."""
        # Add to the specific list
        if pcard_hash not in self._pcard_refs_hashes:
            self._pcard_refs_hashes.append(pcard_hash)
        
        # Also add as generic external ref as per old implementation
        ref = ExternalRef(
            uri=f"pcard://{pcard_hash}",
            content_hash=pcard_hash,
            status="verified"
        )
        self.add_external_ref(ref)
    
    def get_pcard_references(self) -> List[str]:
        """Get all registered PCard hashes."""
        # Return unique set of explicitly tracked + those in external refs
        refs = set(self._pcard_refs_hashes)
        for r in self._external_refs:
             if r.uri.startswith("pcard://"):
                 refs.add(r.content_hash)
        return list(refs)

    # =========================================================================
    # Role 3: Side Effect Manager
    # =========================================================================

    @property
    def external_refs(self) -> List[ExternalRef]:
        return self._external_refs

    def add_external_ref(self, ref: ExternalRef) -> None:
        """Add an external reference (describes a side effect)."""
        self._external_refs.append(ref)
    
    def get_external_refs_by_status(self, status: str) -> List[ExternalRef]:
        """Get external references by verification status."""
        return [r for r in self._external_refs if r.status == status]
    
    def verify_external_ref(self, uri: str, new_hash: str) -> bool:
        """Verify an external reference and update its status."""
        for ref in self._external_refs:
            if ref.uri == uri:
                if ref.content_hash == new_hash:
                    ref.status = "verified"
                    ref.last_verified = datetime.now()
                    return True
                else:
                    ref.status = "stale"
                    return False
        return False

    # =========================================================================
    # Role 4: Input/Output Gatekeeper
    # =========================================================================
    
    def has_capability(self, scope: CapabilityScope, resource_hash: str) -> bool:
        """Check if VCard has a valid capability for a resource."""
        for cap in self.get_valid_capabilities():
            if cap.scope == scope and cap.matches_resource(resource_hash):
                return True
        return False

    def authorize_ingress(
        self,
        source_did: str,
        content_hash: str,
        capability_id: Optional[str] = None
    ) -> bool:
        """Authorize content entering the PKC (ingress)."""
        authorized = False
        used_capability = None
        
        # Check if source has ingress capability
        for cap in self.get_valid_capabilities():
            if cap.actor_did == source_did and cap.scope in [CapabilityScope.WRITE, CapabilityScope.ADMIN]:
                if capability_id is None or cap.capability_id == capability_id:
                    authorized = True
                    used_capability = cap.capability_id
                    break
        
        # Log the gatekeeper event
        event = GatekeeperEvent(
            direction=GatekeeperDirection.INGRESS,
            timestamp=datetime.now(),
            source_did=source_did,
            destination_did=None,
            content_hash=content_hash,
            authorized=authorized,
            capability_used=used_capability
        )
        self._gatekeeper_log.append(event)
        return authorized

    def register_for_egress(self, content_hash: str) -> bool:
        """Register content for potential egress."""
        if content_hash not in self._export_manifest:
            self._export_manifest.append(content_hash)
            return True
        return False
    
    def authorize_egress(
        self,
        destination_did: str,
        content_hash: str,
        capability_id: Optional[str] = None
    ) -> bool:
        """Authorize content leaving the PKC (egress)."""
        if content_hash not in self._export_manifest:
            self._log_egress_attempt(destination_did, content_hash, False, "Not registered in manifest")
            return False
        
        authorized = False
        used_capability = None
        
        for cap in self.get_valid_capabilities():
            if cap.scope in [CapabilityScope.READ, CapabilityScope.ADMIN]:
                if cap.matches_resource(content_hash):
                    if capability_id is None or cap.capability_id == capability_id:
                        authorized = True
                        used_capability = cap.capability_id
                        break
        
        self._log_egress_attempt(destination_did, content_hash, authorized, used_capability)
        return authorized

    def _log_egress_attempt(self, dst, hash_val, auth, cap_id):
        event = GatekeeperEvent(
            direction=GatekeeperDirection.EGRESS,
            timestamp=datetime.now(),
            source_did=None,
            destination_did=dst,
            content_hash=hash_val,
            authorized=auth,
            capability_used=cap_id
        )
        self._gatekeeper_log.append(event)

    def get_gatekeeper_log(
        self,
        direction: Optional[GatekeeperDirection] = None
    ) -> List[GatekeeperEvent]:
        """Get gatekeeper audit log."""
        if direction is None:
            return self._gatekeeper_log
        return [e for e in self._gatekeeper_log if e.direction == direction]
    
    def get_dots_metadata(self) -> DOTSMetadata:
        """Get DOTS metadata for this VCard."""
        return create_vcard_dots_metadata(
            credential_hash=self.hash
        )

    # =========================================================================
    # EOS Compliance
    # =========================================================================
    
    def simulate_mode(self) -> 'VCardSimulation':
        """Enter simulation mode for EOS compliance."""
        return VCardSimulation(self)





    # =========================================================================
    # Petri Net Token Semantics
    # =========================================================================

    def get_token_handle(self) -> str:
        """Get the handle for this VCard (Token).

        If verification VCard, returns the creating PCard's balanced handle.
        Otherwise, derives from content.

        Returns:
            Handle string (Place name)
        """
        parsed = _parse_vcard_content(self)
        v = parsed.get('vcard', parsed) if isinstance(parsed, dict) else {}
        
        # explicit handle in content takes precedence (e.g. verification output)
        if v.get('handle'):
            return v['handle']
        if v.get('token_handle'):
            return v['token_handle']
            
        return f"vcard://{self.hash[:16]}"

    def is_verification_vcard(self) -> bool:
        """Check if this is a Verification VCard (produced by a PCard execution)."""
        parsed = _parse_vcard_content(self)
        v = parsed.get('vcard', parsed) if isinstance(parsed, dict) else {}
        return v.get('type') in ('verification', 'verification-result') or \
               bool(v.get('verification', {}).get('execution_result'))

    @staticmethod
    def create_verification_vcard(
        pcard: Any, 
        execution_result: Any, 
        previous_vcard: Optional['VCard'] = None,
        verified: bool = True,
        hash_function: str = "sha256"
    ) -> 'VCard':
        """Create a Verification VCard (Token) from a PCard execution.

        Args:
            pcard: The PCard (Transition) that executed.
            execution_result: The result of the execution.
            previous_vcard: The input VCard (Token) if any (for provenance).
            verified: Whether execution was successful.
            hash_function: Hash algorithm to use.

        Returns:
            A new VCard instance.
        """
        # Calculate handle (Place)
        handle = getattr(pcard, 'get_balanced_handle', lambda: f"clm://hash/{pcard.hash[:16]}/balanced")()

        # Construct content
        content = {
            'vcard': {
                'version': '1.0',
                'type': 'verification',
                'handle': handle,
                'identity': {
                    'subject_did': 'did:ptr:system',
                    'controller_pubkeys': []
                },
                'verification': {
                    'pcard_hash': pcard.hash,
                    'execution_result': execution_result,
                    'success': verified,  # Match JS 'success' field
                    'timestamp': datetime.utcnow().isoformat(),
                    'previous_hash': previous_vcard.hash if previous_vcard else None
                },
                'gatekeeper': {
                    'capabilities': []
                },
                'external_refs': []
            }
        }
        
        # Create VCard from content
        return VCard(json.dumps(content, sort_keys=True), hash_function=hash_function)

    def get_source_pcard_hash(self) -> Optional[str]:
        """Get the hash of the PCard that produced this token."""
        parsed = _parse_vcard_content(self)
        return parsed.get('verification', {}).get('pcard_hash')

    def get_previous_hash(self) -> Optional[str]:
        """Get the previous VCard hash in the provenance chain."""
        parsed = _parse_vcard_content(self)
        return parsed.get('verification', {}).get('previous_hash')

    def enables_transition(self, pcard: 'PCard') -> bool:
        """Check if this VCard can serve as input to the given PCard.

        Args:
            pcard: The transition to check.

        Returns:
            True if this VCard satisfies one of the inputs.
        """
        input_refs = pcard.get_input_vcard_refs()
        my_handle = self.get_token_handle()
        
        for ref in input_refs:
            # Check handle match (if we were stored at that handle)
            # Since VCard model doesn't know where it is stored (Collection knows),
            # this check is limited. We check if we match strict hash requirements.
            if ref.get('expected_hash') == self.hash:
                return True
        
        return False


class VCardSimulation:
    """Simulation context for VCard (EOS Compliance)."""
    
    def __init__(self, vcard: VCard):
        self.vcard = vcard
        self.simulation_log: List[Dict[str, Any]] = []
    
    def log_effect(self, effect_type: str, details: Dict[str, Any]) -> None:
        """Log a simulated side effect."""
        self.simulation_log.append({
            "timestamp": datetime.now().isoformat(),
            "effect_type": effect_type,
            "details": details,
            "simulated": True
        })
    
    def get_simulation_log(self) -> List[Dict[str, Any]]:
        """Get the simulation log."""
        return self.simulation_log
