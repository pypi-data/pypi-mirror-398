"""Factory for creating ReputationStorage instances. CLI mode removed, using Gateway mode."""
import logging, os
from typing import Any, Dict, Optional
from .ipfs_client import IPFSClient
from .ipfs_storage import IpfsReputationStorage
from .storage_interfaces import ReputationStorage
logger = logging.getLogger(__name__)

def _import_gateway_storage():
    from .greenfield_gateway_storage import GreenfieldGatewayStorage
    return GreenfieldGatewayStorage

def create_reputation_storage(config: Optional[Dict[str, Any]] = None, ipfs_client: Optional[IPFSClient] = None) -> ReputationStorage:
    """Create storage instance. REPUTATION_BACKEND: ipfs (default) or greenfield (gateway mode)."""
    cfg = config or {}
    backend = cfg.get("REPUTATION_BACKEND") or os.getenv("REPUTATION_BACKEND", "ipfs")
    logger.info(f"Creating storage: backend={backend}")
    
    if backend == "greenfield":
        GatewayStorage = _import_gateway_storage()
        url = cfg.get("GREENFIELD_GATEWAY_URL") or os.getenv("GREENFIELD_GATEWAY_URL") or os.getenv("AGENT0_GREENFIELD_GATEWAY_URL")
        key = cfg.get("GREENFIELD_GATEWAY_API_KEY") or os.getenv("GREENFIELD_GATEWAY_API_KEY") or os.getenv("AGENT0_GREENFIELD_GATEWAY_API_KEY")
        timeout = int(cfg.get("GREENFIELD_TIMEOUT") or os.getenv("GREENFIELD_TIMEOUT", "30"))
        if not url: raise ValueError("GREENFIELD_GATEWAY_URL required")
        if not key: raise ValueError("GREENFIELD_GATEWAY_API_KEY required")
        return GatewayStorage(gateway_url=url, api_key=key, timeout=timeout)
    
    if backend != "ipfs":
        logger.warning(f"Unknown backend {backend}, using ipfs")
    if ipfs_client is None:
        url = cfg.get("IPFS_API_URL") or os.getenv("IPFS_API_URL")
        ipfs_client = IPFSClient(url=url) if url else IPFSClient()
    return IpfsReputationStorage(client=ipfs_client)

def build_ipfs_client(config: Optional[Dict[str, Any]] = None) -> IPFSClient:
    cfg = config or {}
    return IPFSClient(
        url=cfg.get("IPFS_API_URL") or os.getenv("IPFS_API_URL"),
        filecoin_pin_enabled=str(cfg.get("FILECOIN_PIN_ENABLED", os.getenv("FILECOIN_PIN_ENABLED", "false"))).lower() == "true",
        filecoin_private_key=cfg.get("FILECOIN_PRIVATE_KEY") or os.getenv("FILECOIN_PRIVATE_KEY"),
        pinata_enabled=str(cfg.get("PINATA_ENABLED", os.getenv("PINATA_ENABLED", "false"))).lower() == "true",
        pinata_jwt=cfg.get("PINATA_JWT") or os.getenv("PINATA_JWT")
    )

