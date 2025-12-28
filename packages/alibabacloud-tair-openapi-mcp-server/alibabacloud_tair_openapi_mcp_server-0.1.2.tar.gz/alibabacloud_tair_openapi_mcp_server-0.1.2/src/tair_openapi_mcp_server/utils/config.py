import os
from typing import Dict, Optional

from dotenv import load_dotenv


load_dotenv()

"""
Configuration for Tair OpenAPI MCP Server:

OpenAPI (Alibaba Cloud R-KVStore):
- ALIBABA_CLOUD_ACCESS_KEY_ID
- ALIBABA_CLOUD_ACCESS_KEY_SECRET

Logging:
- TAIR_MCP_LOG_LEVEL: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL). Default: INFO.
- TAIR_MCP_LOG_FILE: Optional file path to write logs.
"""

OPENAPI_CFG: Dict[str, Optional[str]] = {
    "access_key_id": os.getenv("ALIBABA_CLOUD_ACCESS_KEY_ID", None),
    "access_key_secret": os.getenv("ALIBABA_CLOUD_ACCESS_KEY_SECRET", None),
    "log_level": os.getenv("TAIR_MCP_LOG_LEVEL", "INFO"),
    "log_file": os.getenv("TAIR_MCP_LOG_FILE", None),
}