import logging
import sys
from typing import Optional

from tair_openapi_mcp_server.utils.config import OPENAPI_CFG

_configured = False


def configure_logging(
    level: Optional[str] = None,
    log_file: Optional[str] = None,
) -> None:
    global _configured
    if _configured:
        return
    _configured = True

    level_name = level or OPENAPI_CFG.get("log_level", "INFO")
    log_level = getattr(logging, level_name.upper(), logging.INFO)

    # Configure with timestamp format
    handlers = [logging.StreamHandler(sys.stderr)]

    log_file_path = log_file or OPENAPI_CFG.get("log_file")
    if log_file_path:
        handlers.append(logging.FileHandler(log_file_path, encoding="utf-8"))

    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=handlers,
    )