"""
PTR Core Module

Core components for the Polynomial Type Runtime system.

Includes:
- PTREngine: The main execution engine for CLMs
- CLMVerifier: Verification of CLM specifications
- LensProtocol: Bidirectional transformations
- NetworkRuntime: Network IO operations
- Action: The Action monad for composable CLM actions
- P2PChatSession: P2P session recording
"""

from .engine import PTREngine
from .lens_protocol import LensProtocol
from .verifier import CLMVerifier
from .runtime import RuntimeType, BoundaryType, RuntimeExecutor

# Action monad for composable CLM actions
from .action import (
    Action,
    ActionContext,
    ActionEffect,
    ActionResult,
    ActionStatus,
    sequence,
    parallel,
    kleisli_compose,
    identity_action,
)

# P2P Session recording
from .p2p_session import P2PChatSession, SessionMessage

# Optional NetworkRuntime (requires aiohttp)
try:
    from .network_runtime import NetworkRuntime
    __all__ = [
        "PTREngine", "CLMVerifier", "LensProtocol", "NetworkRuntime",
        "RuntimeType", "BoundaryType", "RuntimeExecutor",
        "Action", "ActionContext", "ActionEffect", "ActionResult", "ActionStatus",
        "sequence", "parallel", "kleisli_compose", "identity_action",
        "P2PChatSession", "SessionMessage",
    ]
except ImportError:
    __all__ = [
        "PTREngine", "CLMVerifier", "LensProtocol",
        "RuntimeType", "BoundaryType", "RuntimeExecutor",
        "Action", "ActionContext", "ActionEffect", "ActionResult", "ActionStatus",
        "sequence", "parallel", "kleisli_compose", "identity_action",
        "P2PChatSession", "SessionMessage",
    ]

