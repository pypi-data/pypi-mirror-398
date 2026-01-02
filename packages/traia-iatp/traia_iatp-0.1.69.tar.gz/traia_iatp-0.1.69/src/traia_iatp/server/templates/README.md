# A2A Utility Agency Templates

This directory contains Jinja2 templates for generating utility agencies that wrap MCP servers and expose them via the A2A (Agent-to-Agent) protocol.

## Overview

These templates follow the pattern established by the [A2A CrewAI examples](https://github.com/google-a2a/a2a-samples/tree/main/samples/python/agents/crewai) to create standardized A2A servers that:

1. **Wrap MCP Servers**: Connect to any MCP (Model Context Protocol) server
2. **Use CrewAI**: Leverage CrewAI agents to process requests intelligently
3. **Expose A2A Interface**: Provide a standard A2A protocol interface for agent-to-agent communication

## Templates

### Core Templates

- **`agent.py.j2`** - CrewAI agent implementation that wraps the MCP server
- **`agent_executor.py.j2`** - A2A executor that interfaces the CrewAI agent with A2A protocol
- **`__main__.py.j2`** - Main entry point that initializes and starts the A2A server

### Simple Server Template

- **`server.py.j2`** - All-in-one simplified implementation combining agent, executor, and server

### Configuration Templates

- **`agency_config.json.j2`** - Agency configuration file
- **`pyproject.toml.j2`** - Python project dependencies
- **`Dockerfile.j2`** - Docker container configuration
- **`README.md.j2`** - Documentation for the generated agency

## Template Variables

The templates expect the following variables:

### Required Variables
- `agency_name` - Human-readable name of the agency
- `agency_id` - Unique identifier for the agency  
- `mcp_server_name` - Name of the MCP server
- `mcp_server_url` - URL or path to the MCP server
- `mcp_server_description` - Description of the MCP server
- `mcp_server_capabilities` - List of capabilities provided

### Optional Variables
- `agency_description` - Description of the agency (auto-generated if not provided)
- `agency_version` - Version of the agency (default: "0.1.0")
- `mcp_server_type` - Type of MCP server: "stdio", "http", etc. (default: "stdio")
- `expose_individual_tools` - Whether to expose each MCP tool as a separate A2A skill
- `auth_required` - Whether authentication is required
- `auth_schemes` - List of auth schemes if auth is required
- `skill_examples` - Example prompts for the main skill
- `additional_dependencies` - Extra Python dependencies
- `use_simple_server` - Whether to use the simplified server.py template

### Auto-generated Variables
- `class_name` - PascalCase class name derived from agency_name
- `package_name` - Python package name (snake_case)
- `module_name` - Python module name
- `docker_image` - Docker image name

## Usage

Use the `UtilityAgencyTemplateGenerator` class to generate agencies:

```python
from traia_iatp.server.template_generator import UtilityAgencyTemplateGenerator

generator = UtilityAgencyTemplateGenerator()
output_path = generator.generate_agency(
    output_dir="path/to/output",
    agency_name="My MCP Agency",
    agency_id="my-mcp-agency",
    mcp_server_name="my-mcp-server",
    mcp_server_url="http://localhost:3000",
    mcp_server_description="Description of the MCP server",
    mcp_server_capabilities=["capability1", "capability2"],
    use_simple_server=True  # For simpler deployments
)
```

## Generated Structure

### Simple Server (use_simple_server=True)
```
output_dir/
├── server.py            # All-in-one A2A server
├── agency_config.json   # Configuration
├── pyproject.toml       # Dependencies
├── Dockerfile           # Container config
├── README.md           # Documentation
├── docker-compose.yml   # Local development
├── .gitignore          # Git ignore rules
└── .env.example        # Environment variables example
```

### Modular Structure (use_simple_server=False)
```
output_dir/
├── package_name/
│   ├── __init__.py
│   ├── agent.py         # CrewAI agent
│   ├── agent_executor.py # A2A executor
│   └── __main__.py      # Entry point
├── agency_config.json
├── pyproject.toml
├── Dockerfile
├── README.md
├── docker-compose.yml
├── .gitignore
└── .env.example
```

## A2A Protocol Compliance

The generated agencies follow the A2A protocol by:

1. **Agent Card**: Exposing agent capabilities at `/.well-known/agent-card.json`
2. **Task Processing**: Handling tasks via POST to `/tasks/send`
3. **Text I/O**: Supporting text input and output by default
4. **Request Context**: Processing request context and metadata
5. **Error Handling**: Proper error responses in A2A format

## Next Steps

After generating an agency:

1. **Test Locally**: Run with `uv run python -m package_name` or `python server.py`
2. **Build Docker**: `docker build -t agency-name .`
3. **Push to GitHub**: Use the push_agency_to_repo functionality
4. **Deploy to Cloud**: Use cloudrun_deployer for Google Cloud Run
5. **Register**: Add to MongoDB registry for discovery

## References

- [A2A Protocol Documentation](https://github.com/google-a2a/A2A)
- [A2A CrewAI Examples](https://github.com/google-a2a/a2a-samples/tree/main/samples/python/agents/crewai)
- [MCP Protocol](https://github.com/anthropics/model-context-protocol) 