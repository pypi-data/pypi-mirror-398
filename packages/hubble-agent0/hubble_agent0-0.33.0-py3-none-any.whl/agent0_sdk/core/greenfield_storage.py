"""Deprecated: Use GreenfieldGatewayStorage instead. HTTP download only."""
import json, uuid, requests
from typing import Any, Dict
from urllib.parse import quote
from .storage_interfaces import ReputationStorage

class GreenfieldReputationStorage(ReputationStorage):
    """Deprecated. HTTP download only. For uploads, use GreenfieldGatewayStorage."""
    def __init__(self, sp_host: str, bucket: str, private_key: str = "", content_type: str = "", timeout: int = 30, **kwargs):
        if not sp_host or not bucket: raise ValueError("sp_host and bucket required")
        self.sp_host, self.bucket, self.timeout = sp_host.strip(), bucket.strip(), timeout
    def put(self, key: str, data: bytes) -> str: raise NotImplementedError("Use GreenfieldGatewayStorage")
    def get(self, key: str) -> bytes:
        r = requests.get(f"https://{self.sp_host}/view/{self.bucket}/{quote(key)}", timeout=self.timeout)
        r.raise_for_status()
        return r.content
    def put_json(self, key: str, data: Dict[str, Any]) -> str: raise NotImplementedError("Use GreenfieldGatewayStorage")
    def get_json(self, key: str) -> Dict[str, Any]: return json.loads(self.get(key).decode())
    def build_uri(self, key: str) -> str: return f"https://{self.bucket}.{self.sp_host}/{quote(key)}"

