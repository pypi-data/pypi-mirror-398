"""Vendor-provisioned SaaS resource types.

Third-party services organized by category:
- Identity/Auth: Google, GitHub, Meta/Facebook
- Messaging: WhatsApp, Line, WeChat, Telegram, Slack
- Collaboration: Trello, Miro, Figma, LinkedIn
"""

from .core import ResourceType

# Vendor/SaaS resource type definitions
RESOURCE_TYPES = {
    # =========================================================================
    # Identity & Authentication Providers
    # =========================================================================
    "google": ResourceType(
        name="google",
        category="vendor",
        uri_template="google://{service}/{resource}",
        hash_template="google:{service}:{resource}:{project_id}",
        default_options={
            "type": "google",
            "service": "oauth",  # oauth, drive, sheets, calendar, etc.
            "auth_env_var": "GOOGLE_CLIENT_ID",
            "required": True
        },
        arg_names=["service", "resource"]
    ),
    
    "github": ResourceType(
        name="github",
        category="vendor",
        uri_template="github://{owner}/{repo}",
        hash_template="github:{owner}:{repo}:{ref}",
        default_options={
            "type": "github",
            "ref": "main",
            "auth_env_var": "GITHUB_TOKEN",
            "required": True
        },
        arg_names=["owner", "repo"]
    ),
    
    "meta": ResourceType(
        name="meta",
        category="vendor",
        uri_template="meta://{app_id}/{service}",
        hash_template="meta:{app_id}:{service}",
        default_options={
            "type": "meta",
            "service": "graph",  # graph, login, messenger, instagram
            "auth_env_var": "META_APP_SECRET",
            "required": True
        },
        arg_names=["app_id", "service"]
    ),
    
    # =========================================================================
    # Messaging Platforms
    # =========================================================================
    "whatsapp": ResourceType(
        name="whatsapp",
        category="vendor",
        uri_template="whatsapp://{phone_number_id}",
        hash_template="whatsapp:{phone_number_id}:{business_id}",
        default_options={
            "type": "whatsapp",
            "api_version": "v18.0",
            "auth_env_var": "WHATSAPP_TOKEN",
            "required": True
        },
        arg_names=["phone_number_id"]
    ),
    
    "telegram": ResourceType(
        name="telegram",
        category="vendor",
        uri_template="telegram://{bot_id}",
        hash_template="telegram:{bot_id}",
        default_options={
            "type": "telegram",
            "auth_env_var": "TELEGRAM_BOT_TOKEN",
            "required": True
        },
        arg_names=["bot_id"]
    ),
    
    "line": ResourceType(
        name="line",
        category="vendor",
        uri_template="line://{channel_id}",
        hash_template="line:{channel_id}",
        default_options={
            "type": "line",
            "auth_env_var": "LINE_CHANNEL_ACCESS_TOKEN",
            "required": True
        },
        arg_names=["channel_id"]
    ),
    
    "wechat": ResourceType(
        name="wechat",
        category="vendor",
        uri_template="wechat://{app_id}",
        hash_template="wechat:{app_id}",
        default_options={
            "type": "wechat",
            "auth_env_var": "WECHAT_APP_SECRET",
            "required": True
        },
        arg_names=["app_id"]
    ),
    
    "slack": ResourceType(
        name="slack",
        category="vendor",
        uri_template="slack://{workspace}/{channel}",
        hash_template="slack:{workspace}:{channel}",
        default_options={
            "type": "slack",
            "auth_env_var": "SLACK_BOT_TOKEN",
            "required": True
        },
        arg_names=["workspace", "channel"]
    ),
    
    # =========================================================================
    # Collaboration & Productivity
    # =========================================================================
    "trello": ResourceType(
        name="trello",
        category="vendor",
        uri_template="trello://{board_id}",
        hash_template="trello:{board_id}",
        default_options={
            "type": "trello",
            "auth_env_var": "TRELLO_API_KEY",
            "required": True
        },
        arg_names=["board_id"]
    ),
    
    "miro": ResourceType(
        name="miro",
        category="vendor",
        uri_template="miro://{board_id}",
        hash_template="miro:{board_id}:{team_id}",
        default_options={
            "type": "miro",
            "auth_env_var": "MIRO_ACCESS_TOKEN",
            "required": True
        },
        arg_names=["board_id"]
    ),
    
    "figma": ResourceType(
        name="figma",
        category="vendor",
        uri_template="figma://{file_key}",
        hash_template="figma:{file_key}:{node_id}",
        default_options={
            "type": "figma",
            "node_id": None,
            "auth_env_var": "FIGMA_ACCESS_TOKEN",
            "required": True
        },
        arg_names=["file_key"]
    ),
    
    "linkedin": ResourceType(
        name="linkedin",
        category="vendor",
        uri_template="linkedin://{organization_id}",
        hash_template="linkedin:{organization_id}",
        default_options={
            "type": "linkedin",
            "auth_env_var": "LINKEDIN_ACCESS_TOKEN",
            "required": True
        },
        arg_names=["organization_id"]
    ),
    
    # =========================================================================
    # Cloud Providers (Infrastructure)
    # =========================================================================
    "aws": ResourceType(
        name="aws",
        category="vendor",
        uri_template="aws://{service}/{resource}",
        hash_template="aws:{service}:{resource}:{region}",
        default_options={
            "type": "aws",
            "region": "us-east-1",
            "auth_env_var": "AWS_ACCESS_KEY_ID",
            "required": True
        },
        arg_names=["service", "resource"]
    ),
    
    "azure": ResourceType(
        name="azure",
        category="vendor",
        uri_template="azure://{subscription}/{resource_group}/{resource}",
        hash_template="azure:{subscription}:{resource_group}:{resource}",
        default_options={
            "type": "azure",
            "auth_env_var": "AZURE_CLIENT_ID",
            "required": True
        },
        arg_names=["subscription", "resource_group", "resource"]
    ),
    
    "gcp": ResourceType(
        name="gcp",
        category="vendor",
        uri_template="gcp://{project}/{service}/{resource}",
        hash_template="gcp:{project}:{service}:{resource}",
        default_options={
            "type": "gcp",
            "auth_env_var": "GOOGLE_APPLICATION_CREDENTIALS",
            "required": True
        },
        arg_names=["project", "service", "resource"]
    ),
}
