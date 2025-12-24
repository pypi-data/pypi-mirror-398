"""DOTS Vocabulary Types - Double Operadic Theory of Systems.

This module defines the core vocabulary from the DOTS framework,
which provides a minimal, mathematically grounded language for describing
any compositional system, including MVP Cards architecture.

DOTS Vocabulary
===============

The DOTS vocabulary consists of 9 fundamental terms that form a
complete language for describing compositional systems:

+----------+--------------------+-----------------------------+
| Term     | Definition         | MVP Cards Mapping           |
+----------+--------------------+-----------------------------+
| Arena    | Container for IO   | VCard (boundary/gatekeeper) |
| Lens     | Bidirectional map  | PCard (CLM transformations) |
| Chart    | Category positions | CLM YAML specification      |
| Target   | Design space       | CLM Abstract/Balanced/Conc  |
| Carrier  | Actual systems     | MCard (content-addressable) |
| Tight    | Vertical/∧ ops     | Prerequisite dependencies   |
| Loose    | Horizontal/∨ ops   | Alternative options         |
| Action   | Morphism in Car    | CardCollection.add()        |
| Unit     | Identity element   | Empty MCard / null content  |
+----------+--------------------+-----------------------------+

Polynomial Functor Foundation
=============================

The DOTS vocabulary is grounded in **polynomial functor algebra**:

    p(y) = Σ(s:S) y^{d(s)}

Where:
- S = positions (types/states)
- d(s) = directions from each position (transitions)

This maps to MVP Cards as:

    MVP(y) = Interface × y^Operations

Which expresses: "For each interface, we have a set of possible operations."

See Also:
    - docs/WorkingNotes/Hub/Theory/Integration/DOTS Vocabulary as Efficient Representation for ABC Curriculum.md
    - docs/WorkingNotes/Permanent/Projects/PKC Kernel/MCard.md
    - docs/WorkingNotes/Permanent/Projects/PKC Kernel/PCard.md
    - docs/WorkingNotes/Permanent/Projects/PKC Kernel/VCard.md
"""
from enum import Enum
from dataclasses import dataclass
from typing import Optional, List


class DOTSRole(Enum):
    """The 9 fundamental DOTS vocabulary terms.
    
    From the Double Operadic Theory of Systems, these terms provide
    a complete language for describing any compositional system.
    """
    
    CARRIER = "Carrier"
    """The category of actual systems (data artifacts).
    
    In MVP Cards: MCard instances - immutable, content-addressable objects.
    Mathematically: Objects and morphisms in Car(S).
    """
    
    LENS = "Lens"
    """Bidirectional transformations between systems.
    
    In MVP Cards: PCard transformations that map input → output.
    Mathematically: Chart composed with an arena map.
    """
    
    CHART = "Chart"
    """Category positions and interface definitions.
    
    In MVP Cards: CLM YAML specifications defining the transformation.
    Mathematically: Functor specifying positions in the Target category.
    """
    
    ARENA = "Arena"
    """Container for input/output operations; the system boundary.
    
    In MVP Cards: VCard - the sovereign gatekeeper for all IO.
    Mathematically: A polynomial functor p with sum and product types.
    """
    
    ACTION = "Action"
    """Morphisms in the Carrier category; state transitions.
    
    In MVP Cards: CardCollection.add() - produces new MCards.
    Mathematically: Loose(I) ⊛ Car(S) → Car(S).
    """
    
    TARGET = "Target"
    """The design space; categories of possible interfaces.
    
    In MVP Cards: CLM Abstract/Balanced/Concrete triad.
    Mathematically: Category of polynomials Poly.
    """
    
    TIGHT = "Tight"
    """Vertical composition; prerequisite dependencies (∧).
    
    In MVP Cards: Sequential execution, dependency chains.
    Mathematically: Product types, conjunction.
    """
    
    LOOSE = "Loose"
    """Horizontal composition; alternative options (∨).
    
    In MVP Cards: Parallel execution, polyglot consensus.
    Mathematically: Sum types, disjunction.
    """
    
    UNIT = "Unit"
    """Identity element; the starting point.
    
    In MVP Cards: Empty collection, null content.
    Mathematically: Terminal object 1 in the category.
    """


class EOSRole(Enum):
    """Experimental-Operational Symmetry roles.
    
    Each MVP Card type plays a specific role in maintaining the
    symmetry between experimental (development) and operational
    (production) environments.
    """
    
    INVARIANT_CONTENT = "InvariantContent"
    """MCard: The Galois root - same content = same hash everywhere.
    
    This is the "Joint Reality" P(H,E) = P(E,H) in Bayesian terms.
    Hash computation is a pure function with no side effects.
    """
    
    GENERATIVE_LENS = "GenerativeLens"
    """PCard: The dynamic lens - pure function transformations.
    
    PCard transformations must be deterministic and reproducible.
    Same input + same PCard = same output in any environment.
    """
    
    SOVEREIGN_DECISION = "SovereignDecision"
    """VCard: The gatekeeper - authorized IO and value exchange.
    
    VCard manages credentials, authorization, and controlled side effects.
    Only VCard can break symmetry; it documents when and why.
    """


class CardPlane(Enum):
    """MVP Cards architectural planes.
    
    The triadic architecture separates concerns into three planes,
    each with distinct responsibilities and DOTS vocabulary mappings.
    """
    
    DATA = "Data"
    """MCard plane: Immutable, content-addressable storage.
    
    DOTS Role: Carrier
    Responsibilities: Store, hash, retrieve content
    """
    
    CONTROL = "Control"
    """PCard plane: Polynomial functor composition.
    
    DOTS Role: Lens + Chart
    Responsibilities: Transform, compose, verify
    """
    
    APPLICATION = "Application"
    """VCard plane: Value exchange and authorization.
    
    DOTS Role: Arena + Action
    Responsibilities: AuthN/AuthZ, IO gatekeeper, credentials
    """


@dataclass
class PolynomialFunctor:
    """Representation of a polynomial functor p(y) = Σ(s:S) y^{d(s)}.
    
    Polynomial functors are the mathematical foundation for DOTS.
    They capture the notion of "interface + operations" in a precise way.
    
    Attributes:
        positions: List of position names (S = set of states/types)
        directions: Dict mapping position → list of direction names
    
    Example:
        A simple boolean functor:
        >>> p = PolynomialFunctor(
        ...     positions=['true', 'false'],
        ...     directions={'true': ['stay', 'flip'], 'false': ['stay', 'flip']}
        ... )
    """
    positions: List[str]
    directions: dict  # position → list of directions


@dataclass
class DOTSMetadata:
    """DOTS vocabulary metadata for a card.
    
    This dataclass captures the DOTS role information for any card,
    enabling programmatic identification of the card's role in the
    compositional system.
    
    Attributes:
        role: Primary DOTS role (Carrier, Lens, Chart, Arena, etc.)
        eos_role: Experimental-Operational Symmetry role
        plane: MVP Cards architectural plane
        polynomial: Optional polynomial functor representation
        tight_refs: Prerequisite hash references (vertical composition)
        loose_refs: Alternative hash references (horizontal composition)
    """
    role: DOTSRole
    eos_role: Optional[EOSRole]
    plane: CardPlane
    polynomial: Optional[PolynomialFunctor] = None
    tight_refs: Optional[List[str]] = None
    loose_refs: Optional[List[str]] = None


def create_mcard_dots_metadata(
    tight_refs: Optional[List[str]] = None,
    loose_refs: Optional[List[str]] = None
) -> DOTSMetadata:
    """Create DOTS metadata for an MCard.
    
    MCard is always a CARRIER in the DATA plane with INVARIANT_CONTENT role.
    
    Args:
        tight_refs: Optional prerequisite hash references
        loose_refs: Optional alternative hash references
        
    Returns:
        DOTSMetadata configured for MCard
        
    Example:
        >>> meta = create_mcard_dots_metadata()
        >>> meta.role
        <DOTSRole.CARRIER: 'Carrier'>
        >>> meta.plane
        <CardPlane.DATA: 'Data'>
    """
    return DOTSMetadata(
        role=DOTSRole.CARRIER,
        eos_role=EOSRole.INVARIANT_CONTENT,
        plane=CardPlane.DATA,
        polynomial=PolynomialFunctor(
            positions=['content'],
            directions={'content': ['hash', 'get', 'text']}
        ),
        tight_refs=tight_refs,
        loose_refs=loose_refs
    )


def create_pcard_dots_metadata(
    spec_hash: Optional[str] = None,
    tight_refs: Optional[List[str]] = None,
    loose_refs: Optional[List[str]] = None
) -> DOTSMetadata:
    """Create DOTS metadata for a PCard.
    
    PCard is LENS + CHART in the CONTROL plane with GENERATIVE_LENS role.
    
    Args:
        spec_hash: Optional hash of the CLM specification
        tight_refs: Sequential execution dependencies
        loose_refs: Parallel/polyglot alternatives
        
    Returns:
        DOTSMetadata configured for PCard
    """
    return DOTSMetadata(
        role=DOTSRole.LENS,
        eos_role=EOSRole.GENERATIVE_LENS,
        plane=CardPlane.CONTROL,
        polynomial=PolynomialFunctor(
            positions=['abstract', 'balanced', 'concrete'],
            directions={
                'abstract': ['specification'],
                'balanced': ['parse', 'verify', 'execute'],
                'concrete': ['code', 'runtime', 'result']
            }
        ),
        tight_refs=tight_refs or ([spec_hash] if spec_hash else None),
        loose_refs=loose_refs
    )


def create_vcard_dots_metadata(
    credential_hash: Optional[str] = None,
    tight_refs: Optional[List[str]] = None,
    loose_refs: Optional[List[str]] = None
) -> DOTSMetadata:
    """Create DOTS metadata for a VCard.
    
    VCard is ARENA + ACTION in the APPLICATION plane with SOVEREIGN_DECISION role.
    
    Args:
        credential_hash: Optional hash of the credential/certificate
        tight_refs: Authorization chain dependencies
        loose_refs: Alternative authorization paths
        
    Returns:
        DOTSMetadata configured for VCard
    """
    return DOTSMetadata(
        role=DOTSRole.ARENA,
        eos_role=EOSRole.SOVEREIGN_DECISION,
        plane=CardPlane.APPLICATION,
        polynomial=PolynomialFunctor(
            positions=['ingress', 'egress', 'internal'],
            directions={
                'ingress': ['authenticate', 'authorize', 'admit'],
                'egress': ['sign', 'encrypt', 'emit'],
                'internal': ['store', 'retrieve', 'delete']
            }
        ),
        tight_refs=tight_refs or ([credential_hash] if credential_hash else None),
        loose_refs=loose_refs
    )
