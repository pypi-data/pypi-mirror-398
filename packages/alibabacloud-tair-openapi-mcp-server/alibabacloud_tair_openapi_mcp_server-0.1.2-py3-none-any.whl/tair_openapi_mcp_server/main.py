import logging
from typing import Literal

import click

from tair_openapi_mcp_server.utils.server import mcp
from tair_openapi_mcp_server.utils.logging import configure_logging
from tair_openapi_mcp_server.version import __version__


class TairOpenAPIMCPServer:
    def __init__(self):
        configure_logging()
        self._logger = logging.getLogger(__name__)
        self._logger.info("Starting ApsaraDB Tair OpenAPI MCP Server")

    def run(self, transport: Literal["stdio", "sse"] = "stdio"):
        mcp.run(transport=transport)


@click.command()
@click.version_option(version=__version__, prog_name="tair-openapi-mcp-server")
def cli():
    server = TairOpenAPIMCPServer()
    server.run()


def main():
    server = TairOpenAPIMCPServer()
    server.run()


if __name__ == "__main__":
    main()