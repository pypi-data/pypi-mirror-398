# Agent Dev CLI

Agent Dev CLI - A Python package for agent debugging and workflow visualization with VS Code integration.

## Installation

```bash
pip install -e .
```

## Usage

### Option 1: CLI Wrapper (Recommended)

The easiest way to use Agent Dev CLI - **no code changes required**:

```bash
# Run your agent script with agentdev instrumentation
agentdev run my_agent.py

# Specify a custom port
agentdev run workflow.py --port 9000

# Enable verbose output
agentdev run my_agent.py --verbose

# Pass arguments to your script
agentdev run my_agent.py -- --model gpt-4 --temperature 0.7
```

The CLI automatically:
- Intercepts `from_agent_framework()` calls
- Injects agentdev visualization endpoints
- Opens the workflow visualization in VS Code

### Option 2: Programmatic API

If you prefer explicit control, you can integrate agentdev directly:

```python
from agentdev import setup_test_tool
from azure.ai.agentserver.agentframework import from_agent_framework

# Create your agent
agent = build_agent(chat_client)

# Create agent server
agent_server = from_agent_framework(agent)

# Setup workflow visualization
setup_test_tool(agent_server)

# Run the server
await agent_server.run_async()
```

## CLI Commands

### `agentdev run`

Run a Python agent script with agentdev instrumentation.

```
agentdev run [OPTIONS] SCRIPT [ARGS]...

Options:
  -p, --port INTEGER    Agent server port (default: 8088)
  -v, --verbose         Enable verbose output
  --help                Show this message and exit
```

### `agentdev info`

Show agentdev configuration and status information.

```
agentdev info
```

## Features

- **Health Check Endpoint**: Adds a `/agentdev/health` endpoint to your agent server
- **Workflow Visualization**: Starts a visualization server on port 8090 for WorkflowAgent instances
- **Easy Integration**: Simple one-function setup

## Requirements

- Python 3.10+
- agent-framework
- starlette

## License

MIT License


## Test

```bash
curl 'http://localhost:8088/agentdev/v1/responses' \
  -H 'Content-Type: application/json' \
  -d '{"model":"workflow_in-memory_content-review-workflow_5c703d16cb1e4756848ddcc685b16503","input":{"role":"user","text":"test"},"stream":true}'
```
