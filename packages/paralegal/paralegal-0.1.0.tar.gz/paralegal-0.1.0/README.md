# Paralegal - Multi-Tenant LLM Observability

Complete observability for your LLM applications with one line of code.

## Installation

```bash
pip install paralegal
```

## Quick Start

```python
import paralegal
from openai import OpenAI

# Initialize with your API key
paralegal.init(api_key="pl_your_api_key_here")

# Your LLM calls are now automatically traced
client = OpenAI()
response = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Hello!"}]
)
```

## Getting Your API Key

1. Sign up at your customer portal
2. Get your API key
3. Use it in your code or set as environment variable:

```bash
export PARALEGAL_API_KEY="pl_your_api_key"
```

## Supported Providers

- ✅ OpenAI / Azure OpenAI
- ✅ Anthropic (Claude)
- ✅ Google AI (Gemini)
- ✅ AWS Bedrock
- ✅ Cohere
- ✅ HuggingFace
- ✅ LangChain
- ✅ LlamaIndex
- And many more via OpenLLMetry

## Advanced Usage

### Custom App Name

```python
paralegal.init(
    api_key="pl_xxx",
    app_name="my-chatbot-prod"
)
```

### Disable Batching (for testing)

```python
paralegal.init(
    api_key="pl_xxx",
    disable_batch=True
)
```

### Association Properties

```python
paralegal.set_association_properties({
    "user_id": "user_123",
    "session_id": "session_456"
})
```

## Documentation

Built on top of OpenLLMetry and OpenTelemetry for industry-standard observability.

## License

MIT License
