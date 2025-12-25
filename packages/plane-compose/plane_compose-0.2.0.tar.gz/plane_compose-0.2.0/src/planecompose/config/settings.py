"""Application settings and configuration.

Supports environment variables for easy configuration:
- PLANE_API_URL: Override default Plane API URL
- PLANE_RATE_LIMIT_PER_MINUTE: Override rate limit (default: 50)
- PLANE_API_TIMEOUT: Override API timeout (default: 30)
- PLANE_DEBUG: Enable debug logging (default: false)
"""
from pathlib import Path
try:
    from pydantic_settings import BaseSettings, SettingsConfigDict
except ImportError:
    # Fallback for older pydantic versions
    from pydantic import BaseSettings
    SettingsConfigDict = None


class Settings(BaseSettings):
    """
    Global application settings with environment variable support.
    
    All settings can be overridden via environment variables with PLANE_ prefix.
    
    Example:
        >>> settings = Settings()
        >>> print(settings.plane_api_url)
        https://api.plane.so
        
        # Override via environment
        >>> import os
        >>> os.environ['PLANE_API_URL'] = 'https://custom.plane.so'
        >>> settings = Settings()
        >>> print(settings.plane_api_url)
        https://custom.plane.so
    """
    
    # API Configuration
    plane_api_url: str = "https://api.plane.so"
    plane_api_version: str = "v1"
    plane_api_timeout: int = 30  # seconds
    plane_api_retry_attempts: int = 3
    
    # Rate Limiting
    rate_limit_per_minute: int = 50
    rate_limit_per_hour: int = 3000
    
    # Paths
    config_dir: Path = Path.home() / ".config" / "plane-compose"
    credentials_file: Path | None = None  # Computed in __init__
    log_file: Path | None = None  # Computed in __init__
    
    # Feature Flags
    enable_offline_mode: bool = False
    enable_caching: bool = False
    cache_ttl_minutes: int = 5
    
    # Logging
    debug: bool = False
    verbose: bool = False
    log_to_file: bool = False
    
    # UI
    use_rich_output: bool = True
    show_progress_bars: bool = True
    
    if SettingsConfigDict:
        model_config = SettingsConfigDict(
            env_prefix="PLANE_",
            env_file=".env",
            env_file_encoding="utf-8",
            case_sensitive=False,
            extra="ignore",
        )
    else:
        class Config:
            env_prefix = "PLANE_"
            env_file = ".env"
            case_sensitive = False
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Compute dependent paths
        if self.credentials_file is None:
            self.credentials_file = self.config_dir / "credentials"
        
        if self.log_file is None and self.log_to_file:
            self.log_file = self.config_dir / "plane.log"
    
    @property
    def full_api_url(self) -> str:
        """Get full API URL with version."""
        return f"{self.plane_api_url}/api/{self.plane_api_version}"


# Global settings instance
_settings: Settings | None = None


def get_settings() -> Settings:
    """
    Get global settings instance (singleton).
    
    Returns:
        Settings instance
    """
    global _settings
    
    if _settings is None:
        _settings = Settings()
    
    return _settings


def reset_settings():
    """Reset global settings (useful for testing)."""
    global _settings
    _settings = None

