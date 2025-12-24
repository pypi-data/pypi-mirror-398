import time
import json
import base64
import logging
import asyncio
from typing import Any, Dict, Optional, Union
from urllib.parse import urlparse, urlencode

# Optional aiohttp import - required for HTTP operations
try:
    import aiohttp
    AIOHTTP_AVAILABLE = True
except ImportError:
    aiohttp = None # type: ignore
    AIOHTTP_AVAILABLE = False

from mcard import MCard
from .infrastructure import RateLimiter, NetworkCache, RetryUtils, RetryConfig

logger = logging.getLogger(__name__)

class HttpClient:
    def __init__(self, rate_limiter: RateLimiter, cache: NetworkCache, security):
        self.rate_limiter = rate_limiter
        self.cache = cache
        self.security = security

    async def request(
        self,
        url: str,
        method: str,
        headers: Dict[str, str],
        body: Optional[Union[str, bytes]] = None,
        config: Dict[str, Any] = {}
    ) -> Dict[str, Any]:
        """
        Execute HTTP request with strict controls (security, rate limit, cache, retry).
        """
        if not AIOHTTP_AVAILABLE:
            raise RuntimeError("aiohttp is required for network operations. Install it with pip install aiohttp[speedups]")

        start_time = time.time()
        
        # 1. Security Check
        self.security.validate_url(url)
        
        # 2. Cache Check (GET only)
        # Note: Cache key generation might need body if varied, though GET usually has no body
        cache_config = config.get("cache")
        cache_key = NetworkCache.generate_key(method, url, str(body) if body else None)
        
        if cache_config and cache_config.get("enabled") and method == "GET":
            cached = self.cache.get(cache_key)
            if cached:
                logger.info(f"[Network] Cache hit for {url}")
                return cached

        # 3. Rate Limiting
        domain = urlparse(url).hostname or ""
        await self.rate_limiter.wait_for(domain)

        # 4. Retry Configuration
        retry_config = config.get("retry", {})
        max_attempts = retry_config.get("max_attempts", 1)
        # Convert backoff string to enum or pass string to infra
        backoff_strategy = retry_config.get("backoff", "exponential") 
        base_delay = retry_config.get("base_delay", 1000)
        max_delay = retry_config.get("max_delay", 30000)
        retry_on = retry_config.get("retry_on")

        last_error: Optional[Exception] = None
        last_status: Optional[int] = None
        retries_attempted = 0
        
        timeout_config = config.get("timeout", 30000)
        timeout_ms = timeout_config.get("total", 30000) if isinstance(timeout_config, dict) else timeout_config
        timeout_sec = timeout_ms / 1000

        for attempt in range(1, max_attempts + 1):
            try:
                ttfb_start = time.time()
                
                async with aiohttp.ClientSession() as session:
                    async with session.request(
                        method=method,
                        url=url,
                        headers=headers,
                        data=body,
                        timeout=aiohttp.ClientTimeout(total=timeout_sec),
                        ssl=config.get("validate_ssl", True),
                    ) as response:
                        ttfb_time = int((time.time() - ttfb_start) * 1000)
                        
                        # Check retry
                        if not response.ok and RetryUtils.should_retry_status(response.status, retry_on):
                            last_status = response.status
                            if attempt < max_attempts:
                                retries_attempted += 1
                                delay = RetryUtils.calculate_backoff_delay(
                                    attempt, backoff_strategy, base_delay, max_delay
                                )
                                logger.info(f"[Network] Retry {attempt}/{max_attempts} for {url} (status: {response.status}, delay: {delay}ms)")
                                await asyncio.sleep(delay / 1000)
                                continue

                        # Process Response
                        response_type = config.get("response_type", "json")
                        
                        if response_type == "json":
                            try:
                                response_body = await response.json()
                            except Exception:
                                response_body = await response.text() # Fallback
                        elif response_type == "text":
                            response_body = await response.text()
                        elif response_type == "binary":
                            raw = await response.read()
                            response_body = base64.b64encode(raw).decode("ascii")
                        else:
                            response_body = await response.text()
                        
                        total_time = int((time.time() - start_time) * 1000)
                        
                        # Calculate mcard_hash if possible
                        mcard_hash: Optional[str] = None
                        try:
                            body_str = (
                                response_body if isinstance(response_body, str)
                                else json.dumps(response_body)
                            )
                            card = MCard(body_str)
                            mcard_hash = card.hash
                        except Exception:
                            pass
                        
                        result = {
                            "success": True,
                            "status": response.status,
                            "headers": dict(response.headers),
                            "body": response_body,
                            "timing": {
                                "dns": 0,
                                "connect": 0,
                                "ttfb": ttfb_time,
                                "total": total_time,
                            },
                            "mcard_hash": mcard_hash
                        }
                        
                        # Cache successful GET
                        if (cache_config and cache_config.get("enabled") and 
                            method == "GET" and response.ok):
                            ttl = cache_config.get("ttl", 300)
                            self.cache.set(cache_key, result, ttl)
                            if cache_config.get("storage") == "mcard":
                                await self.cache.persist(cache_key, result, ttl)
                        
                        return result
            
            except Exception as e:
                last_error = e
                if attempt < max_attempts:
                    retries_attempted += 1
                    delay = RetryUtils.calculate_backoff_delay(
                        attempt, backoff_strategy, base_delay, max_delay
                    )
                    logger.info(f"[Network] Retry {attempt}/{max_attempts} for {url} (error: {e}, delay: {delay}ms)")
                    await asyncio.sleep(delay / 1000)
                    continue

        # Failed after retries
        return {
            "success": False,
            "error": {
                "code": "TIMEOUT" if isinstance(last_error, asyncio.TimeoutError) else "HTTP_ERROR",
                "message": str(last_error) if last_error else "Request failed after retries",
                "status": last_status,
                "retries_attempted": retries_attempted
            }
        }
