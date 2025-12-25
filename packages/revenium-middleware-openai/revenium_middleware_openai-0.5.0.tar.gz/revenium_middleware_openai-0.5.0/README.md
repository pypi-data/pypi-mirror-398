# Revenium Middleware for OpenAI

[![PyPI version](https://img.shields.io/pypi/v/revenium-middleware-openai.svg)](https://pypi.org/project/revenium-middleware-openai/)
[![Python Versions](https://img.shields.io/pypi/pyversions/revenium-middleware-openai.svg)](https://pypi.org/project/revenium-middleware-openai/)
[![Documentation](https://img.shields.io/badge/docs-revenium.io-blue)](https://docs.revenium.io)
[![Website](https://img.shields.io/badge/website-revenium.ai-blue)](https://www.revenium.ai)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Transparent Python middleware for automatic Revenium usage tracking with OpenAI**

A professional-grade Python middleware that seamlessly integrates with OpenAI and Azure OpenAI to provide automatic usage tracking, billing analytics, and comprehensive metadata collection. Features drop-in integration with zero code changes required and supports both Chat Completions and Embeddings APIs.

## Features

- **Seamless Integration** - Drop-in middleware, just import and go
- **Optional Metadata** - Track users, organizations, and business context (all fields optional)
- **Multiple API Support** - Chat Completions and Embeddings
- **Azure OpenAI Support** - Full Azure OpenAI integration with automatic model resolution
- **LangChain Integration** - Native support for LangChain with async detection
- **Streaming Support** - Handles regular and streaming requests seamlessly
- **Fire-and-Forget** - Never blocks your application flow
- **Accurate Pricing** - Automatic model name resolution for precise cost calculation

## Getting Started

**For complete examples and setup instructions, see [`examples/README.md`](https://github.com/revenium/revenium-middleware-openai-python/blob/HEAD/examples/README.md)**

### 1. Create Project Directory

```bash
# Create project directory and navigate to it
mkdir my-openai-project
cd my-openai-project
```

### 2. Create Virtual Environment

```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 3. Install Package

```bash
# Install packages (run after activation)
pip install revenium-middleware-openai

# For LangChain support
pip install revenium-middleware-openai[langchain]
```

### 4. Configure Environment Variables

Create a `.env` file in your project root. See [`.env.example`](https://github.com/revenium/revenium-middleware-openai-python/blob/HEAD/.env.example) for all available configuration options.

**Minimum required configuration:**

```env
REVENIUM_METERING_API_KEY=hak_your_revenium_api_key_here
REVENIUM_METERING_BASE_URL=https://api.revenium.ai
OPENAI_API_KEY=sk_your_openai_api_key_here
```

**NOTE: Replace the placeholder values with your actual API keys.**

### 5. Run Your First Example

Download and run an example from the repository:

```bash
curl -O https://raw.githubusercontent.com/revenium/revenium-middleware-openai-python/main/examples/getting_started.py
python getting_started.py
```

Or use this simple code:

```python
from dotenv import load_dotenv
import openai
import revenium_middleware_openai  # Auto-initializes on import

load_dotenv()  # Load environment variables from .env file
client = openai.OpenAI()
# Your OpenAI API calls here - automatically metered
```

**That's it!** The middleware automatically meters all OpenAI API calls.

**For complete examples and setup instructions, see [`examples/README.md`](https://github.com/revenium/revenium-middleware-openai-python/blob/HEAD/examples/README.md)**

---

## Requirements

- Python 3.8+
- OpenAI Python SDK 1.0.0+
- Works with all OpenAI models and endpoints
- Works with all Azure OpenAI deployments

---

## What Gets Tracked

The middleware automatically captures comprehensive usage data:

### **Usage Metrics**

- **Token Counts** - Input tokens, output tokens, total tokens
- **Model Information** - Model name, provider (OpenAI/Azure), API version
- **Request Timing** - Request duration, response time
- **Cost Calculation** - Estimated costs based on current pricing

### **Business Context (Optional)**

- **User Tracking** - Subscriber ID, email, credentials
- **Organization Data** - Organization ID, subscription ID, product ID
- **Task Classification** - Task type, agent identifier, trace ID
- **Quality Metrics** - Response quality scores, task identifiers

### **Technical Details**

- **API Endpoints** - Chat completions, embeddings
- **Request Types** - Streaming vs non-streaming
- **Error Tracking** - Failed requests, error types
- **Provider Info** - OpenAI vs Azure OpenAI detection

## Metadata Fields

Add business context to track usage by organization, user, task type, or custom fields. Pass a `usage_metadata` dictionary with any of these optional fields:

| Field | Description | Use Case |
|-------|-------------|----------|
| `trace_id` | Unique identifier for session or conversation tracking | Link multiple API calls together for debugging, user session analytics, or distributed tracing across services |
| `task_type` | Type of AI task being performed | Categorize usage by workload (e.g., "chat", "code-generation", "doc-summary") for cost analysis and optimization |
| `subscriber.id` | Unique user identifier | Track individual user consumption for billing, rate limiting, or user analytics |
| `subscriber.email` | User email address | Identify users for support, compliance, or usage reports |
| `subscriber.credential.name` | Authentication credential name | Track which API key or service account made the request |
| `subscriber.credential.value` | Authentication credential value | Associate usage with specific credentials for security auditing |
| `organization_id` | Organization or company identifier | Multi-tenant cost allocation, usage quotas per organization |
| `subscription_id` | Subscription plan identifier | Track usage against subscription limits, identify plan upgrade opportunities |
| `product_id` | Your product or feature identifier | Attribute AI costs to specific features in your application (e.g., "chatbot", "email-assistant") |
| `agent` | AI agent or bot identifier | Distinguish between multiple AI agents or automation workflows in your system |
| `response_quality_score` | Custom quality rating (0.0-1.0) | Track user satisfaction or automated quality metrics for model performance analysis |

### Trace Visualization Fields (v0.4.8+)

Enhanced observability fields for distributed tracing and analytics. These fields help you track, debug, and analyze AI operations across your infrastructure.

#### Field Reference

| Field | Environment Variable | Description | Best Practice |
|-------|---------------------|-------------|---------------|
| `environment` | `REVENIUM_ENVIRONMENT` | Deployment environment (e.g., "production", "staging") | **Use env var** - Static per deployment; auto-detects from `ENVIRONMENT`, `DEPLOYMENT_ENV` |
| `region` | `REVENIUM_REGION` | Cloud region identifier (e.g., "us-east-1", "eastus") | **Use env var** - Static per deployment; auto-detects from `AWS_REGION`, `AZURE_REGION`, `GCP_REGION` |
| `credential_alias` | `REVENIUM_CREDENTIAL_ALIAS` | Human-readable API key name (e.g., "prod-openai-key") | **Use env var** - Identifies which credential is configured |
| `trace_type` | `REVENIUM_TRACE_TYPE` | Workflow category identifier (max 128 chars, alphanumeric/hyphens/underscores) | **Either** - Env var for single-purpose deployments, usage_metadata for multi-purpose |
| `trace_name` | `REVENIUM_TRACE_NAME` | Human-readable trace label (max 256 chars, auto-truncates) | **Either** - Env var for static names, usage_metadata for dynamic names |
| `parent_transaction_id` | `REVENIUM_PARENT_TRANSACTION_ID` | Parent transaction ID for distributed tracing | **Use usage_metadata** - Should be unique per request chain |
| `transaction_name` | `REVENIUM_TRANSACTION_NAME` | Human-friendly operation name | **Either** - Falls back to `task_type` if not set |
| `retry_number` | `REVENIUM_RETRY_NUMBER` | Retry attempt number (0 = first attempt, 1+ = retries) | **Use usage_metadata** - Should change per retry attempt |

**Auto-Detected Fields** (no configuration needed):
- `operation_type` - Automatically detected from API endpoint (CHAT, EMBED, TOOL_CALL, MODERATION)
- `operation_subtype` - Automatically detected from request parameters (e.g., "function_call" for tool use)

#### Usage Examples

**Static Fields (Environment Variables)**

Best for deployment-wide values that don't change per request:

```bash
# .env file
REVENIUM_ENVIRONMENT=production
REVENIUM_REGION=us-east-1
REVENIUM_CREDENTIAL_ALIAS=prod-openai-key
REVENIUM_TRACE_TYPE=customer-support
```

**Dynamic Fields (usage_metadata)**

Best for per-request values that change:

```python
from openai import OpenAI

client = OpenAI()

# Example 1: Retry logic with retry_number
def call_with_retry(prompt: str, max_retries: int = 3):
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                usage_metadata={
                    "retry_number": attempt,  # Track retry attempts
                    "trace_id": "session-123",
                    "task_type": "chat"
                }
            )
            return response
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            print(f"Retry {attempt + 1}/{max_retries} after error: {e}")

# Example 2: Distributed tracing with parent_transaction_id
def parent_operation():
    """Parent operation that spawns child operations."""
    parent_response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "Analyze this document"}],
        usage_metadata={
            "trace_id": "analysis-session-456",
            "transaction_name": "Document Analysis",
            "task_type": "analysis"
        }
    )

    # Get the transaction ID from the parent
    parent_txn_id = parent_response.id

    # Child operations reference the parent
    child_response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "Summarize findings"}],
        usage_metadata={
            "trace_id": "analysis-session-456",
            "parent_transaction_id": parent_txn_id,  # Link to parent
            "transaction_name": "Summarize Results",
            "task_type": "summarization"
        }
    )

    return parent_response, child_response

# Example 3: Dynamic trace names per user session
def handle_user_session(user_id: str, session_id: str, message: str):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": message}],
        usage_metadata={
            "trace_id": session_id,
            "trace_name": f"User {user_id} - Session {session_id}",  # Dynamic per session
            "trace_type": "customer-support",
            "transaction_name": "Chat Response",
            "subscriber": {"id": user_id}
        }
    )
    return response
```

**Combined Approach (Env Vars + usage_metadata)**

Environment variables provide defaults, usage_metadata overrides per request:

```python
# .env file has:
# REVENIUM_ENVIRONMENT=production
# REVENIUM_REGION=us-east-1
# REVENIUM_TRACE_TYPE=customer-support

# Code can override or add to these:
response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Hello"}],
    usage_metadata={
        # These override env vars:
        "trace_type": "premium-support",  # Overrides REVENIUM_TRACE_TYPE
        # These are request-specific:
        "retry_number": 0,
        "trace_id": "session-789",
        "transaction_name": "Premium Chat"
        # environment and region come from env vars
    }
)
```

**Resources:**
- [API Reference](https://revenium.readme.io/reference/meter_ai_completion) - Complete metadata field documentation
- [`.env.example`](https://github.com/revenium/revenium-middleware-openai-python/blob/HEAD/.env.example) - Environment variable configuration examples

## Configuration Options

### Environment Variables

For a complete list of all available environment variables with examples, see [`.env.example`](https://github.com/revenium/revenium-middleware-openai-python/blob/HEAD/.env.example).

**Key variables:**
- `REVENIUM_METERING_API_KEY` - Your Revenium API key (required)
- `REVENIUM_METERING_BASE_URL` - Revenium API endpoint (default: https://api.revenium.ai)
- `OPENAI_API_KEY` - Your OpenAI API key
- `AZURE_OPENAI_ENDPOINT` - Azure OpenAI endpoint (for Azure)
- `REVENIUM_LOG_LEVEL` - Logging level (DEBUG, INFO, WARNING, ERROR)
- `REVENIUM_SELECTIVE_METERING` - Enable selective metering mode (default: false, see [Decorator Support](#decorator-support))

## Examples

The package includes comprehensive examples in the [`examples/`](https://github.com/revenium/revenium-middleware-openai-python/tree/HEAD/examples) directory.

### Getting Started

```bash
python examples/getting_started.py
```

### OpenAI Examples

| Example                  | File                        | Description                      |
| ------------------------ | --------------------------- | -------------------------------- |
| Basic Chat               | `openai_basic.py`           | Simple chat with metadata        |
| Streaming Chat           | `openai_streaming.py`       | Streaming responses              |
| Decorator Support        | `example_decorator.py`      | Automatic metadata injection     |
| Trace Visualization      | `example_tracing.py`        | Distributed tracing & retry tracking |
| Azure Basic              | `azure_basic.py`            | Azure OpenAI integration         |
| Azure Streaming          | `azure_streaming.py`        | Azure streaming                  |
| LangChain Async          | `langchain_async_examples.py` | LangChain with async support   |

**For complete examples and setup instructions, see [`examples/README.md`](https://github.com/revenium/revenium-middleware-openai-python/blob/HEAD/examples/README.md)**

---

## Decorator Support

The middleware provides powerful decorators for automatic metadata injection, eliminating the need to pass `usage_metadata` to every API call.

### `@revenium_metadata`

Automatically injects metadata into all OpenAI API calls within a function:

```python
from revenium_middleware import revenium_metadata
from openai import OpenAI

client = OpenAI()

@revenium_metadata(
    trace_id="session-12345",
    task_type="customer-support",
    organization_id="acme-corp"
)
def handle_customer_query(question: str):
    # All OpenAI calls here automatically include the decorator metadata
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": question}]
    )
    return response.choices[0].message.content
```

### `@revenium_meter()` - Selective Metering

Control which functions are metered by enabling selective metering mode, where only when `@revenium_meter()` is used the calls are metered when `REVENIUM_SELECTIVE_METERING=true`.

**IMPORTANT:** To use selective metering, you **MUST** set the environment variable:

**How it works:**
- **When `REVENIUM_SELECTIVE_METERING=false` (default)**: ALL OpenAI API calls are automatically metered
- **When `REVENIUM_SELECTIVE_METERING=true`**: ONLY calls inside `@revenium_meter()` decorated functions are metered

```bash
# In your .env file or environment
REVENIUM_SELECTIVE_METERING=true
```

**Accepted values for `REVENIUM_SELECTIVE_METERING`:**
- `"true"`, `"1"`, `"yes"`, `"on"` (case-insensitive) → Selective metering enabled
- `"false"`, `"0"`, `"no"`, `"off"`, or unset → All calls metered (default)

**Example:**

```python
from revenium_middleware import revenium_meter, revenium_metadata

# Set in .env file:
# REVENIUM_SELECTIVE_METERING=true

@revenium_meter()
@revenium_metadata(task_type="premium-feature")
def premium_feature(prompt: str):
    # ✅ This WILL be metered (decorated with @revenium_meter)
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

def free_feature(prompt: str):
    # ❌ This will NOT be metered (no @revenium_meter decorator)
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content
```

---

## Provider Detection & Features

### Automatic Provider Detection
The middleware automatically detects whether you're using standard OpenAI or Azure OpenAI:

- **OpenAI**: Detected via `OpenAI()` client
- **Azure OpenAI**: Detected via `AzureOpenAI()` client

### Model Name Resolution (Azure)
For Azure OpenAI, the middleware automatically resolves Azure deployment names to standard OpenAI model names for accurate pricing and tracking.

### Supported Operations
Both providers support:
- Chat completions (streaming and non-streaming)
- Embeddings
- All metadata fields
- Token counting and cost calculation
- Error handling and logging

**Note:** Azure OpenAI examples (`examples/azure_*.py`) require valid Azure OpenAI credentials. Set `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_API_KEY`, and `AZURE_OPENAI_DEPLOYMENT` environment variables to test Azure functionality.

---

## Logging

The middleware logs errors and warnings automatically. Logging is controlled by the upstream `revenium_middleware` package.

---

## Documentation

For detailed documentation, visit [docs.revenium.io](https://docs.revenium.io)

## Contributing

See [CONTRIBUTING.md](https://github.com/revenium/revenium-middleware-openai-python/blob/main/CONTRIBUTING.md)

## Code of Conduct

See [CODE_OF_CONDUCT.md](https://github.com/revenium/revenium-middleware-openai-python/blob/main/CODE_OF_CONDUCT.md)

## Security

See [SECURITY.md](https://github.com/revenium/revenium-middleware-openai-python/blob/main/SECURITY.md)

## License

This project is licensed under the MIT License - see the [LICENSE](https://github.com/revenium/revenium-middleware-openai-python/blob/main/LICENSE) file for details.

## Support

For issues, feature requests, or contributions:

- **Website**: [www.revenium.ai](https://www.revenium.ai)
- **GitHub Repository**: [revenium/revenium-middleware-openai-python](https://github.com/revenium/revenium-middleware-openai-python)
- **Issues**: [Report bugs or request features](https://github.com/revenium/revenium-middleware-openai-python/issues)
- **Documentation**: [docs.revenium.io](https://docs.revenium.io)
- **Email**: support@revenium.io

---

**Built by Revenium**
