from dataclasses import dataclass
from typing import List, Optional
import os
import re
from urllib.parse import urlparse

@dataclass
class NetworkSecurityConfig:
    allowed_domains: Optional[List[str]] = None
    blocked_domains: Optional[List[str]] = None
    allowed_protocols: Optional[List[str]] = None
    block_private_ips: bool = False
    block_localhost: bool = False
    
class SecurityViolationError(Exception):
    """Raised when a security policy is violated."""
    pass

class NetworkSecurity:
    """
    Enforces network security policies for outbound connections.
    """
    
    def __init__(self, config: Optional[NetworkSecurityConfig] = None):
        self.config = config or self._load_from_env()

    def _load_from_env(self) -> NetworkSecurityConfig:
        """Load security configuration from environment variables."""
        def parse_list(value: Optional[str]) -> Optional[List[str]]:
            if not value:
                return None
            return [s.strip() for s in value.split(",") if s.strip()]
        
        return NetworkSecurityConfig(
            allowed_domains=parse_list(os.environ.get("CLM_ALLOWED_DOMAINS")),
            blocked_domains=parse_list(os.environ.get("CLM_BLOCKED_DOMAINS")),
            allowed_protocols=parse_list(os.environ.get("CLM_ALLOWED_PROTOCOLS")),
            block_private_ips=os.environ.get("CLM_BLOCK_PRIVATE_IPS", "").lower() == "true",
            block_localhost=os.environ.get("CLM_BLOCK_LOCALHOST", "").lower() == "true",
        )

    def validate_url(self, url_string: str) -> None:
        """Validate URL against security policy. Raises SecurityViolationError if blocked."""
        try:
            parsed = urlparse(url_string)
        except Exception:
            raise SecurityViolationError(f"Invalid URL: {url_string}")
        
        hostname = (parsed.hostname or "").lower()
        protocol = parsed.scheme.lower()
        
        # 1. Check blocked domains (takes precedence)
        if self.config.blocked_domains:
            for pattern in self.config.blocked_domains:
                if self._match_domain_pattern(hostname, pattern):
                    raise SecurityViolationError(f"Domain '{hostname}' is blocked by security policy")
        
        # 2. Check allowed domains (if configured)
        if self.config.allowed_domains:
            is_allowed = any(
                self._match_domain_pattern(hostname, pattern)
                for pattern in self.config.allowed_domains
            )
            if not is_allowed:
                raise SecurityViolationError(f"Domain '{hostname}' is not in the allowed list")
        
        # 3. Check allowed protocols
        if self.config.allowed_protocols:
            if protocol not in self.config.allowed_protocols:
                raise SecurityViolationError(
                    f"Protocol '{protocol}' is not allowed. "
                    f"Allowed: {', '.join(self.config.allowed_protocols)}"
                )
        
        # 4. Check localhost blocking
        if self.config.block_localhost:
            if hostname in ("localhost", "127.0.0.1", "::1"):
                raise SecurityViolationError("Localhost access is blocked by security policy")
        
        # 5. Check private IP blocking
        if self.config.block_private_ips:
            if self._is_private_ip(hostname):
                raise SecurityViolationError(f"Private IP '{hostname}' is blocked by security policy")

    def _match_domain_pattern(self, hostname: str, pattern: str) -> bool:
        """Match hostname against domain pattern (supports wildcards)."""
        pattern_lower = pattern.lower()
        
        if pattern_lower.startswith("*."):
            # Wildcard: *.example.com matches sub.example.com
            suffix = pattern_lower[1:]  # .example.com
            return hostname.endswith(suffix) or hostname == pattern_lower[2:]
        
        return hostname == pattern_lower

    def _is_private_ip(self, hostname: str) -> bool:
        """Check if hostname is a private IP address."""
        private_patterns = [
            r"^10\.\d+\.\d+\.\d+$",                    # 10.x.x.x
            r"^192\.168\.\d+\.\d+$",                   # 192.168.x.x
            r"^172\.(1[6-9]|2\d|3[01])\.\d+\.\d+$",   # 172.16-31.x.x
            r"^169\.254\.\d+\.\d+$",                   # Link-local
            r"^fc00:",                                  # IPv6 private
            r"^fd00:",                                  # IPv6 private
        ]
        return any(re.match(p, hostname, re.IGNORECASE) for p in private_patterns)
