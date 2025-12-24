from pathlib import Path
from textwrap import dedent

RUNTIME_EXCEPTIONS: str = dedent(
    """
from __future__ import annotations

from typing import Any


class GraphQLHTTPError(RuntimeError):
    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        response_text: str | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.response_text = response_text

class GraphQLErrors(RuntimeError):
    \"\"\"Raised when the GraphQL response contains an 'errors' array.\"\"\"
    def __init__(self, errors: list[Any], *, data: Any = None) -> None:
        super().__init__('GraphQL operation returned errors')
        self.errors = errors
        self.data = data
"""
).lstrip()

RUNTIME_TRANSPORT: str = dedent(
    """
from __future__ import annotations

import datetime
import time
from collections.abc import Iterable, Mapping, MutableMapping
from typing import Any

import httpx
import jwt

from .exceptions import GraphQLErrors, GraphQLHTTPError

Json = dict[str, Any]

_SERVICE_TOKEN_ALG = \"EdDSA\"


def create_service_token(
    service_name: str,
    version: int,
    private_key_bytes: bytes,
    scopes: list[str] | None = None,
) -> str:
    now = datetime.datetime.now(datetime.UTC)
    headers = {
        \"alg\": _SERVICE_TOKEN_ALG,
        \"kid\": f\"{service_name}.v{version}\",
        \"typ\": \"JWT\",
    }
    claims = {
        \"iss\": service_name,
        \"sub\": "service:ingester-1",
        \"aud\": "authenticated",
        \"iat\": int(now.timestamp()),
        \"exp\": int((now + datetime.timedelta(minutes=15)).timestamp()),
        \"service_metadata\": {
            \"service_name\": service_name,
            \"key_version\": version,
            \"iam_metadata\": {
                \"role\": \"internal_service\",
                \"scopes\": scopes,
            },
        },
    }

    return jwt.encode(
        payload=claims,
        key=private_key_bytes,
        algorithm=_SERVICE_TOKEN_ALG,
        headers=headers,
    )

class Transport:
    \"\"\"Sync GraphQL transport using httpx.Client, with optional retries.\"\"\"
    def __init__(
        self,
        url: str,
        *,
        headers: httpx.Headers | None = None,
        timeout: float = 15.0,
        retries: int = 0,
        backoff_factor: float = 0.5,
        client: httpx.Client | None = None,
    ) -> None:
        self._own = client is None
        self._client = client or httpx.Client(base_url=url, timeout=timeout)
        self._endpoint = ""  # use base_url by default
        self._headers: dict[str, str] = dict(headers or {})
        self._retries = max(0, retries)
        self._backoff = max(0.0, backoff_factor)

    def execute(
        self,
        query: str,
        variables: dict[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> Json:
        payload = {"query": query, "variables": variables or {}}
        data = self._post_json(payload, headers=headers)
        if "errors" in data and data["errors"]:
            raise GraphQLErrors(data["errors"], data=data.get("data"))
        return data

    def execute_batch(
        self,
        operations: Iterable[dict[str, Any]],
        *,
        headers: Mapping[str, str] | None = None,
    ) -> Any:
        data = self._post_json(list(operations), headers=headers)
        if isinstance(data, dict) and "errors" in data and data["errors"]:
            raise GraphQLErrors(data["errors"], data=data.get("data"))
        return data

    def close(self) -> None:
        if self._own:
            self._client.close()

    def __enter__(self) -> Transport:
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def _post_json(self, body: Any, headers: Mapping[str, str] | None) -> Json:
        merged: MutableMapping[str, str] = {
            **self._headers,
            "content-type": "application/json",
        }
        if headers:
            merged.update(headers)
        attempt = 0
        while True:
            try:
                resp = self._client.post(self._endpoint, json=body, headers=merged)
                if not (200 <= resp.status_code < 300):
                    raise GraphQLHTTPError(
                        f"HTTP {resp.status_code}",
                        status_code=resp.status_code,
                        response_text=resp.text,
                    )
                return resp.json()
            except (httpx.TransportError, GraphQLHTTPError) as e:
                if attempt >= self._retries:
                    if isinstance(e, GraphQLHTTPError):
                        raise
                    raise GraphQLHTTPError(str(e)) from e
                time.sleep(self._backoff * (2 ** attempt))
                attempt += 1


class AsyncTransport:
    \"\"\"Async GraphQL transport using httpx.AsyncClient, with optional retries.\"\"\"
    def __init__(
        self,
        url: str,
        *,
        headers: Mapping[str, str] | None = None,
        timeout: float = 15.0,
        retries: int = 0,
        backoff_factor: float = 0.5,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self._own = client is None
        self._client = client or httpx.AsyncClient(base_url=url, timeout=timeout)
        self._endpoint = ""
        self._headers: dict[str, str] = dict(headers or {})
        self._retries = max(0, retries)
        self._backoff = max(0.0, backoff_factor)

    async def execute(
        self,
        query: str,
        variables: dict[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> Json:
        payload = {"query": query, "variables": variables or {}}
        data = await self._post_json(payload, headers=headers)
        if "errors" in data and data["errors"]:
            raise GraphQLErrors(data["errors"], data=data.get("data"))
        return data

    async def execute_batch(
        self,
        operations: Iterable[dict[str, Any]],
        *,
        headers: Mapping[str, str] | None = None,
    ) -> Any:
        data = await self._post_json(list(operations), headers=headers)
        if isinstance(data, dict) and "errors" in data and data["errors"]:
            raise GraphQLErrors(data["errors"], data=data.get("data"))
        return data

    async def aclose(self) -> None:
        if self._own:
            await self._client.aclose()

    async def __aenter__(self) -> AsyncTransport:
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.aclose()

    async def _post_json(self, body: Any, headers: Mapping[str, str] | None) -> Json:
        merged: MutableMapping[str, str] = {
            **self._headers,
            "content-type": "application/json",
        }
        if headers:
            merged.update(headers)
        attempt = 0
        while True:
            try:
                resp = await self._client.post(
                    self._endpoint,
                    json=body,
                    headers=merged
                )
                if not (200 <= resp.status_code < 300):
                    raise GraphQLHTTPError(
                        f"HTTP {resp.status_code}",
                        status_code=resp.status_code,
                        response_text=resp.text,
                    )
                return resp.json()
            except (httpx.TransportError, GraphQLHTTPError) as e:
                if attempt >= self._retries:
                    if isinstance(e, GraphQLHTTPError):
                        raise
                    raise GraphQLHTTPError(str(e)) from e
                import asyncio
                await asyncio.sleep(self._backoff * (2 ** attempt))
                attempt += 1
"""
).lstrip()


def write_runtime(out_dir: Path) -> None:
    (out_dir / "exceptions.py").write_text(
        RUNTIME_EXCEPTIONS,
        encoding="utf-8",
    )

    # noqa: E501
    (out_dir / "__init__.py").write_text(
        RUNTIME_TRANSPORT,
        encoding="utf-8",
    )
