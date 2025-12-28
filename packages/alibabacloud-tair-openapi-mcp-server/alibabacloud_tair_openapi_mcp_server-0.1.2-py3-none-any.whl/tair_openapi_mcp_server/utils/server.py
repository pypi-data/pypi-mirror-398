import importlib
import pkgutil
from mcp.server.fastmcp import FastMCP


def load_tools():
    import tair_openapi_mcp_server.tools as tools_pkg

    for _, module_name, _ in pkgutil.iter_modules(tools_pkg.__path__):
        importlib.import_module(
            f"tair_openapi_mcp_server.tools.{module_name}"
        )


mcp = FastMCP("Tair Openapi MCP Server", dependencies=["dotenv"])

# Load tools
load_tools()