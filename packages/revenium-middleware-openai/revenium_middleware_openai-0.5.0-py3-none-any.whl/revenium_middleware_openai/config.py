"""
Configuration constants and settings for Revenium middleware.

This module centralizes all configuration values to eliminate magic numbers
and provide a single source of truth for middleware behavior.
"""

import os
from typing import Set


class Config:
    """Configuration constants for Revenium middleware."""
    
    # Threading and async timeouts
    THREAD_JOIN_TIMEOUT: float = 5.0
    API_REQUEST_TIMEOUT: float = 30.0
    BACKGROUND_THREAD_TIMEOUT: float = 5.0
    
    # Cache settings
    PROVIDER_CACHE_TTL: int = 3600  # 1 hour
    MODEL_CACHE_TTL: int = 3600     # 1 hour
    
    # Logging and security
    MAX_LOG_STRING_LENGTH: int = 100
    MAX_SANITIZATION_DEPTH: int = 3
    
    # Stream processing
    STREAM_CHUNK_BUFFER_SIZE: int = 1000
    STREAM_TIMEOUT: float = 30.0
    
    # Retry and resilience
    MAX_RETRY_ATTEMPTS: int = 3
    RETRY_BACKOFF_FACTOR: float = 1.5
    INITIAL_RETRY_DELAY: float = 0.1
    
    # Azure API settings
    AZURE_API_VERSION_DEFAULT: str = "2024-10-21"
    AZURE_MODEL_RESOLUTION_TIMEOUT: float = 5.0
    
    # Environment variable names
    ENV_OPENAI_API_KEY: str = "OPENAI_API_KEY"
    ENV_AZURE_OPENAI_ENDPOINT: str = "AZURE_OPENAI_ENDPOINT"
    ENV_AZURE_OPENAI_API_KEY: str = "AZURE_OPENAI_API_KEY"
    ENV_REVENIUM_API_KEY: str = "REVENIUM_METERING_API_KEY"
    ENV_LOG_LEVEL: str = "REVENIUM_LOG_LEVEL"

    # Trace visualization environment variables
    ENV_REVENIUM_ENVIRONMENT: str = "REVENIUM_ENVIRONMENT"
    ENV_ENVIRONMENT: str = "ENVIRONMENT"
    ENV_DEPLOYMENT_ENV: str = "DEPLOYMENT_ENV"

    ENV_REVENIUM_REGION: str = "REVENIUM_REGION"
    ENV_AWS_REGION: str = "AWS_REGION"
    ENV_AWS_DEFAULT_REGION: str = "AWS_DEFAULT_REGION"
    ENV_AZURE_REGION: str = "AZURE_REGION"
    ENV_GCP_REGION: str = "GCP_REGION"
    ENV_GOOGLE_CLOUD_REGION: str = "GOOGLE_CLOUD_REGION"

    ENV_REVENIUM_CREDENTIAL_ALIAS: str = "REVENIUM_CREDENTIAL_ALIAS"
    ENV_REVENIUM_TRACE_TYPE: str = "REVENIUM_TRACE_TYPE"
    ENV_REVENIUM_TRACE_NAME: str = "REVENIUM_TRACE_NAME"
    ENV_REVENIUM_PARENT_TRANSACTION_ID: str = (
        "REVENIUM_PARENT_TRANSACTION_ID"
    )
    ENV_REVENIUM_TRANSACTION_NAME: str = "REVENIUM_TRANSACTION_NAME"
    ENV_REVENIUM_RETRY_NUMBER: str = "REVENIUM_RETRY_NUMBER"


class SecurityConfig:
    """Security-related configuration."""
    
    # Sensitive fields that should never be logged
    SENSITIVE_FIELDS: Set[str] = {
        'api_key', 'subscriber_credential', 'subscriber_email', 'messages', 
        'input', 'content', 'prompt', 'text', 'data', 'authorization',
        'x-api-key', 'bearer', 'token', 'password', 'secret', 'key',
        'credential', 'auth', 'private'
    }
    
    # Additional patterns to check for sensitive data
    SENSITIVE_PATTERNS: Set[str] = {
        'sk-', 'pk-', 'Bearer ', 'Basic ', 'Token '
    }


def get_config_value(key: str, default: any = None) -> any:
    """
    Get configuration value from environment or use default.
    
    Args:
        key: Configuration key (environment variable name)
        default: Default value if environment variable not set
        
    Returns:
        Configuration value
    """
    return os.getenv(key, default)


def is_debug_enabled() -> bool:
    """Check if debug logging is enabled."""
    log_level = get_config_value(Config.ENV_LOG_LEVEL, "INFO").upper()
    return log_level == "DEBUG"


def get_timeout_config() -> dict:
    """Get all timeout-related configuration."""
    return {
        'thread_join': Config.THREAD_JOIN_TIMEOUT,
        'api_request': Config.API_REQUEST_TIMEOUT,
        'background_thread': Config.BACKGROUND_THREAD_TIMEOUT,
        'stream': Config.STREAM_TIMEOUT,
        'azure_model_resolution': Config.AZURE_MODEL_RESOLUTION_TIMEOUT
    }
