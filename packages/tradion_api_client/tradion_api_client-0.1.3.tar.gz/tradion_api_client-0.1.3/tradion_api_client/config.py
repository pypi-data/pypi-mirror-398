# config.py
"""
Centralized configuration for Tradion API client
"""
import os
from typing import Final

class Config:
    """Configuration constants"""
    
    # API URLs
    BASE_URL: Final[str] = "https://weblive.rmoneyindia.net"
    AUTH_BASE: Final[str] = f"{BASE_URL}/auth/v1/access"
    ORDER_BASE: Final[str] = f"{BASE_URL}/open-api/od/v1"
    WS_URL: Final[str] = "wss://websocket.rmoneyindia.net/NorenWS/"
    
    # Timeouts (seconds)
    HTTP_TIMEOUT: Final[int] = 30
    WS_HEARTBEAT_INTERVAL: Final[int] = 50
    WS_RECONNECT_DELAY: Final[int] = 5
    
    # Retry settings
    MAX_RETRIES: Final[int] = 3
    RETRY_DELAY: Final[int] = 2
    RETRY_BACKOFF: Final[int] = 2
    
    # Rate limiting (1800 requests per 15 minutes for non-order APIs)
    RATE_LIMIT_MAX_REQUESTS: Final[int] = 1800
    RATE_LIMIT_WINDOW_SECONDS: Final[int] = 900  # 15 minutes
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: str = "logs/tradion.log"
    LOG_MAX_BYTES: Final[int] = 10_485_760  # 10 MB
    LOG_BACKUP_COUNT: Final[int] = 5
    
    # API version
    VERSION: Final[str] = "1.0.0.1.4"
    APP_NAME: Final[str] = "RMONEY"
    OS_NAME: Final[str] = "WEBEXTERNAL"
    SOURCE: Final[str] = "WEB"
