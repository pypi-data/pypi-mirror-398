# utils/http_client.py
"""
HTTP client with retry logic, rate limiting, and error handling
"""
import aiohttp
import ssl
import asyncio
from typing import Optional, Dict, Any
from tradion_api_client.utils.logger import logger
from tradion_api_client.exceptions import NetworkError, TimeoutError, TradionAPIError
from tradion_api_client.config import Config

class HttpClient:
    """Async HTTP client with automatic retries and error handling"""
    
    def __init__(self, timeout: int = None):
        self.timeout = aiohttp.ClientTimeout(total=timeout or Config.HTTP_TIMEOUT)
        
        # Create SSL context that doesn't verify certificates (for self-signed certs)
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        connector = aiohttp.TCPConnector(ssl=ssl_context, limit=100)
        self.session = aiohttp.ClientSession(connector=connector)
        
        logger.debug("HTTP client initialized")
    
    async def request(
        self,
        method: str,
        url: str,
        json: Optional[Dict] = None,
        headers: Optional[Dict] = None,
        max_retries: int = Config.MAX_RETRIES
    ) -> Dict[str, Any]:
        """
        Make HTTP request with automatic retries
        
        Args:
            method: HTTP method (GET, POST, etc.)
            url: Full URL
            json: JSON payload
            headers: HTTP headers
            max_retries: Maximum number of retry attempts
        
        Returns:
            Response JSON as dictionary
        
        Raises:
            TradionAPIError: If API returns error
            NetworkError: If network request fails
            TimeoutError: If request times out
        """
        last_error = None
        
        for attempt in range(max_retries):
            try:
                logger.debug(f"HTTP {method} {url} (attempt {attempt + 1}/{max_retries})")
                
                async with self.session.request(
                    method,
                    url,
                    json=json,
                    headers=headers,
                    timeout=self.timeout
                ) as resp:
                    # Log response status
                    logger.debug(f"Response status: {resp.status}")
                    
                    # Check HTTP status
                    if resp.status >= 500:
                        raise NetworkError(f"Server error: {resp.status}")
                    
                    if resp.status == 429:
                        raise NetworkError("Rate limit exceeded")
                    
                    # Parse JSON
                    try:
                        data = await resp.json()
                    except Exception as e:
                        logger.error(f"Failed to parse JSON response: {e}")
                        raise NetworkError(f"Invalid JSON response: {e}")
                    
                    # Check API status
                    status = data.get("status", "").lower()
                    
                    if status == "not_ok" or status == "failed":
                        error_code = data.get("errorCode", "UNKNOWN")
                        error_msg = data.get("emsg") or data.get("message") or "Unknown error"
                        logger.error(f"API error: [{error_code}] {error_msg}")
                        raise TradionAPIError(error_code, error_msg)
                    
                    logger.debug(f"Request successful: {data.get('status')}")
                    return data
            
            except asyncio.TimeoutError as e:
                last_error = TimeoutError(f"Request timeout after {self.timeout.total}s")
                logger.warning(f"Timeout on attempt {attempt + 1}: {e}")
            
            except aiohttp.ClientError as e:
                last_error = NetworkError(f"Network error: {e}")
                logger.warning(f"Network error on attempt {attempt + 1}: {e}")
            
            except TradionAPIError:
                # Don't retry API errors (like invalid parameters)
                raise
            
            except Exception as e:
                last_error = NetworkError(f"Unexpected error: {e}")
                logger.error(f"Unexpected error on attempt {attempt + 1}: {e}")
            
            # Wait before retry (exponential backoff)
            if attempt < max_retries - 1:
                delay = Config.RETRY_DELAY * (Config.RETRY_BACKOFF ** attempt)
                logger.info(f"Retrying in {delay}s...")
                await asyncio.sleep(delay)
        
        # All retries failed
        logger.error(f"All {max_retries} attempts failed")
        raise last_error
    
    async def close(self):
        """Close HTTP session"""
        await self.session.close()
        logger.debug("HTTP client closed")