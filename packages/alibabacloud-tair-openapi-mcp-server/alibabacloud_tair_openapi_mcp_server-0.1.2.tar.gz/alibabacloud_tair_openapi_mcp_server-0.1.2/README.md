<p align="center">English | <a href="./README_CN.md">中文</a><br></p>

# Alibaba Cloud Tair OpenAPI MCP Server

[![PyPI version](https://badge.fury.io/py/alibabacloud-tair-openapi-mcp-server.svg)](https://pypi.org/project/alibabacloud-tair-openapi-mcp-server/)
[![Python](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)

MCP server for managing Alibaba Cloud R-KVStore (Tair/Redis) via OpenAPI

## Prerequisites
1. Python >=3.12
2. Alibaba Cloud credentials with access to Alibaba Cloud R-KVStore services
3. [Cline](https://github.com/cline/cline) MCP client (recommended) or other MCP-compatible client

## Installation

### Option 1: Install from PyPI
```bash
pip install alibabacloud-tair-openapi-mcp-server
```

### Option 2: Install from Source with UV
```bash
# Install uv if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone and install
git clone https://github.com/aliyun/alibabacloud-tair-mcp-server.git
cd alibabacloud-tair-mcp-server/tair_openapi_mcp_server
uv venv
source .venv/bin/activate
uv pip install -e .
```

## Quick Start

### Setup with Cline (Recommended)

1. **Install the server** (using PyPI or UV as shown above)

2. **Configure Cline** by adding this to your Cline configuration:

```json
{
  "mcpServers": {
    "tair-openapi": {
      "command": "tair-openapi-mcp-server",
      "args": [],
      "env": {
        "ALIBABA_CLOUD_ACCESS_KEY_ID": "your-access-key-id",
        "ALIBABA_CLOUD_ACCESS_KEY_SECRET": "your-access-key-secret"
      }
    }
  }
}
```

Replace the credentials with your actual Alibaba Cloud access keys.

## Available OpenAPI MCP Tools

### Resources
* `describe_regions`: List all available regions for Alibaba Cloud Tair instances
* `describe_zones`: Query available zones in a region for Tair instances
* `describe_available_resource`: Query available instance specifications in a specific zone
* `describe_vpcs`: Query VPC (Virtual Private Cloud) list in a region
* `describe_vswitches`: Query VSwitch (Virtual Switch) list in a region

### Instance Creation
* `create_instance`: Create a Redis Open-Source Edition or classic DRAM-based instance
* `create_tair_instance`: Create a cloud-native DRAM-based instance

### Account Management
* `describe_accounts`: Query account information for a Tair instance
* `reset_account_password`: Reset the password for a Tair account with security validation

### IP Whitelist
* `describe_security_ips`: Query IP whitelist configuration for a Tair instance
* `modify_security_ips`: Modify IP whitelist for a Tair instance

## Configuration Options

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `ALIBABA_CLOUD_ACCESS_KEY_ID` | Alibaba Cloud Access Key ID | - | Yes |
| `ALIBABA_CLOUD_ACCESS_KEY_SECRET` | Alibaba Cloud Access Key Secret | - | Yes |
| `TAIR_MCP_LOG_LEVEL` | Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL) | `INFO` | No |
| `TAIR_MCP_LOG_FILE` | Optional log file path | - | No |

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Support

- **Documentation**: [Alibaba Cloud Tair Documentation](https://www.alibabacloud.com/help/en/redis)
- **Issues**: Report issues on [GitHub](https://github.com/aliyun/alibabacloud-tair-mcp-server/issues)
- **MCP Protocol**: [Model Context Protocol](https://modelcontextprotocol.io)

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](../LICENSE) file for details.
