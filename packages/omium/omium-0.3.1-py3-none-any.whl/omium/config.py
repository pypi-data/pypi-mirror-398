"""
Configuration management for Omium SDK.
"""

import json
import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger(__name__)

# Default config directory
CONFIG_DIR = Path.home() / ".omium"
CONFIG_FILE = CONFIG_DIR / "config.json"


class OmiumConfig(BaseModel):
    """Omium SDK configuration model."""
    
    api_key: Optional[str] = Field(None, description="API key for authentication")
    api_url: str = Field(
        default="https://api.omium.ai",
        description="Omium API base URL"
    )
    region: str = Field(
        default="us-east-1",
        description="AWS region (us-east-1, us-west-2, eu-west-1, etc.)"
    )
    checkpoint_manager_url: Optional[str] = Field(
        None,
        description="Local checkpoint manager URL (for local development)"
    )
    use_remote_api: bool = Field(
        default=True,
        description="Whether to use remote API (True) or local gRPC (False)"
    )
    timeout: float = Field(
        default=30.0,
        description="Request timeout in seconds"
    )
    retry_attempts: int = Field(
        default=3,
        description="Number of retry attempts for failed requests"
    )
    
    @field_validator("api_key")
    @classmethod
    def validate_api_key(cls, v: Optional[str]) -> Optional[str]:
        """Validate API key format."""
        if v is None:
            return v
        if not v.startswith("omium_"):
            raise ValueError("API key must start with 'omium_'")
        if len(v) < 20:
            raise ValueError("API key appears to be invalid (too short)")
        return v
    
    @field_validator("region")
    @classmethod
    def validate_region(cls, v: str) -> str:
        """Validate region format."""
        # Basic validation - can be expanded
        if not v or len(v) < 3:
            raise ValueError("Region must be at least 3 characters")
        return v.lower()
    
    class Config:
        """Pydantic config."""
        extra = "forbid"
        json_encoders = {
            Path: str,
        }


class ConfigManager:
    """Manages Omium SDK configuration."""
    
    def __init__(self, config_file: Optional[Path] = None):
        """
        Initialize config manager.
        
        Args:
            config_file: Optional path to config file (defaults to ~/.omium/config.json)
        """
        self.config_file = config_file or CONFIG_FILE
        self._config: Optional[OmiumConfig] = None
    
    def load(self) -> OmiumConfig:
        """
        Load configuration from file and environment variables.
        
        Priority:
        1. Environment variables (OMIUM_API_KEY, OMIUM_API_URL, etc.)
        2. Config file (~/.omium/config.json)
        3. Default values
        
        Returns:
            OmiumConfig instance
        """
        # Start with defaults
        config_dict: Dict[str, Any] = {}
        
        # Load from config file if it exists
        if self.config_file.exists():
            try:
                with open(self.config_file, "r") as f:
                    file_config = json.load(f)
                    config_dict.update(file_config)
                logger.debug(f"Loaded config from {self.config_file}")
            except Exception as e:
                logger.warning(f"Failed to load config file {self.config_file}: {e}")
        
        # Override with environment variables
        env_mapping = {
            "OMIUM_API_KEY": "api_key",
            "OMIUM_API_URL": "api_url",
            "OMIUM_REGION": "region",
            "OMIUM_CHECKPOINT_MANAGER_URL": "checkpoint_manager_url",
            "OMIUM_USE_REMOTE_API": "use_remote_api",
            "OMIUM_TIMEOUT": "timeout",
            "OMIUM_RETRY_ATTEMPTS": "retry_attempts",
        }
        
        for env_var, config_key in env_mapping.items():
            env_value = os.getenv(env_var)
            if env_value is not None:
                # Type conversion
                if config_key in ["use_remote_api"]:
                    config_dict[config_key] = env_value.lower() in ("true", "1", "yes")
                elif config_key in ["timeout"]:
                    config_dict[config_key] = float(env_value)
                elif config_key in ["retry_attempts"]:
                    config_dict[config_key] = int(env_value)
                else:
                    config_dict[config_key] = env_value
        
        # Create config object
        try:
            self._config = OmiumConfig(**config_dict)
        except Exception as e:
            logger.error(f"Invalid configuration: {e}")
            # Return default config on error
            self._config = OmiumConfig()
        
        return self._config
    
    def save(self, config: Optional[OmiumConfig] = None) -> None:
        """
        Save configuration to file.
        
        Args:
            config: Optional config to save (uses current config if not provided)
        """
        if config is None:
            config = self._config or self.load()
        
        # Create config directory if it doesn't exist
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Prepare config dict (exclude None values for optional fields)
        config_dict = config.model_dump(exclude_none=True)
        
        # Don't save API key to file if it's set (security)
        # User should use environment variable instead
        if "api_key" in config_dict:
            logger.warning(
                "API key found in config. Consider using OMIUM_API_KEY environment variable instead."
            )
        
        try:
            with open(self.config_file, "w") as f:
                json.dump(config_dict, f, indent=2)
            logger.info(f"Saved config to {self.config_file}")
        except Exception as e:
            logger.error(f"Failed to save config to {self.config_file}: {e}")
            raise
    
    def get(self) -> OmiumConfig:
        """Get current configuration (loads if not already loaded)."""
        if self._config is None:
            self._config = self.load()
        return self._config
    
    def update(self, **kwargs) -> OmiumConfig:
        """
        Update configuration values.
        
        Args:
            **kwargs: Configuration values to update
            
        Returns:
            Updated OmiumConfig
        """
        current = self.get()
        updated_dict = current.model_dump()
        updated_dict.update(kwargs)
        self._config = OmiumConfig(**updated_dict)
        return self._config
    
    def validate_api_key(self, api_key: str) -> bool:
        """
        Validate API key format.
        
        Args:
            api_key: API key to validate
            
        Returns:
            True if format is valid
        """
        try:
            OmiumConfig(api_key=api_key)
            return True
        except Exception:
            return False


# Global config manager instance
_config_manager: Optional[ConfigManager] = None


def get_config_manager() -> ConfigManager:
    """Get or create global config manager instance."""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager


def get_config() -> OmiumConfig:
    """Get current configuration."""
    return get_config_manager().get()

