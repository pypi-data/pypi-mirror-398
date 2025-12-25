# Cascade SDK

Agent observability platform for tracking AI agent execution, LLM calls, and tool usage.

## Quick Start

### Install from PyPI

```bash
pip install cascade-sdk
```

### Setup

1. **Set your API key** (get one from [Cascade Dashboard](https://cascade-dashboard.vercel.app)):
   ```bash
   export CASCADE_API_KEY="your-api-key"
   ```

2. **Use in your code**:
   ```python
   from cascade import init_tracing, trace_run, wrap_llm_client, tool
   from anthropic import Anthropic
   import os

   # Initialize tracing (uses cloud endpoint by default)
   init_tracing(project="my_project")

   # Wrap LLM client
   client = wrap_llm_client(Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY")))

   # Decorate tools
   @tool
   def my_tool(query: str, client) -> str:
       """My custom tool."""
       response = client.messages.create(
           model="claude-3-haiku-20240307",
           max_tokens=100,
           messages=[{"role": "user", "content": query}]
       )
       return response.content[0].text

   # Trace agent execution
   with trace_run("MyAgent", metadata={"task": "example"}):
       result = my_tool("What is AI?", client)
       print(result)
   ```

3. **View traces** in the [Cascade Dashboard](https://cascade-dashboard.vercel.app)

## Features

- ✅ **Zero setup** - No backend services to run
- ✅ **Cloud-first** - Traces automatically sent to cloud
- ✅ **LLM tracking** - Automatic tracking of LLM calls (Anthropic, OpenAI, etc.)
- ✅ **Tool tracing** - Decorate functions with `@tool` for automatic tracing
- ✅ **Rich metadata** - Add custom metadata to traces
- ✅ **OpenTelemetry** - Built on OpenTelemetry standards

## Configuration

### Environment Variables

- `CASCADE_API_KEY` - Your Cascade API key (required)
- `CASCADE_ENDPOINT` - Override default endpoint (default: `https://api.runcascade.com/v1/traces`)

### Custom Endpoint

If you need to use a custom endpoint:

```python
init_tracing(
    project="my_project",
    endpoint="https://your-custom-endpoint.com/v1/traces",
    api_key="your-api-key"
)
```

## CLI Commands

- `cascade info` - Show setup instructions and information
- `cascade --help` - Show help message
- `cascade --version` - Show version

## Development

This is a monorepo containing:
- `cascade/` - SDK package (published to PyPI)
- `backend/` - Backend service (not included in package)
- `dashboard/` - Frontend dashboard (not included in package)

### Install SDK in Development Mode

```bash
pip install -e .
```

