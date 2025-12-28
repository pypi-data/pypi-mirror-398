import logging
from typing import Dict, Tuple

from alibabacloud_tea_openapi import models as open_api_models
from alibabacloud_r_kvstore20150101.client import Client as R_kvstoreClient
from alibabacloud_vpc20160428.client import Client as VpcClient
from tair_openapi_mcp_server.utils.config import OPENAPI_CFG

_logger = logging.getLogger(__name__)


class OpenAPIClientManager:
    """Alibaba Cloud OpenAPI client manager for R-KVStore and VPC.

    Provides cached client instances per region to avoid repeated initialization.
    Each region gets its own client instance since endpoints differ by region.
    """

    _kvstore_clients: Dict[str, R_kvstoreClient] = {}
    _vpc_clients: Dict[str, VpcClient] = {}

    @classmethod
    def _get_credentials(cls) -> Tuple[str, str]:
        """Get and validate AK/SK credentials from environment.

        Returns:
            Tuple of (access_key_id, access_key_secret)

        Raises:
            ValueError: If credentials are not configured
        """
        ak = OPENAPI_CFG.get("access_key_id")
        sk = OPENAPI_CFG.get("access_key_secret")

        if not ak or not sk:
            raise ValueError(
                "Missing credentials. Set ALIBABA_CLOUD_ACCESS_KEY_ID and "
                "ALIBABA_CLOUD_ACCESS_KEY_SECRET in environment or .env file"
            )
        return ak, sk

    @classmethod
    def get_client(cls, region_id: str) -> R_kvstoreClient:
        """Get R-KVStore openapi client for specified region.

        Args:
            region_id: Alibaba Cloud region ID (e.g., 'cn-hangzhou')

        Returns:
            Cached R-KVStore openapi client instance for the region
        """
        if not region_id:
            raise ValueError("region_id is required")

        if region_id not in cls._kvstore_clients:
            ak, sk = cls._get_credentials()
            config = open_api_models.Config(
                access_key_id=ak,
                access_key_secret=sk,
                region_id=region_id
            )
            cls._kvstore_clients[region_id] = R_kvstoreClient(config)
            _logger.info("R-KVStore client initialized for region: %s", region_id)

        return cls._kvstore_clients[region_id]

    @classmethod
    def get_vpc_client(cls, region_id: str) -> VpcClient:
        """Get VPC openapi client for specified region.

        Args:
            region_id: Alibaba Cloud region ID (e.g., 'cn-hangzhou')

        Returns:
            Cached VPC openapi client instance for the region
        """
        if not region_id:
            raise ValueError("region_id is required")

        if region_id not in cls._vpc_clients:
            ak, sk = cls._get_credentials()
            config = open_api_models.Config(
                access_key_id=ak,
                access_key_secret=sk
            )
            config.endpoint = f"vpc.{region_id}.aliyuncs.com"
            cls._vpc_clients[region_id] = VpcClient(config)
            _logger.info("VPC client initialized for region: %s", region_id)

        return cls._vpc_clients[region_id]

    @classmethod
    def reset(cls) -> None:
        """Reset all cached client instances.

        Useful for testing or when credentials change.
        """
        cls._kvstore_clients.clear()
        cls._vpc_clients.clear()
        _logger.info("All cached clients have been reset")
