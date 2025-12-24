from __future__ import annotations

import copy
import requests
import threading
from requests import Response
from requests.exceptions import RequestException
from typing import Any, Dict, Optional, Union
from urllib.parse import urljoin

from .exceptions import (
    AuthenticationError,
    ClientInitializationError,
    ConflictError,
    NotFoundError,
    QuantumSDKError,
    ServerError,
    TransportError,
    ValidationError,
)

JsonType = Union[Dict[str, Any], list, str, int, float, bool, None]


class HttpClient:
    _instance: Optional["HttpClient"] = None
    _lock = threading.Lock()

    def __init__(
        self,
        access_token: Optional[str] = None,
        refresh_token: Optional[str] = None,
        *,
        base_url: str = "https://api.quantumelements.ai",
        refresh_endpoint: str = "/auth/refresh_token/",
        timeout: float = 15.0,
        session: Optional[requests.Session] = None,
    ) -> None:
        if HttpClient._instance is not None:
            raise ClientInitializationError(
                "HttpClient is a singleton; use HttpClient.initialize(...) "
                "or HttpClient.instance()."
            )

        if not base_url:
            raise ClientInitializationError("base_url is required for HttpClient.")

        self.base_url = self._normalize_base_url(base_url)
        self._access_token = access_token
        self._refresh_token = refresh_token
        self._refresh_endpoint = refresh_endpoint
        self._timeout = timeout
        self._session = session or requests.Session()

    @classmethod
    def initialize(
        cls,
        access_token: Optional[str] = None,
        refresh_token: Optional[str] = None,
        *,
        base_url: str = "https://api.quantumelements.ai",
        refresh_endpoint: str = "/auth/refresh_token/",
        timeout: float = 120.0,
        session: Optional[requests.Session] = None,
    ) -> "HttpClient":

        with cls._lock:
            cls._instance = cls(
                access_token,
                refresh_token,
                base_url=base_url,
                refresh_endpoint=refresh_endpoint,
                timeout=timeout,
                session=session,
            )
            return cls._instance

    @classmethod
    def instance(cls) -> "HttpClient":
        if cls._instance is None:
            raise ClientInitializationError(
                "HttpClient has not been initialized. Call "
                "HttpClient.initialize(...) first."
            )
        return cls._instance

    @classmethod
    def reset(cls) -> None:
        with cls._lock:
            cls._instance = None

    @staticmethod
    def _normalize_base_url(base_url: str) -> str:
        base = base_url.strip()
        if not base.endswith("/"):
            base += "/"
        return base

    @property
    def access_token(self) -> Optional[str]:
        return self._access_token

    @property
    def refresh_token(self) -> Optional[str]:
        return self._refresh_token

    def set_tokens(self, access: str, refresh: str) -> None:
        self._access_token = access
        self._refresh_token = refresh

    def get(
        self, path: str, *, params: Optional[Dict[str, Any]] = None, **kwargs: Any
    ) -> JsonType:
        response = self._request("GET", path, params=params, **kwargs)
        return self._parse_response(response)

    def post(
        self, path: str, *, json: Optional[Dict[str, Any]] = None, **kwargs: Any
    ) -> JsonType:
        response = self._request("POST", path, json=json, **kwargs)
        return self._parse_response(response)

    def patch(
        self, path: str, *, json: Optional[Dict[str, Any]] = None, **kwargs: Any
    ) -> JsonType:
        response = self._request("PATCH", path, json=json, **kwargs)
        return self._parse_response(response)

    def delete(self, path: str, **kwargs: Any) -> Optional[JsonType]:
        response = self._request("DELETE", path, **kwargs)
        if response.status_code == 204 or not response.content:
            return None
        return self._parse_response(response)

    def _request(
        self, method: str, path: str, retry: bool = True, **kwargs: Any
    ) -> Response:
        url = self._build_url(path)
        headers = kwargs.pop("headers", {}) or {}
        auth_headers = self._auth_headers()
        if auth_headers:
            headers.update(auth_headers)

        request_kwargs = copy.deepcopy(kwargs)
        request_kwargs["headers"] = headers
        request_kwargs.setdefault("timeout", self._timeout)

        try:
            response = self._session.request(method, url, **request_kwargs)
        except RequestException as exc:
            raise TransportError(
                f"Failed to execute {method} request to {url}: {exc}"
            ) from exc

        if response.status_code == 401 and retry and self._refresh_token:
            if self._refresh_tokens():
                # retry once with refreshed access token
                auth_headers = self._auth_headers()
                if auth_headers:
                    headers.update(auth_headers)
                request_kwargs = copy.deepcopy(kwargs)
                request_kwargs["headers"] = headers
                request_kwargs.setdefault("timeout", self._timeout)
                try:
                    response = self._session.request(method, url, **request_kwargs)
                except RequestException as exc:
                    raise TransportError(
                        f"Failed to execute retry {method} request to {url}: {exc}"
                    ) from exc

        if response.status_code >= 400:
            self._handle_error(response)

        return response

    def _parse_response(self, response: Response) -> JsonType:
        if not response.content:
            return None
        content_type = response.headers.get("Content-Type", "")
        if "application/json" in content_type:
            return response.json()
        return response.text

    def _auth_headers(self) -> Dict[str, str]:
        if not self._access_token:
            return {}
        return {"Authorization": f"Bearer {self._access_token}"}

    def _build_url(self, path: str) -> str:
        cleaned_path = path.lstrip("/")
        return urljoin(self.base_url, cleaned_path)

    def _refresh_tokens(self) -> bool:
        if not self._refresh_token:
            return False

        refresh_url = self._build_url(self._refresh_endpoint)
        payload = {"refresh": self._refresh_token}
        try:
            response = self._session.post(
                refresh_url,
                json=payload,
                timeout=self._timeout,
            )
        except RequestException as exc:
            raise TransportError(f"Failed to refresh tokens: {exc}") from exc

        if response.status_code != 200:
            self._handle_error(response)
            return False

        data = response.json()
        access = data.get("access")
        refresh = data.get("refresh")
        if not access or not refresh:
            raise AuthenticationError(
                "Refresh endpoint returned invalid payload. 'access' and "
                "'refresh' keys are required."
            )
        self._access_token = access
        self._refresh_token = refresh
        return True

    def _handle_error(self, response: Response) -> None:
        status = response.status_code
        try:
            payload = response.json()
        except ValueError:
            payload = response.text or None

        message = self._extract_error_message(payload) or f"HTTP {status}"

        import json as json_module

        print(f"[ERROR] HTTP {status}: {message}")
        print(f"[ERROR] Request URL: {response.url}")
        print(
            f"[ERROR] Request Method: {response.request.method if response.request else 'N/A'}"
        )
        if payload:
            print(
                f"[ERROR] Response payload: {json_module.dumps(payload, indent=2) if isinstance(payload, dict) else payload}"
            )
        else:
            print(
                f"[ERROR] Response body (raw): {response.text[:500] if response.text else '(empty)'}"
            )

        print(f"[ERROR] Response headers: {dict(response.headers)}")

        if status in (400, 422):
            raise ValidationError(message, status_code=status, payload=payload)
        if status in (401, 403):
            raise AuthenticationError(message, status_code=status, payload=payload)
        if status == 404:
            raise NotFoundError(message, status_code=status, payload=payload)
        if status == 409:
            raise ConflictError(message, status_code=status, payload=payload)
        if 500 <= status < 600:
            raise ServerError(message, status_code=status, payload=payload)
        raise QuantumSDKError(message, status_code=status, payload=payload)

    @staticmethod
    def _extract_error_message(payload: Any) -> Optional[str]:
        if isinstance(payload, dict):
            detail = payload.get("detail")
            if isinstance(detail, str):
                return detail
            message = payload.get("message")
            if isinstance(message, str):
                return message
        if isinstance(payload, str):
            return payload
        return None
