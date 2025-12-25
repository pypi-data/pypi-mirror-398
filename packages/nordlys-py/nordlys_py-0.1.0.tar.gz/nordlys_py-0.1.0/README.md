# Nordlys Python SDK

OpenAI-compatible Python client for Nordlys models with intelligent model selection and registry functionality.

## Installation

```bash
uv add nordlys-py
```

```bash
poetry add nordlys-py
```

```bash
pip install nordlys-py
```

## Authentication

Set your API key in the environment:

```bash
export NORDLYS_API_KEY="your-api-key"
```

## Quick Start

### Synchronous Usage

```python
from nordlys_py import Nordlys

nordlys = Nordlys()

response = nordlys.chat.completions.create(
    model="nordlys/nordlys-code",
    messages=[{"role": "user", "content": "Hello from Nordlys"}],
)
```

### Asynchronous Usage

```python
import asyncio
from nordlys_py import AsyncNordlys

async def main():
    nordlys = AsyncNordlys()
    response = await nordlys.chat.completions.create(
        model="nordlys/nordlys-code",
        messages=[{"role": "user", "content": "Hello from Nordlys"}],
    )
    await nordlys.aclose()

asyncio.run(main())
```

## OpenAI Compatibility

The Nordlys SDK is a drop-in replacement for the OpenAI SDK. All OpenAI methods and parameters are supported.

### Chat Completions

```python
from nordlys_py import Nordlys

nordlys = Nordlys()

response = nordlys.chat.completions.create(
    model="nordlys/nordlys-code",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Explain quantum computing in simple terms."}
    ],
    temperature=0.7,
    max_tokens=500,
    stream=False
)

print(response.choices[0].message.content)
```

### Text Completions

```python
from nordlys_py import Nordlys

nordlys = Nordlys()

response = nordlys.completions.create(
    model="nordlys/nordlys-code",
    prompt="The future of AI is",
    temperature=0.8,
    max_tokens=100
)

print(response.choices[0].text)
```

### Migration from OpenAI SDK

Replace your OpenAI imports with Nordlys:

```python
# Before
from openai import OpenAI
client = OpenAI(api_key="your-key")

# After
from nordlys_py import Nordlys
client = Nordlys(api_key="your-key")
```

## Registry API

Discover available models and providers through Nordlys' intelligent registry.

### List All Models

```python
from nordlys_py import Nordlys

nordlys = Nordlys()
models = nordlys.registry.models()

for model in models:
    print(f"Model: {model.model_name}, Context: {model.context_length}")
```

### Get Model Details

```python
from nordlys_py import Nordlys

nordlys = Nordlys()
model = nordlys.registry.model("nordlys/nordlys-code")

print(f"Model: {model.model_name}")
print(f"Description: {model.description}")
print(f"Context Length: {model.context_length}")
```

### List Providers

```python
from nordlys_py import Nordlys

nordlys = Nordlys()
providers = nordlys.registry.providers()

for provider in providers:
    print(f"Provider: {provider.name}, Models: {provider.model_count}")
```

### Filter Models

```python
from nordlys_py import Nordlys, RegistryModelsQuery

nordlys = Nordlys()

# Find models with specific criteria
query = RegistryModelsQuery(
    provider="anthropic",
    min_context_length=8192,
    max_prompt_cost="0.0001"
)

models = nordlys.registry.models(query)
```

### Filter Providers

```python
from nordlys_py import Nordlys, RegistryProvidersQuery

nordlys = Nordlys()

# Find providers with specific criteria
query = RegistryProvidersQuery(
    tag="openai",
    has_pricing=True
)

providers = nordlys.registry.providers(query)
```

### Asynchronous Registry Usage

```python
import asyncio
from nordlys_py import AsyncNordlys, RegistryModelsQuery

async def main():
    nordlys = AsyncNordlys()

    # Get all models
    models = await nordlys.registry.models()

    # Get specific model
    model = await nordlys.registry.model("nordlys/nordlys-code")

    # Filter models
    query = RegistryModelsQuery(provider="openai")
    filtered_models = await nordlys.registry.models(query)

    await nordlys.aclose()

asyncio.run(main())
```

## Model Selection

Select the optimal model for your prompt using Nordlys' intelligent routing.

### Basic Usage

```python
from nordlys_py import Nordlys, SelectModelRequest

nordlys = Nordlys()
request = SelectModelRequest(prompt="Explain quantum computing simply")
result = nordlys.router.select_model(request)

print(f"Selected model: {result.selected_model}")
```

### Advanced Usage

```python
from nordlys_py import Nordlys, SelectModelRequest

nordlys = Nordlys()

# With cost bias and model constraints
request = SelectModelRequest(
    prompt="Write a Python function",
    cost_bias=0.8,  # Prefer cost-efficient models
    models=["nordlys/nordlys-code", "nordlys/nordlys-fast"],
    semantic_cache_threshold=0.9
)

result = nordlys.router.select_model(request)
print(f"Selected: {result.selected_model}, Cache tier: {result.cache_tier}")
```

### Asynchronous Usage

```python
import asyncio
from nordlys_py import AsyncNordlys, SelectModelRequest

async def main():
    nordlys = AsyncNordlys()
    request = SelectModelRequest(prompt="Analyze this data")
    result = await nordlys.router.select_model(request)
    print(f"Selected model: {result.selected_model}")
    await nordlys.aclose()

asyncio.run(main())
```

## Error Handling

The SDK provides a custom `NordlysError` exception for API-related errors.

```python
from nordlys_py import Nordlys, NordlysError

nordlys = Nordlys()

try:
    response = nordlys.chat.completions.create(
        model="invalid-model",
        messages=[{"role": "user", "content": "Hello"}]
    )
except NordlysError as e:
    print(f"Nordlys Error: {e}")
    print(f"Status Code: {e.status_code}")
    print(f"Payload: {e.payload}")
```

### Error Properties

- `message`: Error description
- `status_code`: HTTP status code (if applicable)
- `payload`: Response payload or error details

## Configuration Options

### API Key

```python
from nordlys_py import Nordlys

# Use environment variable (recommended)
nordlys = Nordlys()

# Or pass directly
nordlys = Nordlys(api_key="your-api-key")
```

### Custom Base URL

```python
from nordlys_py import Nordlys

# Use custom endpoint
nordlys = Nordlys(base_url="https://your-custom-endpoint.com/v1")
```

### Timeout Configuration

```python
from nordlys_py import Nordlys

# Set timeout in seconds
nordlys = Nordlys(timeout=30.0)

# Or use httpx.Timeout for advanced configuration
import httpx
nordlys = Nordlys(timeout=httpx.Timeout(10.0, read=30.0))
```

### Custom HTTP Client

```python
import httpx
from nordlys_py import Nordlys

# Use custom HTTP client
http_client = httpx.Client(proxies="http://proxy.example.com:8080")
nordlys = Nordlys(http_client=http_client)
```

### Additional Headers

```python
from nordlys_py import Nordlys

# Add custom headers
headers = {"X-Custom-Header": "value"}
nordlys = Nordlys(headers=headers)
```

## Resource Management

### Context Managers (Recommended)

```python
from nordlys_py import Nordlys

# Automatic resource cleanup
with Nordlys() as nordlys:
    response = nordlys.chat.completions.create(
        model="nordlys/nordlys-code",
        messages=[{"role": "user", "content": "Hello"}]
    )
```

### Asynchronous Context Managers

```python
import asyncio
from nordlys_py import AsyncNordlys

async def main():
    async with AsyncNordlys() as nordlys:
        response = await nordlys.chat.completions.create(
            model="nordlys/nordlys-code",
            messages=[{"role": "user", "content": "Hello"}]
        )

asyncio.run(main())
```

### Manual Resource Cleanup

```python
from nordlys_py import Nordlys

nordlys = Nordlys()

# Use the client...
response = nordlys.chat.completions.create(
    model="nordlys/nordlys-code",
    messages=[{"role": "user", "content": "Hello"}]
)

# Manually close when done
nordlys.close()
```

For async clients:

```python
import asyncio
from nordlys_py import AsyncNordlys

async def main():
    nordlys = AsyncNordlys()

    # Use the client...
    response = await nordlys.chat.completions.create(
        model="nordlys/nordlys-code",
        messages=[{"role": "user", "content": "Hello"}]
    )

    # Manually close when done
    await nordlys.aclose()

asyncio.run(main())
```

## Development

Format:

```bash
uv run ruff format
```

Lint:

```bash
uv run ruff check .
```

Type check:

```bash
uv run ty check
```

Tests:

```bash
uv run pytest
```

## Versioning

Use `uv version` to bump versions:

```bash
uv version --bump patch
```</content>
<parameter name="filePath">/home/botir-khaltaev/repos/adaptive/nordlys-py/README.md