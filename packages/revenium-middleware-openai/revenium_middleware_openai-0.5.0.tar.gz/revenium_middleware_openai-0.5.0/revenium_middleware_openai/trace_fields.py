"""
Trace visualization field capture and validation.

This module provides functions to capture trace visualization fields from
environment variables and validate them according to the specification.
"""

import os
import re
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

# Environment variable names
ENV_REVENIUM_ENVIRONMENT = "REVENIUM_ENVIRONMENT"
ENV_ENVIRONMENT = "ENVIRONMENT"
ENV_DEPLOYMENT_ENV = "DEPLOYMENT_ENV"

ENV_REVENIUM_REGION = "REVENIUM_REGION"
ENV_AWS_REGION = "AWS_REGION"
ENV_AWS_DEFAULT_REGION = "AWS_DEFAULT_REGION"
ENV_AZURE_REGION = "AZURE_REGION"
ENV_GCP_REGION = "GCP_REGION"
ENV_GOOGLE_CLOUD_REGION = "GOOGLE_CLOUD_REGION"

ENV_REVENIUM_CREDENTIAL_ALIAS = "REVENIUM_CREDENTIAL_ALIAS"
ENV_REVENIUM_TRACE_TYPE = "REVENIUM_TRACE_TYPE"
ENV_REVENIUM_TRACE_NAME = "REVENIUM_TRACE_NAME"
ENV_REVENIUM_PARENT_TRANSACTION_ID = "REVENIUM_PARENT_TRANSACTION_ID"
ENV_REVENIUM_TRANSACTION_NAME = "REVENIUM_TRANSACTION_NAME"
ENV_REVENIUM_RETRY_NUMBER = "REVENIUM_RETRY_NUMBER"

# Validation constants
TRACE_TYPE_MAX_LENGTH = 128
TRACE_NAME_MAX_LENGTH = 256
TRACE_TYPE_PATTERN = re.compile(r'^[a-zA-Z0-9_-]+$')


def get_environment() -> Optional[str]:
    """
    Get deployment environment from environment variables.
    
    Checks in order:
    1. REVENIUM_ENVIRONMENT
    2. ENVIRONMENT
    3. DEPLOYMENT_ENV
    
    Returns:
        Environment name (e.g., 'production', 'staging') or None
    """
    return (
        os.getenv(ENV_REVENIUM_ENVIRONMENT) or
        os.getenv(ENV_ENVIRONMENT) or
        os.getenv(ENV_DEPLOYMENT_ENV)
    )


def get_region() -> Optional[str]:
    """
    Get cloud region from environment variables.
    
    Checks in order:
    1. REVENIUM_REGION
    2. AWS_REGION or AWS_DEFAULT_REGION
    3. AZURE_REGION
    4. GCP_REGION or GOOGLE_CLOUD_REGION
    
    Returns:
        Region name (e.g., 'us-east-1', 'eastus') or None
    """
    # Try Revenium-specific env var first
    region = os.getenv(ENV_REVENIUM_REGION)
    if region:
        return region
    
    # Try AWS region
    region = os.getenv(ENV_AWS_REGION) or os.getenv(ENV_AWS_DEFAULT_REGION)
    if region:
        return region
    
    # Try Azure region
    region = os.getenv(ENV_AZURE_REGION)
    if region:
        return region
    
    # Try GCP region
    region = os.getenv(ENV_GCP_REGION) or os.getenv(ENV_GOOGLE_CLOUD_REGION)
    if region:
        return region
    
    return None


def get_credential_alias() -> Optional[str]:
    """
    Get credential alias from environment variables.
    
    Returns:
        Credential alias (e.g., 'prod-api-key', 'staging-key') or None
    """
    return os.getenv(ENV_REVENIUM_CREDENTIAL_ALIAS)


def get_trace_type() -> Optional[str]:
    """
    Get and validate trace type from environment variables.
    
    Returns:
        Validated trace type or None if invalid/not set
    """
    trace_type = os.getenv(ENV_REVENIUM_TRACE_TYPE)
    if trace_type:
        return validate_trace_type(trace_type)
    return None


def get_trace_name() -> Optional[str]:
    """
    Get and validate trace name from environment variables.
    
    Returns:
        Validated trace name (truncated if needed) or None if not set
    """
    trace_name = os.getenv(ENV_REVENIUM_TRACE_NAME)
    if trace_name:
        return validate_trace_name(trace_name)
    return None


def get_parent_transaction_id() -> Optional[str]:
    """
    Get parent transaction ID from environment variables.
    
    Returns:
        Parent transaction ID or None
    """
    return os.getenv(ENV_REVENIUM_PARENT_TRANSACTION_ID)


def get_transaction_name(usage_metadata: Optional[Dict[str, Any]] = None) -> Optional[str]:
    """
    Get transaction name with fallback to task_type.

    Checks in order:
    1. REVENIUM_TRANSACTION_NAME env var
    2. transactionName from usage_metadata
    3. task_type from usage_metadata (fallback)

    Args:
        usage_metadata: Optional metadata dictionary

    Returns:
        Transaction name or None
    """
    # First priority: env var
    transaction_name = os.getenv(ENV_REVENIUM_TRANSACTION_NAME)
    if transaction_name:
        return transaction_name

    # Second priority: usage_metadata
    if usage_metadata:
        transaction_name = (
            usage_metadata.get('transactionName') or
            usage_metadata.get('transaction_name')
        )
        if transaction_name:
            return transaction_name

        # Third priority: fallback to task_type
        task_type = (
            usage_metadata.get('task_type') or
            usage_metadata.get('taskType')
        )
        if task_type:
            return task_type

    return None


def get_retry_number() -> int:
    """
    Get retry number from environment variables.

    Returns:
        Retry number (0 for first attempt, 1+ for retries)
    """
    try:
        return int(os.getenv(ENV_REVENIUM_RETRY_NUMBER, '0'))
    except ValueError:
        logger.warning(
            "Invalid REVENIUM_RETRY_NUMBER value, defaulting to 0"
        )
        return 0


def validate_trace_type(trace_type: str) -> Optional[str]:
    """
    Validate trace type format and length.

    Rules:
    - Only alphanumeric characters, hyphens, and underscores
    - Maximum 128 characters

    Args:
        trace_type: Trace type to validate

    Returns:
        Valid trace type or None if invalid
    """
    if not trace_type:
        return None

    # Check length
    if len(trace_type) > TRACE_TYPE_MAX_LENGTH:
        logger.warning(
            f"traceType exceeds maximum length of "
            f"{TRACE_TYPE_MAX_LENGTH} characters: '{trace_type}'. "
            f"Field will be omitted."
        )
        return None

    # Check format
    if not TRACE_TYPE_PATTERN.match(trace_type):
        logger.warning(
            f"traceType contains invalid characters "
            f"(only alphanumeric, hyphens, and underscores allowed): "
            f"'{trace_type}'. Field will be omitted."
        )
        return None

    return trace_type


def validate_trace_name(trace_name: str) -> Optional[str]:
    """
    Validate trace name length and truncate if needed.

    Rules:
    - Maximum 256 characters
    - Truncates with warning if too long

    Args:
        trace_name: Trace name to validate

    Returns:
        Valid trace name (truncated if needed) or None if empty
    """
    if not trace_name:
        return None

    # Check length and truncate if needed
    if len(trace_name) > TRACE_NAME_MAX_LENGTH:
        logger.warning(
            f"traceName exceeds maximum length of "
            f"{TRACE_NAME_MAX_LENGTH} characters. "
            f"Truncating from {len(trace_name)} to "
            f"{TRACE_NAME_MAX_LENGTH} characters."
        )
        return trace_name[:TRACE_NAME_MAX_LENGTH]

    return trace_name


def detect_operation_type(
    provider: str,
    endpoint: str,
    request_body: Optional[Dict[str, Any]] = None
) -> Dict[str, Optional[str]]:
    """
    Auto-detect operation type and subtype from provider, endpoint,
    and request.

    Args:
        provider: Provider name (e.g., 'openai', 'azure_openai') or Provider enum
        endpoint: API endpoint (e.g., '/chat/completions', '/embeddings')
        request_body: Optional request body to check for tools/functions

    Returns:
        Dictionary with 'operationType' and 'operationSubtype' keys
    """
    # Handle Provider enum or string
    if hasattr(provider, 'name'):
        # It's a Provider enum, get the name (e.g., 'OPENAI', 'AZURE_OPENAI')
        provider_str = provider.name
    else:
        provider_str = str(provider)

    provider_lower = provider_str.lower()
    request_body = request_body or {}

    # OpenAI and Azure OpenAI
    if provider_lower in ('openai', 'azure_openai', 'azure'):
        # Chat completions
        is_chat = (
            'chat/completions' in endpoint or
            endpoint.endswith('/chat/completions')
        )
        if is_chat:
            # Check for tools or functions
            has_tools = (
                request_body.get('tools') or
                request_body.get('functions')
            )
            if has_tools:
                return {
                    'operationType': 'TOOL_CALL',
                    'operationSubtype': 'function_call'
                }
            return {
                'operationType': 'CHAT',
                'operationSubtype': None
            }

        # Embeddings
        if 'embeddings' in endpoint or endpoint.endswith('/embeddings'):
            return {
                'operationType': 'EMBED',
                'operationSubtype': None
            }

        # Moderations
        if 'moderations' in endpoint or endpoint.endswith('/moderations'):
            return {
                'operationType': 'MODERATION',
                'operationSubtype': None
            }

    # Default fallback
    return {
        'operationType': 'CHAT',
        'operationSubtype': None
    }
