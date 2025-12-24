"""Observability resource types - Grafana LGTM Stack."""

from .core import ResourceType

# Observability resource type definitions as pure data
RESOURCE_TYPES = {
    "grafana": ResourceType(
        name="grafana",
        category="observability",
        uri_template="grafana://{endpoint}",
        hash_template="grafana:{endpoint}:{org_id}:{dashboard_uid}",
        default_options={"type": "grafana", "org_id": None, "dashboard_uid": None},
        arg_names=["endpoint"]
    ),
    
    "prometheus": ResourceType(
        name="prometheus",
        category="observability",
        uri_template="prometheus://{endpoint}",
        hash_template="prometheus:{endpoint}:{job_name}",
        default_options={"type": "prometheus", "scrape_interval": 15},
        arg_names=["endpoint"]
    ),
    
    "loki": ResourceType(
        name="loki",
        category="observability",
        uri_template="loki://{endpoint}",
        hash_template="loki:{endpoint}:{tenant_id}",
        default_options={"type": "loki", "labels": {}},
        arg_names=["endpoint"]
    ),
    
    "tempo": ResourceType(
        name="tempo",
        category="observability",
        uri_template="tempo://{endpoint}",
        hash_template="tempo:{endpoint}:{service_name}",
        default_options={"type": "tempo", "sampling_rate": 1.0},
        arg_names=["endpoint"]
    ),
    
    "faro": ResourceType(
        name="faro",
        category="observability",
        uri_template="faro://{collector_url}",
        hash_template="faro:{collector_url}:{app_name}:{environment}",
        default_options={
            "type": "faro",
            "environment": "production",
            "features": ["console", "errors", "web_vitals", "sessions"]
        },
        arg_names=["collector_url", "app_name"]
    ),
    
    "otlp": ResourceType(
        name="otlp",
        category="observability",
        uri_template="otlp://{endpoint}",
        hash_template="otlp:{endpoint}:{protocol}:{service_name}",
        default_options={
            "type": "otlp",
            "protocol": "grpc",
            "signals": ["traces", "metrics", "logs"]
        },
        arg_names=["endpoint"]
    ),
}
