"""Network resource types - APIs and webhooks."""

from .core import ResourceType, ResourceCategory

# Network resource type definitions as pure data
RESOURCE_TYPES = {
    "api": ResourceType(
        name="api",
        category=ResourceCategory.NETWORK.value,
        uri_template="{endpoint}",
        hash_template="api:{method}:{endpoint}",
        default_options={"type": "api", "method": "GET", "_preserve_uri": True},
        arg_names=["endpoint"]
    ),
    
    "webhook": ResourceType(
        name="webhook",
        category=ResourceCategory.NETWORK.value,
        uri_template="{endpoint}",
        hash_template="webhook:{endpoint}",
        default_options={"type": "webhook", "_preserve_uri": True},
        arg_names=["endpoint"]
    ),
}
