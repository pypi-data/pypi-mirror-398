from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict, Mapping, Optional

import requests

from .exceptions import ApiError, AuthenticationError, RequestError


DEFAULT_BASE_URL = "https://red-rhg.openrainbow.io/provisioningapi/api"
DEFAULT_TIMEOUT = 10


@dataclass
class TransportConfig:
    base_url: str = DEFAULT_BASE_URL
    timeout: int = DEFAULT_TIMEOUT
    user_agent: str = "rbh-builder-python/0.1.0"


class Transport:
    """
    Thin wrapper around requests.Session to handle base URL, headers, and error mapping.
    """

    def __init__(
        self,
        config: TransportConfig,
        access_token: Optional[str] = None,
        session: Optional[requests.Session] = None,
    ) -> None:
        self.config = config
        self.session = session or requests.Session()
        self.session.headers.update({"User-Agent": self.config.user_agent})
        if access_token:
            self.set_access_token(access_token)

    def set_access_token(self, token: str) -> None:
        self.session.headers.update({"Authorization": f"Bearer {token}"})

    def request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Mapping[str, Any]] = None,
        json_body: Optional[Mapping[str, Any]] = None,
        data: Optional[Mapping[str, Any]] = None,
        headers: Optional[Mapping[str, str]] = None,
    ) -> Dict[str, Any]:
        url = f"{self.config.base_url.rstrip('/')}/{path.lstrip('/')}"
        try:
            resp = self.session.request(
                method=method.upper(),
                url=url,
                params=params,
                json=json_body,
                data=data,
                headers=headers,
                timeout=self.config.timeout,
            )
        except requests.RequestException as exc:
            raise RequestError(str(exc)) from exc

        if resp.status_code == 401:
            raise AuthenticationError(resp.text, status_code=resp.status_code)

        # Best-effort JSON parse for error context.
        try:
            payload: Dict[str, Any] = resp.json() if resp.text else {}
        except json.JSONDecodeError:
            payload = {}

        if resp.status_code >= 400:
            message = payload.get("ErrorMessage") or payload.get("Message") or resp.text
            raise ApiError(resp.status_code, message or "Request failed", payload)

        return payload
