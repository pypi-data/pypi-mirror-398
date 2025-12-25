"""Rate-limited async HTTP client for Plane API.

PERFORMANCE: Uses httpx.AsyncClient for true async I/O.
"""
import httpx
from planecompose.backend.plane import PlaneBackend


class RateLimitedHTTPClient:
    """
    Async HTTP client with rate limiting.
    
    PERFORMANCE: Uses httpx.AsyncClient for non-blocking I/O.
    Connection pooling is handled automatically by AsyncClient.
    """
    
    def __init__(self, api_key: str, base_url: str = "https://api.plane.so"):
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {"X-Api-Key": api_key}
        self._rate_limiter = PlaneBackend._rate_limiter
        self._client: httpx.AsyncClient | None = None
    
    async def _get_client(self) -> httpx.AsyncClient:
        """
        Get or create async client with connection pooling.
        
        PERFORMANCE: Reuses connections instead of creating new ones per request.
        """
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers=self.headers,
                timeout=30.0,
                # Connection pooling
                limits=httpx.Limits(
                    max_keepalive_connections=5,
                    max_connections=10,
                ),
            )
        return self._client
    
    async def close(self):
        """Close the client and release connections."""
        if self._client:
            await self._client.aclose()
            self._client = None
    
    async def get(self, path: str, **kwargs) -> httpx.Response:
        """Make a rate-limited async GET request."""
        await self._rate_limiter.acquire()
        
        client = await self._get_client()
        url = path if path.startswith('http') else path
        
        return await client.get(url, **kwargs)
    
    async def post(self, path: str, **kwargs) -> httpx.Response:
        """Make a rate-limited async POST request."""
        await self._rate_limiter.acquire()
        
        client = await self._get_client()
        return await client.post(path, **kwargs)
    
    async def put(self, path: str, **kwargs) -> httpx.Response:
        """Make a rate-limited async PUT request."""
        await self._rate_limiter.acquire()
        
        client = await self._get_client()
        return await client.put(path, **kwargs)
    
    async def delete(self, path: str, **kwargs) -> httpx.Response:
        """Make a rate-limited async DELETE request."""
        await self._rate_limiter.acquire()
        
        client = await self._get_client()
        return await client.delete(path, **kwargs)
    
    async def patch(self, path: str, **kwargs) -> httpx.Response:
        """Make a rate-limited async PATCH request."""
        await self._rate_limiter.acquire()
        
        client = await self._get_client()
        return await client.patch(path, **kwargs)
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit - close client."""
        await self.close()
