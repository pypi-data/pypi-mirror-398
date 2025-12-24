"""Storage resource types - databases and object storage."""

from .core import ResourceType, ResourceCategory

# Storage resource type definitions as pure data
RESOURCE_TYPES = {
    "sqlite": ResourceType(
        name="sqlite",
        category=ResourceCategory.STORAGE.value,
        uri_template="sqlite://{path}",
        hash_template="sqlite:{path}",
        default_options={"engine": "sqlite", "required": True},
        arg_names=["path"]
    ),
    
    "postgres": ResourceType(
        name="postgres",
        category=ResourceCategory.STORAGE.value,
        uri_template="postgres://{connection}",
        hash_template="postgres:{connection}",
        default_options={"engine": "postgresql", "required": True},
        arg_names=["connection"]
    ),
    
    "s3": ResourceType(
        name="s3",
        category=ResourceCategory.STORAGE.value,
        uri_template="s3://{bucket}/{key}",
        hash_template="s3:{bucket}/{key}",
        default_options={"engine": "s3", "region": "us-east-1"},
        arg_names=["bucket", "key"]
    ),
    
    # LiteFS: Distributed SQLite replication (Fly.io)
    "litefs": ResourceType(
        name="litefs",
        category=ResourceCategory.STORAGE.value,
        uri_template="litefs://{path}",
        hash_template="litefs:{path}:{primary}",
        default_options={
            "engine": "litefs",
            "primary": None,
            "lease_key": None,
            "required": True
        },
        arg_names=["path"]
    ),
    
    # Turso: Edge SQLite (libSQL)
    "turso": ResourceType(
        name="turso",
        category=ResourceCategory.STORAGE.value,
        uri_template="libsql://{database}.turso.io",
        hash_template="turso:{database}:{group}",
        default_options={
            "engine": "turso",
            "group": "default",
            "auth_token_env_var": "TURSO_AUTH_TOKEN",
            "sync_url": None,
            "required": True
        },
        arg_names=["database"]
    ),
}
