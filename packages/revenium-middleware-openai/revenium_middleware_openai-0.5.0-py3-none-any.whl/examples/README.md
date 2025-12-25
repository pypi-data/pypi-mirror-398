# Revenium OpenAI Middleware - Examples

This guide provides complete, step-by-step instructions for using the Revenium middleware with OpenAI and Azure OpenAI.

## Getting Started - Step by Step

### 1. Create Your Project

```bash
mkdir my-openai-project
cd my-openai-project

# Create virtual environment
python -m venv .venv

# Activate virtual environment
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 2. Install Dependencies

```bash
# Install packages (run after activation)
pip install revenium-middleware-openai

# For LangChain support
pip install revenium-middleware-openai[langchain]
```

### 3. Environment Setup

Create a `.env` file:

```bash
# Revenium Configuration (Required)
REVENIUM_METERING_API_KEY=hak_your_revenium_key_here
REVENIUM_METERING_BASE_URL=https://api.revenium.ai

# OpenAI Configuration (Required for OpenAI)
OPENAI_API_KEY=sk-your_openai_key_here

# Azure OpenAI Configuration (Optional - for Azure OpenAI)
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your_azure_key_here
AZURE_OPENAI_DEPLOYMENT=gpt-4o
AZURE_OPENAI_API_VERSION=2024-12-01-preview

# Trace Visualization (Optional - for distributed tracing)
REVENIUM_ENVIRONMENT=production
REVENIUM_REGION=us-east-1
REVENIUM_CREDENTIAL_ALIAS=openai-prod-key
REVENIUM_TRACE_TYPE=workflow
REVENIUM_TRACE_NAME=My Workflow
REVENIUM_PARENT_TRANSACTION_ID=parent-txn-123
REVENIUM_TRANSACTION_NAME=My Transaction
REVENIUM_RETRY_NUMBER=0
```

Get your Revenium API key: https://app.revenium.ai

### 4. Run Examples

Download and run examples from the repository:

```bash
# Download an example
curl -O https://raw.githubusercontent.com/revenium/revenium-middleware-openai-python/main/examples/getting_started.py

# Run it
python getting_started.py
```

**Available examples to download:**
- `getting_started.py` - Simple entry point with all metadata fields
- `openai_basic.py` - Basic chat and embeddings
- `openai_streaming.py` - Streaming responses
- `example_decorator.py` - Decorator support for automatic metadata injection
- `example_tracing.py` - Trace visualization and distributed tracing
- `azure_basic.py` - Azure OpenAI integration
- `azure_streaming.py` - Azure OpenAI streaming
- `langchain_async_examples.py` - LangChain async integration

## Available Examples

### `getting_started.py` - Simple Entry Point

The simplest example to get you started with Revenium tracking:

**Key Features:**
- Minimal setup - just import and go
- Complete metadata example
- Shows all optional metadata fields
- Single API call demonstration

**Perfect for:** First-time users, quick validation, understanding metadata structure

**Run it:**
```bash
python examples/getting_started.py
```

### `openai_basic.py` - OpenAI Basic Usage

Demonstrates:
- Chat completions with metadata
- Embeddings API tracking
- Optional metadata fields
- Error handling

**Run it:**
```bash
python examples/openai_basic.py
```

### `openai_streaming.py` - OpenAI Streaming

Demonstrates:
- Streaming chat completions
- Real-time response tracking
- Batch embeddings
- Metadata in streaming contexts

**Run it:**
```bash
python examples/openai_streaming.py
```

### `example_decorator.py` - Decorator Support

Demonstrates automatic metadata injection using decorators - the cleanest way to add tracking without cluttering your code:

**Key Features:**
- `@revenium_metadata` - Automatically inject metadata into all OpenAI calls within a function
- `@revenium_meter()` - Enable selective metering (requires `REVENIUM_SELECTIVE_METERING=true`)
- Nested decorators - Inner decorators override outer metadata
- Works with chat, embeddings, and streaming
- Clean separation of business logic and tracking

**⚠️ For Selective Metering:**
To use `@revenium_meter()` for selective metering, set in your `.env` file:
```bash
REVENIUM_SELECTIVE_METERING=true
```
When enabled, ONLY functions decorated with `@revenium_meter()` will be metered.
When disabled (default), ALL OpenAI calls are metered automatically.

**Demonstrates:**
- Single query with automatic metadata
- Batch processing with shared metadata
- Embeddings with metadata
- Combined decorators (`@revenium_meter` + `@revenium_metadata`)
- Nested decorators with metadata inheritance

**Run it:**
```bash
python examples/example_decorator.py
```

**Example:**
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

### `example_tracing.py` - Trace Visualization

Comprehensive guide to trace visualization features for distributed tracing and observability:

**Key Features:**
- Retry tracking with `retry_number`
- Distributed tracing with `parent_transaction_id`
- Dynamic trace names per user session
- Environment and region tracking
- Complete multi-step workflow tracing

**Demonstrates:**
1. **Retry Tracking** - Proper use of `retry_number` to track retry attempts (0 = first attempt, 1+ = retries)
2. **Distributed Tracing** - Linking child operations to parent transactions across services
3. **Dynamic Trace Names** - Per-session/per-user trace identification
4. **Environment/Region** - Static deployment info via env vars vs dynamic overrides
5. **Complete Workflow** - Realistic multi-step scenario combining all features

**Run it:**
```bash
python examples/example_tracing.py
```

**Example - Retry Tracking:**
```python
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
        break
    except Exception as e:
        if attempt == max_retries - 1:
            raise
```

**Example - Distributed Tracing:**
```python
# Parent operation
parent_response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Analyze document"}],
    usage_metadata={
        "trace_id": "analysis-456",
        "transaction_name": "Document Analysis"
    }
)

# Child operation links to parent
child_response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Summarize"}],
    usage_metadata={
        "trace_id": "analysis-456",
        "parent_transaction_id": parent_response.id,  # Link to parent
        "transaction_name": "Summarize Results"
    }
)
```

### `azure_basic.py` - Azure OpenAI Basic

Demonstrates:
- Azure OpenAI chat completions
- Azure OpenAI embeddings
- Automatic model resolution
- Azure-specific configuration

**Run it:**
```bash
python examples/azure_basic.py
```

### `azure_streaming.py` - Azure OpenAI Streaming

Demonstrates:
- Azure OpenAI streaming responses
- Batch embeddings with Azure
- Metadata tracking with Azure

**Run it:**
```bash
python examples/azure_streaming.py
```

### `trace_visualization_example.py` - Trace Visualization

Demonstrates:
- Basic trace visualization with environment variables
- Distributed tracing with parent-child relationships
- Retry tracking for failed operations
- Multi-region deployment tracking
- Custom trace categorization and naming

**Run it:**
```bash
python examples/trace_visualization_example.py
```

### `langchain_async_examples.py` - LangChain Integration

Demonstrates:
- Async LangChain integration
- Automatic async detection
- LangChain-specific patterns
- Callback handler usage

**Run it:**
```bash
python examples/langchain_async_examples.py
```

## Key Features Demonstrated

### Automatic Tracking
- All API calls are automatically tracked to Revenium
- No metadata required - works out of the box
- Provider detection (OpenAI vs Azure) is automatic

### Optional Rich Metadata
- All metadata fields are completely optional
- Add business context for enhanced analytics
- Perfect for enterprise use cases

### Streaming Support
- Real-time streaming responses work seamlessly
- Usage tracked automatically when streams complete
- Metadata flows through streaming calls

### Enterprise Ready
- Azure OpenAI support with compliance features
- Batch processing for efficiency
- Comprehensive business analytics

## Example Metadata Fields

All metadata fields are optional. Use what you need:

```python
usage_metadata={
    # User tracking (nested structure)
    "subscriber": {
        "id": "user-123",
        "email": "user@company.com",
        "credential": {
            "name": "api-key-name",
            "value": "key-identifier"
        }
    },

    # Business context
    "organization_id": "my-company",
    "subscription_id": "sub-premium",
    "product_id": "ai-assistant",

    # Task classification
    "task_type": "chat-completion",
    "trace_id": "session-456",
    "agent": "customer-support",

    # Quality metrics
    "response_quality_score": 0.95
}
```

## Troubleshooting

### Import Errors

**Error:** `ModuleNotFoundError: No module named 'revenium_middleware_openai'`

**Solution:**
```bash
pip install revenium-middleware-openai
```

### API Key Not Found

**Error:** `REVENIUM_METERING_API_KEY environment variable is required`

**Solution:**
Ensure `.env` file exists and is loaded:

```python
from dotenv import load_dotenv
load_dotenv()
```

### Debug Mode

Enable debug logging to see detailed tracking information:

```bash
REVENIUM_DEBUG=true python examples/getting_started.py
```

### No Tracking Data Appearing

1. Verify API key is correct
2. Check network connectivity to api.revenium.ai
3. Enable debug mode to see detailed logs
4. Verify middleware is imported before making API calls

### LangChain Import Errors

**Error:** `ModuleNotFoundError: No module named 'langchain_openai'`

**Solution:**
```bash
pip install revenium-middleware-openai[langchain]
```

### Azure Credentials Note

Azure OpenAI requires proper credentials configuration. See `.env.example` for the required environment variables. The examples use environment variables, but you can also pass credentials directly to the AzureOpenAI client.

## Use Cases

- **Development & Testing** - Track API usage during development
- **Production Monitoring** - Monitor AI costs and usage patterns
- **Enterprise Analytics** - Rich business intelligence with metadata
- **Cost Management** - Detailed cost tracking per user/product/team
- **Compliance** - Azure OpenAI with enterprise security features

## Next Steps

- **Main Documentation**: [README.md](../README.md)
- **API Reference**: [revenium.readme.io](https://revenium.readme.io/reference/meter_ai_completion)
- **Revenium Dashboard**: [app.revenium.ai](https://app.revenium.ai)
- **Documentation**: [docs.revenium.io](https://docs.revenium.io)
- **Support**: support@revenium.io
