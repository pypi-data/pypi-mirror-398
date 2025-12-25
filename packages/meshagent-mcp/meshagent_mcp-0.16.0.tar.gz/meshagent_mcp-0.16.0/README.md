# [Meshagent](https://www.meshagent.com)

## MeshAgent MCP

The ``meshagent.mcp`` package allows you to use any MCP server as a MeshAgent tool. 

### MCPTool
Wrap an MCP tool with ``MCPTool`` so it conforms to the MeshAgent Tool syntax. For more details on how to do this check out the [MeshAgent MCP docs](https://docs.meshagent.com/mcp-overview/overview).

### MCPToolkit
The ``MCPToolkit`` bundles multiple ``MCPTool`` instances into a toolkit that agents can invoke just like built-in MeshAgent tools or custom tools.

```Python Python
import mcp
from meshagent.mcp import MCPToolkit

session = mcp.ClientSession(...)
toolkit = MCPToolkit(
    name="mcp-tools",
    session=session,
    tools=[...]
)
```

---
### Learn more about MeshAgent on our website or check out the docs for additional examples!

**Website**: [www.meshagent.com](https://www.meshagent.com/)

**Documentation**: [docs.meshagent.com](https://docs.meshagent.com/)

---