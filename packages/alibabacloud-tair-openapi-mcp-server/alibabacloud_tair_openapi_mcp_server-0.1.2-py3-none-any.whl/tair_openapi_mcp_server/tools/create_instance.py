from typing import Any, Callable, Dict, Literal

from pydantic import Field

from tair_openapi_mcp_server.utils.server import mcp
from tair_openapi_mcp_server.utils.openapi_client import OpenAPIClientManager
from alibabacloud_r_kvstore20150101 import models as r_kvstore_models

# Valid billing periods for PrePaid instances
VALID_PERIODS = [1, 2, 3, 4, 5, 6, 7, 8, 9, 12, 24, 36, 60]


def _dry_run_and_create(
    region_id: str,
    params: Dict[str, Any],
    create_fn: Callable
) -> Dict[str, Any]:
    """Execute DryRun pre-check, then create instance if passed.

    Args:
        region_id: Region for the API client
        params: Request parameters
        create_fn: Function that takes (client, params) and returns response

    Returns:
        Instance creation response or error dict with stage indicator
    """
    try:
        client = OpenAPIClientManager.get_client(region_id=region_id)

        # DryRun pre-check
        try:
            create_fn(client, {**params, "dry_run": True})
        except Exception as e:
            code = getattr(e, "code", None)
            # DryRunOperation means pre-check passed
            if code != "DryRunOperation":
                return {
                    "error": getattr(e, "message", str(e)),
                    "code": code or "",
                    "stage": "dry_run"
                }

        # Real creation
        return create_fn(client, params).body.to_map()

    except Exception as e:
        return {"error": str(e), "stage": "create"}


@mcp.tool()
async def create_instance(
    region_id: str = Field(description="Region ID (e.g., 'cn-hangzhou')"),
    instance_class: str = Field(
        description="Instance class. Master-slave specs typically don't contain 'proxy', cluster specs typically contain 'proxy'. Use describe_available_resource to query valid options."
    ),
    shard_count: int = Field(
        description="Number of shards. Use 1 for master-slave, 2+ for cluster."
    ),
    zone_id: str = Field(description="Zone ID (e.g., 'cn-hangzhou-b')"),
    vpc_id: str = Field(description="VPC ID (e.g., 'vpc-xxxx')"),
    vswitch_id: str = Field(description="VSwitch ID (e.g., 'vsw-xxxx')"),
    instance_name: str = Field(default="", description="Instance name"),
    password: str = Field(default="", description="Password for the default account"),
    charge_type: Literal["PostPaid", "PrePaid"] = Field(
        default="PostPaid",
        description="Billing type: 'PostPaid' (pay-as-you-go) or 'PrePaid' (subscription)"
    ),
    period: int = Field(
        default=1,
        description="Billing period in months (only for PrePaid)"
    ),
    engine_version: str = Field(default="7.0", description="Engine version"),
) -> Dict[str, Any]:
    """Create a Redis or Tair Classic instance.

    Supported instance types:
    - Redis Open-Source Edition (classic or cloud-native)
    - DRAM-based instance (classic)

    For cloud-native DRAM-based instances, use create_tair_instance instead.

    Instance class naming conventions:
    - Master-Slave (shard_count=1): specs typically don't contain 'proxy'
    - Cluster (shard_count>=2): specs typically contain 'proxy'

    A DryRun pre-check is automatically performed before actual creation.

    Returns:
        A dict containing InstanceId, ConnectionDomain, Port, etc.
    """
    if shard_count <= 0:
        return {"error": "shard_count must be a positive integer"}

    params: Dict[str, Any] = {
        "region_id": region_id,
        "instance_class": instance_class,
        "shard_count": shard_count,
        "zone_id": zone_id,
        "vpc_id": vpc_id,
        "v_switch_id": vswitch_id,
        "node_type": "MASTER_SLAVE",
        "instance_type": "Redis",
        "network_type": "VPC",
        "charge_type": charge_type,
        "engine_version": engine_version or "7.0",
    }

    if instance_name:
        params["instance_name"] = instance_name
    if password:
        params["password"] = password
    if charge_type == "PrePaid":
        params["period"] = period

    def create_fn(client, p):
        return client.create_instance(r_kvstore_models.CreateInstanceRequest(**p))

    return _dry_run_and_create(region_id, params, create_fn)


@mcp.tool()
async def create_tair_instance(
    region_id: str = Field(description="Region ID (e.g., 'cn-hangzhou')"),
    instance_class: str = Field(
        description="Instance class. Master-slave specs don't contain 'proxy', cluster specs contain 'proxy'. Use describe_available_resource to query valid options."
    ),
    zone_id: str = Field(description="Zone ID (e.g., 'cn-hangzhou-h')"),
    vpc_id: str = Field(description="VPC ID (e.g., 'vpc-bp1nme44gek34slfc****')"),
    vswitch_id: str = Field(description="VSwitch ID (e.g., 'vsw-bp1e7clcw529l773d****')"),
    instance_name: str = Field(default="", description="Instance name"),
    password: str = Field(default="", description="Password for the default account"),
    charge_type: Literal["PostPaid", "PrePaid"] = Field(
        default="PrePaid",
        description="Billing type: 'PostPaid' or 'PrePaid' (default)"
    ),
    period: int = Field(
        default=1,
        description="Billing period in months: 1-9, 12, 24, 36, 60 (PrePaid only)"
    ),
    shard_type: Literal["MASTER_SLAVE", "STAND_ALONE"] = Field(
        default="MASTER_SLAVE",
        description="'MASTER_SLAVE' (High Availability with master-slave replication, default) or 'STAND_ALONE' (single node)"
    ),
    shard_count: int = Field(
        default=1,
        description="Data nodes: 1 (standard) or 2-128 (cluster)"
    ),
    engine_version: str = Field(
        default="7.0",
        description="Engine version: '5.0', '6.0', or '7.0'"
    ),
) -> Dict[str, Any]:
    """Create a cloud-native DRAM-based instance.

    A DryRun pre-check is automatically performed before actual creation.

    Instance class naming conventions:
    - Master-Slave (shard_count=1): specs don't contain 'proxy'
    - Cluster (shard_count>=2): specs contain 'proxy'

    For Redis Open-Source Edition or classic DRAM-based instances,
    use create_instance instead.

    Returns:
        A dict containing InstanceId, ConnectionDomain, Port, etc.
    """
    # Validate shard_count
    if not 1 <= shard_count <= 128:
        return {"error": "shard_count must be between 1 and 128"}

    # Validate period for PrePaid
    if charge_type == "PrePaid" and period not in VALID_PERIODS:
        return {"error": f"period must be one of {VALID_PERIODS}"}

    params: Dict[str, Any] = {
        "region_id": region_id,
        "instance_class": instance_class,
        "zone_id": zone_id,
        "vpc_id": vpc_id,
        "v_switch_id": vswitch_id,
        "shard_type": shard_type,
        "shard_count": shard_count,
        "engine_version": engine_version or "7.0",
        "instance_type": "tair_rdb",
        "charge_type": charge_type,
    }

    if instance_name:
        params["instance_name"] = instance_name
    if password:
        params["password"] = password
    if charge_type == "PrePaid":
        params["period"] = period

    def create_fn(client, p):
        return client.create_tair_instance(
            r_kvstore_models.CreateTairInstanceRequest(**p)
        )

    return _dry_run_and_create(region_id, params, create_fn)
