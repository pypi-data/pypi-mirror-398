"""VCard Application Vocabulary - Data-driven patterns for side effects.

This module provides application-specific vocabulary for VCard following the
Empty Schema principle. Resource types are defined as DATA in vcard_ext/,
making the system fully extensible without code changes.

Usage
=====

    from mcard.model.vcard_vocabulary import Resource, ApplicationResources
    
    # Direct factory usage (any registered type)
    ref = Resource.create("env", "DATABASE_URL", required=True)
    ref = Resource.create("turso", "my-database", group="us-east")
    
    # ApplicationResources for managing multiple resources
    resources = ApplicationResources()
    resources.add("env", "DATABASE_URL")
    resources.add("turso", "my-database")
    resources.add_lgtm_stack("http://localhost", "mcard-service")

Extending with new types:
    # Add to vcard_ext/storage.py, network.py, or observability.py
    # Or create a new file and register in vcard_ext/__init__.py
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from pathlib import Path
import hashlib
import os

from mcard.model.vcard import ExternalRef
from mcard.model.vcard_ext import RESOURCE_REGISTRY, ResourceType, ResourceCategory


# Re-export for convenience
__all__ = [
    'Resource', 'ResourceCategory', 'ResourceType', 'RESOURCE_REGISTRY',
    'EnvResource', 'FileResource', 'StorageResource', 'NetworkResource',
    'ObservabilityResource', 'ApplicationResources',
    'create_lgtm_stack', 'create_from_dotenv', 'AccessMode'
]


class AccessMode:
    """Access mode constants for resources."""
    READ = "read"
    WRITE = "write"
    READ_WRITE = "rw"
    EXECUTE = "execute"


# =============================================================================
# Core Resource Factory (Single Entry Point)
# =============================================================================

class Resource:
    """Universal factory for creating ExternalRefs from registry."""
    
    @staticmethod
    def create(resource_type: str, *args, **kwargs) -> ExternalRef:
        """Create an ExternalRef for any registered resource type."""
        if resource_type not in RESOURCE_REGISTRY:
            raise ValueError(f"Unknown resource type: {resource_type}. "
                           f"Available: {list(RESOURCE_REGISTRY.keys())}")
        
        rtype = RESOURCE_REGISTRY[resource_type]
        options = {**rtype.default_options, **kwargs}
        
        # Map positional args using type's arg_names
        template_vars = dict(options)
        for i, arg in enumerate(args):
            if i < len(rtype.arg_names):
                template_vars[rtype.arg_names[i]] = arg
        
        # Build URI
        uri = Resource._build_uri(rtype.uri_template, template_vars)
        
        # Compute hash
        hash_content = Resource._build_hash_content(rtype.hash_template, template_vars)
        content_hash = hashlib.sha256(hash_content.encode()).hexdigest()
        
        # Determine status
        status = Resource._determine_status(resource_type, template_vars, options)
        
        # Build QoS metrics
        qos_metrics = {
            "category": rtype.category if isinstance(rtype.category, str) else rtype.category.value,
            **{k: v for k, v in template_vars.items() if v is not None and not k.startswith('_')}
        }
        
        return ExternalRef(uri=uri, content_hash=content_hash, status=status, qos_metrics=qos_metrics)
    
    @staticmethod
    def _build_uri(template: str, vars: dict) -> str:
        preserve_uri = vars.get('_preserve_uri', False)
        uri = template
        for key, value in vars.items():
            if value is not None and not key.startswith('_'):
                str_val = str(value)
                if not preserve_uri and key in ("endpoint", "collector_url"):
                    str_val = str_val.replace("http://", "").replace("https://", "")
                uri = uri.replace(f"{{{key}}}", str_val)
        return uri
    
    @staticmethod
    def _build_hash_content(template: str, vars: dict) -> str:
        content = template
        for key, value in vars.items():
            content = content.replace(f"{{{key}}}", str(value) if value is not None else "None")
        return content
    
    @staticmethod
    def _determine_status(resource_type: str, vars: dict, options: dict) -> str:
        required = options.get("required", True)
        if resource_type == "env":
            actual = os.environ.get(vars.get("name", ""), options.get("default"))
            if actual is not None:
                return "verified"
            return "invalid" if required else "pending"
        if resource_type in ("file", "directory", "sqlite"):
            path = Path(vars.get("path", ""))
            if path.exists():
                return "verified"
            return "invalid" if required else "pending"
        return "pending"
    
    @staticmethod
    def types() -> List[str]:
        return list(RESOURCE_REGISTRY.keys())
    
    @staticmethod
    def register(resource_type: ResourceType) -> None:
        RESOURCE_REGISTRY[resource_type.name] = resource_type


# =============================================================================
# Helper Functions
# =============================================================================

def create_lgtm_stack(base_url: str, service_name: str,
                      environment: str = "production",
                      ports: Optional[Dict[str, int]] = None) -> List[ExternalRef]:
    """Create ExternalRefs for a complete Grafana LGTM stack."""
    p = {"grafana": 3000, "prometheus": 9090, "loki": 3100, "tempo": 4317, **(ports or {})}
    return [
        Resource.create("grafana", f"{base_url}:{p['grafana']}", description=f"Grafana for {service_name}"),
        Resource.create("prometheus", f"{base_url}:{p['prometheus']}", job_name=service_name),
        Resource.create("loki", f"{base_url}:{p['loki']}", labels={"service": service_name, "environment": environment}),
        Resource.create("tempo", f"{base_url}:{p['tempo']}", service_name=service_name),
    ]


def create_from_dotenv(dotenv_path: str = ".env") -> List[ExternalRef]:
    """Create ExternalRefs for all variables in a .env file."""
    refs = []
    path = Path(dotenv_path)
    if path.exists():
        with open(path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    name = line.split('=')[0].strip()
                    secret = any(s in name.upper() for s in ['KEY', 'SECRET', 'TOKEN', 'PASSWORD'])
                    refs.append(Resource.create("env", name, secret=secret))
    return refs


# =============================================================================
# Convenience Wrappers (Backward Compatibility)
# =============================================================================

class EnvResource:
    @staticmethod
    def create(name: str, required: bool = True, secret: bool = False,
               default: Optional[str] = None, description: Optional[str] = None) -> ExternalRef:
        return Resource.create("env", name, required=required, secret=secret, default=default, description=description)
    
    @staticmethod
    def create_from_dotenv(path: str = ".env") -> List[ExternalRef]:
        return create_from_dotenv(path)
    
    @staticmethod
    def resolve(ref: ExternalRef) -> Optional[str]:
        if not ref.uri.startswith("env://"):
            raise ValueError(f"Not an env:// URI: {ref.uri}")
        return os.environ.get(ref.uri.replace("env://", ""))


class FileResource:
    @staticmethod
    def create(path: str, mode: str = "read", required: bool = True, description: Optional[str] = None) -> ExternalRef:
        abs_path = Path(path).resolve()
        exists = abs_path.exists()
        if exists:
            with open(abs_path, 'rb') as f:
                content_hash = hashlib.sha256(f.read()).hexdigest()
            status = "verified"
        else:
            content_hash = hashlib.sha256(f"file:{abs_path}".encode()).hexdigest()
            status = "invalid" if required else "pending"
        return ExternalRef(
            uri=f"file://{abs_path}", content_hash=content_hash, status=status,
            qos_metrics={"category": "file", "mode": mode, "required": required, "exists": exists, "description": description}
        )
    
    @staticmethod
    def create_directory(path: str, recursive: bool = True, description: Optional[str] = None) -> ExternalRef:
        return Resource.create("directory", path, recursive=recursive, description=description, is_directory=True)
    
    @staticmethod
    def verify(ref: ExternalRef) -> bool:
        if not ref.uri.startswith("file://"):
            raise ValueError(f"Not a file:// URI: {ref.uri}")
        path = Path(ref.uri.replace("file://", "").rstrip("/"))
        if not path.exists():
            return False
        with open(path, 'rb') as f:
            return hashlib.sha256(f.read()).hexdigest() == ref.content_hash


class StorageResource:
    @staticmethod
    def create_sqlite(path: str, **kwargs) -> ExternalRef:
        return Resource.create("sqlite", path, **kwargs)
    
    @staticmethod
    def create_postgres(connection: str, **kwargs) -> ExternalRef:
        return Resource.create("postgres", connection, **kwargs)
    
    @staticmethod
    def create_s3(bucket: str, key: str, **kwargs) -> ExternalRef:
        return Resource.create("s3", bucket, key, **kwargs)
    
    @staticmethod
    def create_litefs(path: str, **kwargs) -> ExternalRef:
        return Resource.create("litefs", path, **kwargs)
    
    @staticmethod
    def create_turso(database: str, **kwargs) -> ExternalRef:
        return Resource.create("turso", database, **kwargs)


class NetworkResource:
    @staticmethod
    def create_api(endpoint: str, **kwargs) -> ExternalRef:
        return Resource.create("api", endpoint, **kwargs)
    
    @staticmethod
    def create_webhook(endpoint: str, **kwargs) -> ExternalRef:
        return Resource.create("webhook", endpoint, **kwargs)


class ObservabilityResource:
    @staticmethod
    def create_grafana(endpoint: str, **kwargs) -> ExternalRef:
        return Resource.create("grafana", endpoint, endpoint=endpoint, **kwargs)
    
    @staticmethod
    def create_prometheus(endpoint: str, **kwargs) -> ExternalRef:
        return Resource.create("prometheus", endpoint, endpoint=endpoint, **kwargs)
    
    @staticmethod
    def create_loki(endpoint: str, **kwargs) -> ExternalRef:
        return Resource.create("loki", endpoint, endpoint=endpoint, **kwargs)
    
    @staticmethod
    def create_tempo(endpoint: str, **kwargs) -> ExternalRef:
        return Resource.create("tempo", endpoint, endpoint=endpoint, **kwargs)
    
    @staticmethod
    def create_faro(collector_url: str, app_name: str, **kwargs) -> ExternalRef:
        return Resource.create("faro", collector_url, app_name, collector_url=collector_url, **kwargs)
    
    @staticmethod
    def create_otlp(endpoint: str, **kwargs) -> ExternalRef:
        return Resource.create("otlp", endpoint, endpoint=endpoint, **kwargs)
    
    @staticmethod
    def create_lgtm_stack(base_url: str, service_name: str, **kwargs) -> List[ExternalRef]:
        return create_lgtm_stack(base_url, service_name, **kwargs)


# =============================================================================
# Application Resources Manager
# =============================================================================

@dataclass
class ApplicationResources:
    """Collection of typed resources for an application."""
    resources: List[ExternalRef] = field(default_factory=list)
    
    def add(self, resource_type: str, *args, **kwargs) -> 'ApplicationResources':
        self.resources.append(Resource.create(resource_type, *args, **kwargs))
        return self
    
    # Convenience methods (delegate to add)
    def add_env(self, name: str, **kwargs): return self.add("env", name, **kwargs)
    def add_env_from_dotenv(self, path: str = ".env"):
        self.resources.extend(create_from_dotenv(path))
        return self
    def add_file(self, path: str, **kwargs): return self.add("file", path, **kwargs)
    def add_directory(self, path: str, **kwargs): return self.add("directory", path, **kwargs)
    def add_sqlite(self, path: str, **kwargs): return self.add("sqlite", path, **kwargs)
    def add_litefs(self, path: str, **kwargs): return self.add("litefs", path, **kwargs)
    def add_turso(self, database: str, **kwargs): return self.add("turso", database, **kwargs)
    def add_api(self, endpoint: str, **kwargs): return self.add("api", endpoint, **kwargs)
    def add_grafana(self, endpoint: str, **kwargs): return self.add("grafana", endpoint, **kwargs)
    def add_prometheus(self, endpoint: str, **kwargs): return self.add("prometheus", endpoint, **kwargs)
    def add_loki(self, endpoint: str, **kwargs): return self.add("loki", endpoint, **kwargs)
    def add_tempo(self, endpoint: str, **kwargs): return self.add("tempo", endpoint, **kwargs)
    def add_faro(self, url: str, app: str, **kwargs): return self.add("faro", url, app, **kwargs)
    def add_otlp(self, endpoint: str, **kwargs): return self.add("otlp", endpoint, **kwargs)
    def add_lgtm_stack(self, base_url: str, service_name: str, **kwargs):
        self.resources.extend(create_lgtm_stack(base_url, service_name, **kwargs))
        return self
    
    def get_all(self) -> List[ExternalRef]: return self.resources
    def get_by_category(self, category: ResourceCategory) -> List[ExternalRef]:
        cat = category.value if isinstance(category, ResourceCategory) else category
        return [r for r in self.resources if r.qos_metrics and r.qos_metrics.get("category") == cat]
    def get_observability_resources(self) -> List[ExternalRef]:
        return [r for r in self.resources if r.qos_metrics and r.qos_metrics.get("category") == "observability"]
    def get_invalid(self) -> List[ExternalRef]:
        return [r for r in self.resources if r.status == "invalid"]
    def validate(self) -> Dict[str, Any]:
        invalid = self.get_invalid()
        return {
            "valid": len(invalid) == 0, "total": len(self.resources),
            "verified": len([r for r in self.resources if r.status == "verified"]),
            "pending": len([r for r in self.resources if r.status == "pending"]),
            "invalid": len(invalid), "invalid_resources": [r.uri for r in invalid]
        }
