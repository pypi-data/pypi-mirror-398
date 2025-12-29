# Dockerfile Assistant

AI-powered CLI tool that generates production-ready Dockerfiles and .dockerignore files for Python and Node.js projects.

## Features

- **Multi-Provider LLM Support** - OpenAI, Google (Gemini), Anthropic (Claude), and Ollama (local)
- **Automatic Stack Detection** - Detects Python/Node.js, package managers, entry points, and ports
- **Production-Ready Templates** - Multi-stage builds, non-root users, health checks
- **Filesystem MCP Integration** - Optional AI-powered file exploration and generation
- **Interactive CLI** - Chat-based interface with multi-turn conversations

## Installation

```bash
pip install dockerfile-assistant
```

### From Source

```bash
git clone https://github.com/giulianotesta7/dockerfile-assistant.git
cd dockerfile-assistant
pip install -e .
```

## Configuration

Create a `.env` file in your working directory:

```ini
# Required
LLM_PROVIDER=openai # ollama/google/anthropic
MODEL_NAME=gpt-4o-mini

# API Key (based on provider)
OPENAI_API_KEY=sk-...
# GOOGLE_API_KEY=...
# ANTHROPIC_API_KEY=...
# OLLAMA_BASE_URL=http://localhost:11434/v1

# Optional - Enable filesystem access for AI
USE_FS_MCP=false 
# Only if USE_FS_MCP is set on true
PROJECT_PATH=/path/to/your/project
OUTPUT_PATH=/path/to/output 
```

### Supported Providers

| Provider | Model Examples | Required Variable |
|----------|----------------|-------------------|
| `openai` | gpt-4 | `OPENAI_API_KEY` |
| `google` | gemini-pro | `GOOGLE_API_KEY` |
| `anthropic` | claude-sonnet | `ANTHROPIC_API_KEY` |
| `ollama` | llama3.1:8b | `OLLAMA_BASE_URL` |

## Usage

```bash
dockerfile-assistant
```

### Mode Comparison

| Feature | Basic Mode | MCP Mode |
|---------|------------|----------|
| User provides project info | Yes | Optional |
| Auto-detects stack | No | Yes |
| Auto-detects dependencies | No | Yes |
| Reads project files | No | Yes |
| Saves files to disk | No | Yes |
| Required env vars | `LLM_PROVIDER`, `MODEL_NAME`, API key | + `PROJECT_PATH`, `OUTPUT_PATH` |

### Basic Mode

**Required input:** Describe your project to the agent (stack, package manager, port, start command).

If there is missing information, AI will ask you for:
- Stack (Python or Node.js)
- Package manager (pip, poetry, npm, yarn, pnpm)
- Container port
- Start command

Then generates a Dockerfile and .dockerignore.

> **Note:** For Ollama, `llama3.1:8b` was used during development testing. The `OLLAMA_BASE_URL` must include `/v1` (e.g., `http://localhost:11434/v1`).

### MCP Mode (USE_FS_MCP=true)

**Required input:** Just ask `"Generate a Dockerfile for my project"` - the AI explores your project automatically.

When enabled, the AI can:
- Explore your project directory automatically (`PROJECT_PATH`)
- Detect stack from file signatures (package.json, requirements.txt, etc.)
- Find entry points and ports from configuration
- Save generated files directly to `OUTPUT_PATH` (Dockerfile, .dockerignore)

```bash
# Set in .env
USE_FS_MCP=true
PROJECT_PATH=/path/to/your/project
OUTPUT_PATH=/path/to/your/project
```



> **Important:** MCP mode requires a model that supports tool/function calling.

> **Note:** Ollama with small models (< 30B parameters) is not recommended for MCP mode. Small local models may struggle with tool calling and file exploration, leading to unexpected behavior. For MCP mode, use larger models or cloud providers (OpenAI, Google, Anthropic).

> **Security:** The AI cannot read or write `.env` files. Access is blocked for security reasons.

## Generated Dockerfile Features

All generated Dockerfiles include:

- **Multi-stage builds** for optimized image size
- **Non-root user** for security
- **Health checks** for container orchestration
- **Optimized base images** (python:3.12-slim, node:20-alpine)

### Supported Stacks

| Stack | Package Managers |
|-------|------------------|
| Python | pip, poetry |
| Node.js | npm, yarn, pnpm |




## Environment Variables Reference

| Variable | Required | Description |
|----------|----------|-------------|
| `LLM_PROVIDER` | Yes | Provider: openai, google, anthropic, ollama |
| `MODEL_NAME` | Yes | Model identifier for the provider |
| `OPENAI_API_KEY` | If openai | OpenAI API key |
| `GOOGLE_API_KEY` | If google | Google AI API key |
| `ANTHROPIC_API_KEY` | If anthropic | Anthropic API key |
| `OLLAMA_BASE_URL` | If ollama | Ollama server URL |
| `USE_FS_MCP` | No | Enable filesystem MCP (true/false) |
| `PROJECT_PATH` | If MCP | Path to project directory |
| `OUTPUT_PATH` | If MCP | Path for output files |

## Requirements

- Python 3.10+
- Node.js (only if using MCP filesystem features)

## License

MIT License - see [LICENSE](LICENSE) for details.

## Author

Giuliano Testa ([@giulianotesta7](https://github.com/giulianotesta7))

## Acknowledgments

- System prompts were crafted with the assistance of [Claude](https://claude.ai) (Anthropic)
- Built with [Pydantic AI](https://github.com/pydantic/pydantic-ai)
