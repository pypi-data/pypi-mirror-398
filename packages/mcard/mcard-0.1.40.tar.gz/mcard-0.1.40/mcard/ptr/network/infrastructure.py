import time
import hashlib
import random
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
import json
import asyncio

# Need to import response types from core config or defining locally if not there.
# For now, I'll rely on dictionary interfaces or check where HttpSuccessResponse comes from.
# In original code: from .network_config import HttpSuccessResponse, HttpTiming
# We might need to handle circular imports if network_config is in ptr/core. 
# Best practice: Move network_config to ptr/network or shared location. 
# I will mirror JS behavior and assume loose typing or importing from a shared config later.

@dataclass
class RetryConfig:
    max_attempts: int = 1
    backoff: str = "exponential" # "exponential", "linear", "constant"
    base_delay: int = 1000
    max_delay: int = 30000
    retry_on: Optional[List[int]] = None

class RetryUtils:
    DEFAULT_RETRY_STATUSES = [408, 429, 500, 502, 503, 504]

    @staticmethod
    def calculate_backoff_delay(
        attempt: int,
        strategy: str,
        base_delay: int,
        max_delay: Optional[int] = None
    ) -> int:
        """Calculate delay for retry attempt based on backoff strategy."""
        
        if strategy == "exponential":
            delay = base_delay * (2 ** (attempt - 1))
        elif strategy == "linear":
            delay = base_delay * attempt
        else:  # CONSTANT
            delay = base_delay
        
        # Add jitter (±10%)
        jitter = delay * 0.1 * (random.random() * 2 - 1)
        delay = int(delay + jitter)
        
        if max_delay:
            delay = min(delay, max_delay)
        
        return delay

    @staticmethod
    def should_retry_status(status: int, retry_on: Optional[List[int]] = None) -> bool:
        """Check if HTTP status code should trigger a retry."""
        retry_statuses = retry_on or RetryUtils.DEFAULT_RETRY_STATUSES
        return status in retry_statuses

class NetworkCache:
    def __init__(self, storage_collection=None):
        # Dictionary to hold: key -> (ResponseDict, expires_at_timestamp)
        self._memory_cache: Dict[str, Tuple[Dict[str, Any], float]] = {}
        self.collection = storage_collection

    @staticmethod
    def generate_key(method: str, url: str, body: Optional[str] = None) -> str:
        """Generate cache key from request config."""
        key_data = f"{method}:{url}:{body or ''}"
        return f"cache_{hashlib.md5(key_data.encode()).hexdigest()[:16]}"
    
    def get(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get cached response if valid."""
        cached = self._memory_cache.get(cache_key)
        if cached and cached[1] > time.time():
            response = cached[0]
            # Return copy with cached=True
            return {**response, "cached": True}
        
        # Clean up expired
        if cached:
            del self._memory_cache[cache_key]
        return None

    def set(self, cache_key: str, response: Dict[str, Any], ttl: int) -> None:
        """Cache a response with TTL."""
        expires_at = time.time() + ttl
        self._memory_cache[cache_key] = (response, expires_at)

    async def persist(self, cache_key: str, response: Dict[str, Any], ttl: int) -> None:
        """Store response in MCard collection for persistent caching."""
        if not self.collection:
            return
        
        # Need to import MCard here to avoid circular dep if it was at top level, 
        # but typically models are safe.
        from mcard import MCard 
        
        cache_entry = {
            "key": cache_key,
            "response": response,
            "expires_at": time.time() + ttl,
            "cached_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
        
        card = MCard(json.dumps(cache_entry))
        await asyncio.to_thread(self.collection.add, card)

class RateLimiter:
    DEFAULT_RATE_LIMIT = {"tokens_per_second": 10, "max_burst": 20}

    def __init__(self):
        # domain -> (tokens, last_refill)
        self._buckets: Dict[str, Tuple[float, float]] = {} 

    def check(self, domain: str) -> bool:
        """Token bucket rate limiter. Returns True if request should proceed."""
        now = time.time()
        tokens, last_refill = self._buckets.get(domain, (
            self.DEFAULT_RATE_LIMIT["max_burst"],
            now
        ))
        
        # Refill tokens
        elapsed = now - last_refill
        refill = elapsed * self.DEFAULT_RATE_LIMIT["tokens_per_second"]
        tokens = min(self.DEFAULT_RATE_LIMIT["max_burst"], tokens + refill)
        
        if tokens >= 1:
            tokens -= 1
            self._buckets[domain] = (tokens, now)
            return True
        
        self._buckets[domain] = (tokens, now)
        return False

    async def wait_for(self, domain: str) -> None:
        """Wait until rate limit allows request."""
        while not self.check(domain):
            await asyncio.sleep(0.1)
