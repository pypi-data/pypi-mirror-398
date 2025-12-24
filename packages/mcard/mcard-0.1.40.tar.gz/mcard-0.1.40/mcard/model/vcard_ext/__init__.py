"""VCard Extension Types - Resource type definitions as pure data.

This package provides modular resource type definitions that are loaded
automatically into the VCard vocabulary. Each file exports resource type
definitions as dictionaries or ResourceType dataclasses.

Adding new resource types:
1. Create a new .py file in this directory
2. Define RESOURCE_TYPES dict with your type definitions
3. The types are auto-registered on import

Example:
    # my_custom_types.py
    RESOURCE_TYPES = {
        "mytype": {
            "name": "mytype",
            "category": "custom",
            "uri_template": "mytype://{identifier}",
            "hash_template": "mytype:{identifier}",
            "default_options": {"required": True}
        }
    }
"""

from .core import RESOURCE_REGISTRY, ResourceType, ResourceCategory
from .storage import RESOURCE_TYPES as STORAGE_TYPES
from .network import RESOURCE_TYPES as NETWORK_TYPES
from .observability import RESOURCE_TYPES as OBSERVABILITY_TYPES
from .vendors import RESOURCE_TYPES as VENDOR_TYPES

# Auto-register all extension types
for types_dict in [STORAGE_TYPES, NETWORK_TYPES, OBSERVABILITY_TYPES, VENDOR_TYPES]:
    for name, type_def in types_dict.items():
        if isinstance(type_def, dict):
            RESOURCE_REGISTRY[name] = ResourceType(**type_def)
        else:
            RESOURCE_REGISTRY[name] = type_def

__all__ = ['RESOURCE_REGISTRY', 'ResourceType', 'ResourceCategory']
