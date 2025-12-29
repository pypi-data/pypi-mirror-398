from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

import requests


@dataclass
class FluxsaveError(Exception):
    message: str
    status: int
    data: Optional[Any] = None

    def __str__(self) -> str:
        return f"{self.status}: {self.message}"


class FluxsaveClient:
    def __init__(
        self,
        base_url: str,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        timeout: int = 30,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.api_secret = api_secret
        self.timeout = timeout

    def set_auth(self, api_key: str, api_secret: str) -> None:
        self.api_key = api_key
        self.api_secret = api_secret

    def _headers(self) -> Dict[str, str]:
        if not self.api_key or not self.api_secret:
            raise FluxsaveError("API key and secret are required", 401)
        return {
            "x-api-key": self.api_key,
            "x-api-secret": self.api_secret,
        }

    def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        url = f"{self.base_url}{path}"
        response = requests.request(method, url, headers=self._headers(), timeout=self.timeout, **kwargs)
        try:
            payload = response.json()
        except ValueError:
            payload = response.text

        if not response.ok:
            message = payload.get("message") if isinstance(payload, dict) else response.reason
            raise FluxsaveError(message or response.reason, response.status_code, payload)

        return payload

    def upload_file(self, file_path: str, name: Optional[str] = None, transform: Optional[bool] = None) -> Any:
        files = {"file": open(file_path, "rb")}
        data: Dict[str, Any] = {}
        if name:
            data["name"] = name
        if transform is not None:
            data["transform"] = str(transform).lower()
        try:
            return self._request("POST", "/api/v1/files/upload", files=files, data=data)
        finally:
            files["file"].close()

    def upload_files(self, file_paths: list[str], name: Optional[str] = None, transform: Optional[bool] = None) -> Any:
        files = [("files", open(path, "rb")) for path in file_paths]
        data: Dict[str, Any] = {}
        if name:
            data["name"] = name
        if transform is not None:
            data["transform"] = str(transform).lower()
        try:
            return self._request("POST", "/api/v1/files/upload", files=files, data=data)
        finally:
            for _, fh in files:
                fh.close()

    def list_files(self) -> Any:
        return self._request("GET", "/api/v1/files")

    def get_file_metadata(self, file_id: str) -> Any:
        return self._request("GET", f"/api/v1/files/metadata/{file_id}")

    def update_file(
        self,
        file_id: str,
        file_path: str,
        name: Optional[str] = None,
        transform: Optional[bool] = None,
    ) -> Any:
        files = {"file": open(file_path, "rb")}
        data: Dict[str, Any] = {}
        if name:
            data["name"] = name
        if transform is not None:
            data["transform"] = str(transform).lower()
        try:
            return self._request("PUT", f"/api/v1/files/{file_id}", files=files, data=data)
        finally:
            files["file"].close()

    def delete_file(self, file_id: str) -> Any:
        return self._request("DELETE", f"/api/v1/files/{file_id}")

    def get_metrics(self) -> Any:
        return self._request("GET", "/api/v1/metrics")

    def build_file_url(self, file_id: str, **options: Any) -> str:
        url = f"{self.base_url}/api/v1/files/{file_id}"
        if options:
            query = "&".join(f"{k}={v}" for k, v in options.items())
            return f"{url}?{query}"
        return url
