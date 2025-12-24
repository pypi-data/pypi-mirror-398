"""
Polynomial Type Runtime (PTR) Package

A Python implementation of the PTR execution sidecar for CLM verification.
PTR enforces the Cubical Logic Model through mandatory verification gates,
using MCard for content-addressable storage and YAML templates for CLM definitions.
"""

__version__ = "0.1.0"

from .clm.assembler import CLMAssembler
from .clm.loader import YAMLTemplateLoader
from .core.engine import PTREngine
from .core.lens_protocol import LensProtocol
from .core.verifier import CLMVerifier
from .mcard_integration.storage import MCardStorage

# Default PTR instance for quick access
default_engine = PTREngine()
default_verifier = CLMVerifier(default_engine)
default_lens_protocol = LensProtocol(default_engine)

__all__ = [
    "PTREngine",
    "CLMVerifier",
    "LensProtocol",
    "YAMLTemplateLoader",
    "CLMAssembler",
    "MCardStorage",
    "default_engine",
    "default_verifier",
    "default_lens_protocol",
]
