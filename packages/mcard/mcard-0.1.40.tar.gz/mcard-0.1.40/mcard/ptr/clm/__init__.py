"""
CLM Module - Cubical Logic Model templates and assembly

Provides YAML templates for CLM dimensions and dynamic assembly
using MCard Collections.
"""

from .assembler import CLMAssembler
from .loader import YAMLTemplateLoader

__all__ = ["YAMLTemplateLoader", "CLMAssembler"]
