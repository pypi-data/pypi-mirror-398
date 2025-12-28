from typing import Any, Dict

from pydantic import Field

from tair_openapi_mcp_server.utils.server import mcp
from tair_openapi_mcp_server.utils.openapi_client import OpenAPIClientManager
from alibabacloud_r_kvstore20150101 import models as r_kvstore_models

SPECIAL_CHARS = "!@#$%^&*()_+-="


@mcp.tool()
async def reset_account_password(
    instance_id: str = Field(description="Instance ID (e.g., 'r-bp1zxszhcgatnx****')"),
    account_name: str = Field(description="Account name to reset password for"),
    account_password: str = Field(
        description="New password (8-32 chars). Must contain at least 3 of: "
                    "uppercase, lowercase, digits, special chars (!@#$%^&*()_+-=)"
    ),
    region_id: str = Field(default="cn-hangzhou", description="Region ID"),
) -> Dict[str, Any]:
    """Reset the password for a Tair account.

    Password requirements:
    - Length: 8-32 characters
    - Complexity: Must contain at least 3 of the following 4 types:
      uppercase letters, lowercase letters, digits, special characters

    Returns:
        Dict with RequestId field on success.
    """
    # Validate password length
    if not 8 <= len(account_password) <= 32:
        return {"error": "Password must be 8-32 characters long"}

    # Validate password complexity (at least 3 of 4 character types)
    checks = [
        any(c.isupper() for c in account_password),
        any(c.islower() for c in account_password),
        any(c.isdigit() for c in account_password),
        any(c in SPECIAL_CHARS for c in account_password),
    ]
    if sum(checks) < 3:
        return {
            "error": "Password must contain at least 3 of: "
                     "uppercase, lowercase, digits, special chars"
        }

    try:
        client = OpenAPIClientManager.get_client(region_id=region_id)
        req = r_kvstore_models.ResetAccountPasswordRequest(
            instance_id=instance_id,
            account_name=account_name,
            account_password=account_password,
        )
        return client.reset_account_password(req).body.to_map()
    except Exception as e:
        return {"error": str(e)}
