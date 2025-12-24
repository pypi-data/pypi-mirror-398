"""Core resource types and base registry."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Dict, Any, Callable


class ResourceCategory(Enum):
    """Categories of external resources (side effects)."""
    ENVIRONMENT = "env"
    FILESYSTEM = "file"
    STORAGE = "storage"
    NETWORK = "network"
    OBSERVABILITY = "observability"
    COMPUTE = "compute"
    RANDOM = "random"


@dataclass
class ResourceType:
    """Definition of a resource type in the registry."""
    name: str                    # Type identifier (e.g., "env", "sqlite", "grafana")
    category: str                # Category string or ResourceCategory value
    uri_template: str            # URI template with {placeholders}
    hash_template: str           # Hash content template
    default_options: Dict[str, Any] = field(default_factory=dict)
    arg_names: list = field(default_factory=list)  # Positional argument names


# Core resource types that are always available
RESOURCE_REGISTRY: Dict[str, ResourceType] = {
    # Environment
    "env": ResourceType(
        name="env",
        category=ResourceCategory.ENVIRONMENT.value,
        uri_template="env://{name}",
        hash_template="env:{name}:{required}:{secret}",
        default_options={"required": True, "secret": False},
        arg_names=["name"]
    ),
    
    # Filesystem
    "file": ResourceType(
        name="file",
        category=ResourceCategory.FILESYSTEM.value,
        uri_template="file://{path}",
        hash_template="file:{path}",
        default_options={"mode": "read", "required": True},
        arg_names=["path"]
    ),
    "directory": ResourceType(
        name="directory",
        category=ResourceCategory.FILESYSTEM.value,
        uri_template="file://{path}/",
        hash_template="dir:{path}",
        default_options={"recursive": True},
        arg_names=["path"]
    ),
}
