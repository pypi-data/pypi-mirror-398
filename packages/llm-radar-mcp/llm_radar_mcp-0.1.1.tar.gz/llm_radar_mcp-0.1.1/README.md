<div align="center">

# LLM Radar

### Real-time AI Model Intelligence via MCP

[![MIT License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org)
[![MCP Server](https://img.shields.io/badge/MCP-Server-orange.svg)](https://modelcontextprotocol.io)
[![Updated Daily](https://img.shields.io/badge/data-updated%20daily-brightgreen.svg)](data/)

**Skip the search. Your AI already has current model info.**

[Live Dashboard](https://llm-radar.ajents.company) · [Model Reference](data/MODELS.md) · [MCP Setup](#mcp-server-setup) · [Contributing](CONTRIBUTING.md)

</div>

---

## What is LLM Radar?

LLM Radar is an **MCP server** that gives your AI assistant current information about AI models from OpenAI, Anthropic, and Google.

**The problem:** AI assistants have training cutoffs. Ask about models and you get outdated recommendations, deprecated APIs, or hallucinated pricing.

**The solution:** Connect LLM Radar and your AI already knows what's available today:

- Fetching fresh data from provider APIs **daily**
- Enriching it with Claude for better descriptions
- Exposing it via MCP for any compatible client

---

## MCP Server Setup

### Install via pip

```bash
# Install
pip install llm-radar-mcp

# Or run directly
pip install llm-radar-mcp && llm-radar-mcp
```

**Claude Desktop config** (local stdio):

```json
{
  "mcpServers": {
    "llm-radar": {
      "command": "llm-radar-mcp"
    }
  }
}
```

### Option 3: Docker

```bash
docker run -p 8000:8000 ghcr.io/ajentsor/llm-radar:latest
```

Then connect to `http://localhost:8000/sse`

---

## Available MCP Tools

Once connected, you can use these tools:

| Tool | Description |
|------|-------------|
| `query_models` | Search/filter models by provider, type, or modality support |
| `compare_models` | Side-by-side comparison of specific models |
| `get_model` | Get detailed info about a specific model by API ID |
| `list_model_ids` | List all available model IDs for a provider |

### Example Queries

```
"What models support vision input?"
→ Uses query_models with input_modality="image"

"Compare GPT-4o, Claude Sonnet, and Gemini 2.5 Pro"
→ Uses compare_models with those model IDs

"List all OpenAI model IDs"
→ Uses list_model_ids with provider="openai"
```

---

## Available Resources

The MCP server also exposes resources you can read directly:

| Resource URI | Description |
|--------------|-------------|
| `llm-radar://models/all` | Complete JSON data |
| `llm-radar://models/openai` | OpenAI models only |
| `llm-radar://models/anthropic` | Anthropic models only |
| `llm-radar://models/google` | Google models only |
| `llm-radar://highlights` | Curated recommendations |

---

## How It Works

```
┌─────────────────────────────────────────────────────────────────┐
│                    Daily GitHub Action (8am UTC)                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐                    │
│  │  OpenAI  │   │Anthropic │   │  Google  │   ← Fetch APIs     │
│  │   API    │   │   API    │   │   API    │                    │
│  └────┬─────┘   └────┬─────┘   └────┬─────┘                    │
│       │              │              │                           │
│       └──────────────┼──────────────┘                           │
│                      ▼                                          │
│              ┌──────────────┐                                   │
│              │    Claude    │   ← Enrich & Format               │
│              │   (Sonnet)   │                                   │
│              └──────┬───────┘                                   │
│                     │                                           │
│       ┌─────────────┼─────────────┐                            │
│       ▼             ▼             ▼                            │
│  ┌─────────┐  ┌──────────┐  ┌───────────┐                      │
│  │models.  │  │ MCP      │  │  GitHub   │   ← Deploy           │
│  │  json   │  │ Server   │  │  Pages    │                      │
│  └─────────┘  └──────────┘  └───────────┘                      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Data Format

Each model includes:

| Field | Description |
|-------|-------------|
| `id` | API model identifier |
| `name` | Human-friendly name |
| `provider` | openai, anthropic, or google |
| `description` | What the model is best for |
| `context_window` | Max input tokens |
| `pricing` | Input/output cost per 1M tokens |
| `capabilities` | vision, function_calling, reasoning, etc. |
| `status` | active, preview, or deprecated |
| `released` | Release date |
| `recommended_for` | Use case suggestions |

---

## Local Development

```bash
# Clone
git clone https://github.com/ajentsor/llm-radar.git
cd llm-radar

# Install
python3 -m venv venv
source venv/bin/activate
pip install -e ".[dev]"

# Run MCP server (stdio mode)
llm-radar-mcp

# Run MCP server (HTTP mode for testing)
llm-radar-mcp --http --port 8000

# Fetch fresh data (requires API keys)
cp .env.example .env
# Edit .env with your API keys
python3 -m llm_radar.fetch_models
python3 -m llm_radar.aggregate_with_claude
```

---

## Project Structure

```
llm-radar/
├── src/llm_radar/              # Main package
│   ├── __init__.py
│   ├── mcp_server.py           # MCP server implementation
│   ├── fetch_models.py         # API fetchers
│   └── aggregate_with_claude.py # Claude enrichment
├── data/
│   ├── models.json             # Structured model data
│   ├── MODELS.md               # Human-readable reference
│   └── raw/                    # Raw API responses
├── docs/                       # Landing page (Cloudflare)
├── Dockerfile                  # Container build
├── docker-compose.yml          # Local container setup
├── pyproject.toml              # Python package config
└── .github/workflows/
    └── update-models.yml       # Daily cron job
```

---

## Configuration

To run the data fetcher yourself:

```bash
# .env file
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=AI...
```

For GitHub Actions, add these as repository secrets.

---

## Self-Hosting

### Docker Compose

```yaml
version: '3.8'
services:
  llm-radar:
    image: ghcr.io/ajentsor/llm-radar:latest
    ports:
      - "8000:8000"
    restart: unless-stopped
```

### Cloudflare Workers / Fly.io / Railway

The MCP server supports HTTP/SSE transport, making it deployable to any platform that supports long-running HTTP connections.

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

Key areas for contribution:
- Additional providers (Cohere, Mistral, etc.)
- More MCP tools
- Better data enrichment prompts
- Documentation improvements

---

## License

MIT License - see [LICENSE](LICENSE)

---

<div align="center">

**Built for developers who want accurate AI model info**

[Star this repo](https://github.com/ajentsor/llm-radar) · [Report Issue](https://github.com/ajentsor/llm-radar/issues) · [View Dashboard](https://llm-radar.ajents.company)

</div>
