from typing import Any, Dict, Literal

from pydantic import Field

from tair_openapi_mcp_server.utils.server import mcp
from tair_openapi_mcp_server.utils.openapi_client import OpenAPIClientManager
from alibabacloud_r_kvstore20150101 import models as r_kvstore_models


@mcp.tool()
async def modify_security_ips(
    region_id: str = Field(description="Region ID (e.g., 'cn-hangzhou')"),
    instance_id: str = Field(description="Instance ID (e.g., 'r-bp1xxxxx')"),
    security_ips: str = Field(
        description="IP whitelist entries (comma-separated, max 1000). "
                    "Supports CIDR notation. E.g., '192.168.1.0/24,10.0.0.100'"
    ),
    security_ip_group_name: str = Field(
        default="default",
        description="Name of the IP whitelist group"
    ),
    modify_mode: Literal["Cover", "Append", "Delete"] = Field(
        default="Cover",
        description="Modification mode: 'Cover' (replace), 'Append' (add), 'Delete' (remove)"
    ),
) -> Dict[str, Any]:
    """Modify IP whitelist for a Tair instance.

    Manage IP whitelists for database access control:
    - Cover: Replace the entire whitelist with new IPs
    - Append: Add new IPs to the existing whitelist
    - Delete: Remove specified IPs from the whitelist

    IP Format Examples:
    - Single IP: "192.168.1.1"
    - CIDR block: "10.0.0.0/24"
    - Allow all: "0.0.0.0/0" (not recommended for production)

    Returns:
        Dict with RequestId field on success.
    """
    # Validate IP count
    ip_count = len(security_ips.split(","))
    if ip_count > 1000:
        return {"error": f"Too many IP entries: {ip_count}. Maximum is 1000."}

    try:
        client = OpenAPIClientManager.get_client(region_id=region_id)
        req = r_kvstore_models.ModifySecurityIpsRequest(
            instance_id=instance_id,
            security_ips=security_ips,
            security_ip_group_name=security_ip_group_name,
            modify_mode=modify_mode,
        )
        return client.modify_security_ips(req).body.to_map()
    except Exception as e:
        return {"error": str(e)}
