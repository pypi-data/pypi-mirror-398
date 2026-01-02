# AgentBill Python SDK

OpenTelemetry-based SDK for automatically tracking and billing AI agent usage.

## Installation

### From PyPI (Recommended)
```bash
pip install agentbill-py-sdk
```

### From PyPI (Coming Soon)
```bash
pip install agentbill
```

### From Source
```bash
# Clone your repository and install
git clone https://github.com/yourusername/agentbill-python-sdk.git
cd agentbill-python-sdk
pip install -e .
```

## File Structure

```
agentbill-python/
├── agentbill/
│   ├── __init__.py
│   ├── client.py
│   ├── tracer.py
│   └── types.py
├── examples/
│   ├── openai_basic.py
│   ├── anthropic_basic.py
│   ├── bedrock_basic.py
│   ├── azure_openai_basic.py
│   ├── mistral_basic.py
│   └── google_ai_basic.py
├── tests/
│   ├── test_agentbill.py
│   └── test_tracer.py
├── README.md
├── setup.py
├── pyproject.toml
├── pytest.ini
├── Makefile
├── CHANGELOG.md
├── CONTRIBUTING.md
├── SECURITY.md
└── LICENSE
```

## Quick Start

```python
from agentbill import AgentBill
import openai

# Initialize AgentBill
agentbill = AgentBill.init({
    "api_key": "your-api-key",
    "customer_id": "customer-123",
    "debug": True
})

# Wrap your OpenAI client
client = agentbill.wrap_openai(openai.OpenAI(
    api_key="sk-..."
))

# Use normally - all calls are automatically tracked!
response = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Hello!"}]
)
```

## ⚠️ Critical: Cost Guard Error Handling

When using budget limits (`daily_budget`/`monthly_budget`), the SDK raises exceptions when limits are exceeded. **Do NOT catch and continue with direct AI calls** - the blocking is intentional to prevent overspending!

```python
# ❌ WRONG - This bypasses budget protection!
try:
    response = wrapped_client.chat.completions.create(...)
except Exception as e:
    print("AgentBill failed, continuing anyway...")
    response = unwrapped_client.chat.completions.create(...)  # BUDGET BYPASSED!

# ✅ CORRECT - Respect the block, handle gracefully
try:
    response = wrapped_client.chat.completions.create(...)
except Exception as e:
    if hasattr(e, 'code') and e.code == 'BUDGET_EXCEEDED':
        print("Budget limit reached - please upgrade or wait")
        return None  # Return early, don't bypass!
    raise  # Re-raise other errors
```

## Features

- ✅ Zero-config instrumentation
- ✅ Accurate token & cost tracking
- ✅ Multi-provider support (OpenAI, Anthropic, Bedrock, Azure OpenAI, Mistral, Google AI)
- ✅ Rich metadata capture
- ✅ OpenTelemetry-based
- ✅ Cost Guard budget enforcement (blocks requests BEFORE spending)

## Supported Providers

- **OpenAI** - GPT-4, GPT-5, Embeddings, DALL-E, Whisper, TTS
- **Anthropic** - Claude Sonnet, Claude Opus
- **AWS Bedrock** - Claude, Titan, and other Bedrock models
- **Azure OpenAI** - GPT models via Azure
- **Mistral AI** - Mistral models
- **Google AI** - Gemini Pro, Gemini Flash

## Provider Examples

### OpenAI
```python
from agentbill import AgentBill
import openai

agentbill = AgentBill.init({"api_key": "your-api-key"})
client = agentbill.wrap_openai(openai.OpenAI(api_key="sk-..."))

response = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Hello!"}]
)
```

### Anthropic
```python
from agentbill import AgentBill
import anthropic

agentbill = AgentBill.init({"api_key": "your-api-key"})
client = agentbill.wrap_anthropic(anthropic.Anthropic(api_key="sk-ant-..."))

response = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Hello!"}]
)
```

### AWS Bedrock
```python
from agentbill import AgentBill
import boto3

agentbill = AgentBill.init({"api_key": "your-api-key"})
bedrock = agentbill.wrap_bedrock(boto3.client('bedrock-runtime'))

response = bedrock.invoke_model(
    modelId='anthropic.claude-v2',
    body=json.dumps({
        "prompt": "Hello!",
        "max_tokens_to_sample": 300
    })
)
```

### Azure OpenAI
```python
from agentbill import AgentBill
from openai import AzureOpenAI

agentbill = AgentBill.init({"api_key": "your-api-key"})
client = agentbill.wrap_azure_openai(AzureOpenAI(
    api_key="your-azure-key",
    api_version="2024-02-01",
    azure_endpoint="https://your-resource.openai.azure.com"
))

response = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Hello!"}]
)
```

### Mistral AI
```python
from agentbill import AgentBill
from mistralai import Mistral

agentbill = AgentBill.init({"api_key": "your-api-key"})
client = agentbill.wrap_mistral(Mistral(api_key="your-mistral-key"))

response = client.chat.complete(
    model="mistral-large-latest",
    messages=[{"role": "user", "content": "Hello!"}]
)
```

### Google AI (Gemini)
```python
from agentbill import AgentBill
import google.generativeai as genai

agentbill = AgentBill.init({"api_key": "your-api-key"})
genai.configure(api_key="your-google-key")
model = genai.GenerativeModel('gemini-pro')
wrapped_model = agentbill.wrap_google_ai(model)

response = wrapped_model.generate_content("Hello!")
```

## Configuration

```python
config = {
    "api_key": "your-api-key",        # Required
    "base_url": "https://...",         # Optional
    "customer_id": "customer-123",     # Optional
    "debug": True                       # Optional
}

agentbill = AgentBill.init(config)
```

## Publishing to PyPI

### Prerequisites
1. Create a PyPI account at https://pypi.org/account/register/
2. Generate an API token at https://pypi.org/manage/account/token/
3. Create `~/.pypirc` file with your token:
```ini
[pypi]
username = __token__
password = pypi-YOUR_API_TOKEN_HERE
```

### Publishing Steps
```bash
# Build the package
python setup.py sdist bdist_wheel

# Upload to PyPI
pip install twine
twine upload dist/*
```

## GitHub Repository Setup

1. Create your GitHub repository (e.g., `agentbill-python-sdk`)
2. Push all files (agentbill/, examples/, LICENSE, setup.py, README.md)
3. Tag releases: `git tag v1.0.0 && git push origin v1.0.0`
4. Users can install with: `pip install agentbill-py-sdk`

## License

MIT
