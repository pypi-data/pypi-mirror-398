"""Gateway mode Greenfield storage implementation."""
import json, logging, os, uuid
from typing import Any, Dict
import requests
from .storage_interfaces import ReputationStorage

logger = logging.getLogger(__name__)

class GreenfieldGatewayStorage(ReputationStorage):
    """Gateway mode storage - calls Greenfield Gateway HTTP API."""
    
    def __init__(self, gateway_url: str, api_key: str, timeout: int = 30):
        if not gateway_url: raise ValueError("gateway_url required")
        if not api_key: raise ValueError("api_key required")
        self.gateway_url = gateway_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self._session = requests.Session()
        self._session.headers.update({"Authorization": f"Bearer {api_key}"})
        logger.info("GreenfieldGatewayStorage: url=%s", gateway_url)

    def put(self, key: str, data: bytes) -> str:
        name = key.strip() if key else uuid.uuid4().hex
        r = self._session.post(f"{self.gateway_url}/api/v1/objects",
            files={"file": (name, data, "application/octet-stream")},
            data={"object_name": name}, timeout=self.timeout)
        r.raise_for_status()
        res = r.json()
        if not res.get("success"): raise RuntimeError(res.get("error", {}).get("message", "Upload failed"))
        return res["data"].get("objectName") or res["data"].get("object_name")

    def get(self, key: str) -> bytes:
        r = self._session.get(f"{self.gateway_url}/api/v1/objects/{key}", timeout=self.timeout)
        r.raise_for_status()
        return r.content

    def put_json(self, key: str, data: Dict[str, Any]) -> str:
        name = key.strip() if key else f"{uuid.uuid4().hex}.json"
        if not name.endswith(".json"): name += ".json"
        r = self._session.post(f"{self.gateway_url}/api/v1/objects",
            files={"file": (name, json.dumps(data).encode(), "application/json")},
            data={"object_name": name}, timeout=self.timeout)
        r.raise_for_status()
        res = r.json()
        if not res.get("success"): raise RuntimeError(res.get("error", {}).get("message", "Upload failed"))
        return res["data"].get("objectName") or res["data"].get("object_name")

    def get_json(self, key: str) -> Dict[str, Any]:
        return json.loads(self.get(key).decode())

    def build_uri(self, key: str, expires_in: int = 3600) -> str:
        r = self._session.get(f"{self.gateway_url}/api/v1/objects/{key}/signed-uri",
            params={"expires_in": expires_in}, timeout=self.timeout)
        r.raise_for_status()
        res = r.json()
        if not res.get("success"): raise RuntimeError(res.get("error", {}).get("message", "Failed"))
        return res["data"].get("signedUri") or res["data"].get("signed_uri")

