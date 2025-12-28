from typing import Any, Dict, Literal

from pydantic import Field

from tair_openapi_mcp_server.utils.server import mcp
from tair_openapi_mcp_server.utils.openapi_client import OpenAPIClientManager
from alibabacloud_r_kvstore20150101 import models as r_kvstore_models
from alibabacloud_vpc20160428 import models as vpc_models


@mcp.tool()
async def describe_regions(
    accept_language: Literal["zh-CN", "en-US"] = Field(
        default="zh-CN",
        description="Language for region names: 'zh-CN' (Chinese) or 'en-US' (English)"
    ),
) -> Dict[str, Any]:
    """Query all available regions for Alibaba Cloud Tair instances.

    This is typically the first API to call when planning instance deployment.
    Returns the complete list of regions where Tair instances can be deployed.

    Returns:
        A dict containing regions list and request_id.
    """
    try:
        client = OpenAPIClientManager.get_client(region_id="cn-hangzhou")
        req = r_kvstore_models.DescribeRegionsRequest(accept_language=accept_language)
        return client.describe_regions(req).body.to_map()
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
async def describe_zones(
    region_id: str = Field(description="Region ID (e.g., 'cn-hangzhou')"),
    accept_language: Literal["zh-CN", "en-US"] = Field(
        default="zh-CN",
        description="Language for zone names: 'zh-CN' or 'en-US'"
    ),
) -> Dict[str, Any]:
    """Query available zones in a region for Tair instances.

    Use this to find which zones support Tair instances before creating one.

    Returns:
        A dict containing zones list with their details.
    """
    try:
        client = OpenAPIClientManager.get_client(region_id=region_id)
        req = r_kvstore_models.DescribeZonesRequest(
            region_id=region_id,
            accept_language=accept_language
        )
        return client.describe_zones(req).body.to_map()
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
async def describe_available_resource(
    region_id: str = Field(description="Region ID (e.g., 'cn-hangzhou')"),
    zone_id: str = Field(description="Zone ID (e.g., 'cn-hangzhou-h')"),
    instance_charge_type: Literal["PrePaid", "PostPaid"] = Field(
        default="PrePaid",
        description="Billing type: 'PrePaid' (subscription) or 'PostPaid' (pay-as-you-go)"
    ),
    product_type: Literal["Local", "Tair_rdb", "OnECS"] = Field(
        default="Local",
        description="Product type: 'Local' (classic Redis Open-Source Edition instance or classic DRAM-based instance), 'Tair_rdb' (cloud-native DRAM-based instance), 'OnECS' (cloud-native Redis Open-Source Edition instance). Use 'OnECS' for cloud-native Redis Open-Source Edition instances, 'Tair_rdb' for cloud-native DRAM-based instances."
    ),
    accept_language: Literal["zh-CN", "en-US"] = Field(
        default="zh-CN",
        description="Language for response: 'zh-CN' or 'en-US'"
    ),
) -> Dict[str, Any]:
    """Query available instance specifications in a specific zone.

    Use this to find what instance types and configurations are available
    before creating an instance.

    Product type selection guide (based on instance type and deployment mode):
    - 'Local': classic Redis Open-Source Edition instance or classic DRAM-based instance
    - 'Tair_rdb': cloud-native DRAM-based instance. Use for cloud-native DRAM-based instances.
    - 'OnECS': cloud-native Redis Open-Source Edition instance. Use for cloud-native Redis Open-Source Edition instances.

    Selection rules:
    - For cloud-native Redis Open-Source Edition instances → use 'OnECS'
    - For cloud-native DRAM-based instances → use 'Tair_rdb'
    - For classic instances (Redis Open-Source Edition or DRAM-based) → use 'Local'

    Note: Fixed parameters (not exposed):
      - OrderType: 'BUY' (new purchase)
      - Engine: 'Redis'
      - InstanceScene: 'professional' (standard edition)

    Returns:
        A dict containing available zones with instance specifications.
    """
    try:
        client = OpenAPIClientManager.get_client(region_id=region_id)
        req = r_kvstore_models.DescribeAvailableResourceRequest(
            region_id=region_id,
            zone_id=zone_id,
            instance_charge_type=instance_charge_type,
            order_type="BUY",
            engine="Redis",
            product_type=product_type,
            accept_language=accept_language,
            instance_scene="professional",
        )
        return client.describe_available_resource(req).body.to_map()
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
async def describe_vpcs(
    region_id: str = Field(description="Region ID (e.g., 'cn-hangzhou')"),
    vpc_id: str = Field(
        default="",
        description="VPC ID filter. Multiple IDs can be separated by commas"
    ),
    vpc_name: str = Field(default="", description="VPC name filter"),
    page_number: int = Field(default=1, description="Page number, starting from 1"),
    page_size: int = Field(default=10, description="Number of entries per page (1-50)"),
) -> Dict[str, Any]:
    """Query VPC (Virtual Private Cloud) list in a region.

    VPCs are isolated virtual networks in Alibaba Cloud.
    You need a VPC and VSwitch to create a Tair instance.

    Returns:
        A dict containing Vpcs list, TotalCount, PageNumber, PageSize.
    """
    # Validate pagination parameters
    if not 1 <= page_size <= 50:
        return {"error": "page_size must be between 1 and 50"}
    if page_number < 1:
        return {"error": "page_number must be >= 1"}

    try:
        client = OpenAPIClientManager.get_vpc_client(region_id=region_id)
        request = vpc_models.DescribeVpcsRequest(
            region_id=region_id,
            page_number=page_number,
            page_size=page_size
        )

        # Apply optional filters
        if vpc_id:
            request.vpc_id = vpc_id
        if vpc_name:
            request.vpc_name = vpc_name

        return client.describe_vpcs(request).body.to_map()
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
async def describe_vswitches(
    region_id: str = Field(description="Region ID (e.g., 'cn-hangzhou')"),
    vpc_id: str = Field(default="", description="VPC ID filter"),
    vswitch_id: str = Field(default="", description="VSwitch ID filter"),
    vswitch_name: str = Field(default="", description="VSwitch name filter"),
    zone_id: str = Field(default="", description="Zone ID filter (e.g., 'cn-hangzhou-b')"),
    page_number: int = Field(default=1, description="Page number, starting from 1"),
    page_size: int = Field(default=10, description="Number of entries per page (1-50)"),
) -> Dict[str, Any]:
    """Query VSwitch (Virtual Switch) list in a region.

    VSwitches are subnets within a VPC, associated with specific zones.
    You need a VSwitch in the target zone to create a Tair instance.

    Returns:
        A dict containing VSwitches list, TotalCount, PageNumber, PageSize.
    """
    # Validate pagination parameters
    if not 1 <= page_size <= 50:
        return {"error": "page_size must be between 1 and 50"}
    if page_number < 1:
        return {"error": "page_number must be >= 1"}

    try:
        client = OpenAPIClientManager.get_vpc_client(region_id=region_id)
        request = vpc_models.DescribeVSwitchesRequest(
            region_id=region_id,
            page_number=page_number,
            page_size=page_size
        )

        # Apply optional filters
        if vpc_id:
            request.vpc_id = vpc_id
        if vswitch_id:
            request.vswitch_id = vswitch_id
        if vswitch_name:
            request.vswitch_name = vswitch_name
        if zone_id:
            request.zone_id = zone_id

        return client.describe_vswitches(request).body.to_map()
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
async def describe_accounts(
    instance_id: str = Field(description="Instance ID (e.g., 'r-bp1zxszhcgatnx****')"),
    account_name: str = Field(
        default="",
        description="Account name to query. If empty, returns all accounts"
    ),
    region_id: str = Field(default="cn-hangzhou", description="Region ID"),
) -> Dict[str, Any]:
    """Query account information for a Tair instance.

    Use this to list all accounts or query a specific account.

    Returns:
        A dict containing Accounts list and RequestId.
    """
    try:
        client = OpenAPIClientManager.get_client(region_id=region_id)
        request = r_kvstore_models.DescribeAccountsRequest(instance_id=instance_id)

        if account_name:
            request.account_name = account_name

        return client.describe_accounts(request).body.to_map()
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
async def describe_security_ips(
    region_id: str = Field(description="Region ID (e.g., 'cn-hangzhou')"),
    instance_id: str = Field(description="Instance ID (e.g., 'r-bp1xxxxx')"),
) -> Dict[str, Any]:
    """Query IP whitelist configuration for a Tair instance.

    Retrieves all IP whitelist groups and their entries.
    Use this before modifying whitelists to understand the current configuration.

    Returns:
        A dict containing SecurityIpGroups list and InstanceId.
    """
    try:
        client = OpenAPIClientManager.get_client(region_id=region_id)
        req = r_kvstore_models.DescribeSecurityIpsRequest(instance_id=instance_id)
        return client.describe_security_ips(req).body.to_map()
    except Exception as e:
        return {"error": str(e)}
