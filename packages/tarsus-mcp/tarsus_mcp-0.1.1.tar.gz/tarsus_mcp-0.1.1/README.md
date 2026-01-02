# Tarsus MCP Tools (Python)

Library of MCP-compatible tool definitions for the Tarsus API.

## Installation

```bash
pip install tarsus-mcp
```

## Usage

```python
from tarsus import TarsusClient
from tarsus_mcp import TarsusTools

# Initialize client
client = TarsusClient(api_key="...")

# Get tools
tools_wrapper = TarsusTools(client)
tools = tools_wrapper.get_all_tools()

for tool in tools:
    print(f"Tool: {tool['name']}")
    # tool['callable'] is the executable function
    # tool['inputSchema'] is the JSON schema
```
