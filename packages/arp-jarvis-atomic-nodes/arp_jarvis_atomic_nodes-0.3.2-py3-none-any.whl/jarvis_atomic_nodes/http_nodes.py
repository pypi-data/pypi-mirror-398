from __future__ import annotations

import base64
import os
from typing import Any
from urllib.parse import urlparse

from pydantic import AnyHttpUrl, BaseModel, ConfigDict, Field

from .sdk import NodeContext, atomic_node

_ALLOWED_METHODS = {"GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"}
_DEFAULT_TIMEOUT = 10.0
_DEFAULT_MAX_BYTES = 1024 * 1024


def _env_csv(name: str) -> set[str]:
    raw = (os.environ.get(name) or "").strip()
    if not raw:
        return set()
    return {item.strip().lower() for item in raw.split(",") if item.strip()}


def _env_float(name: str) -> float | None:
    raw = (os.environ.get(name) or "").strip()
    if not raw:
        return None
    try:
        return float(raw)
    except ValueError:
        return None


def _env_int(name: str) -> int | None:
    raw = (os.environ.get(name) or "").strip()
    if not raw:
        return None
    try:
        return int(raw)
    except ValueError:
        return None


def _as_str_dict(value: Any, field: str) -> dict[str, str]:
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise ValueError(f"{field} must be an object")
    return {str(k): str(v) for k, v in value.items()}


class WebFetchInput(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    url: AnyHttpUrl
    method: str = "GET"
    headers: dict[str, str] | None = None
    params: dict[str, str] | None = None
    json_body: Any | None = Field(default=None, alias="json")
    body: str | None = None
    timeout_seconds: float | None = None
    max_bytes: int | None = None
    follow_redirects: bool = False


class WebFetchOutput(BaseModel):
    status_code: int
    headers: dict[str, str]
    content_type: str | None = None
    content_base64: str
    final_url: str
    content_bytes: int


@atomic_node(
    name="jarvis.web.fetch",
    side_effect="read",
    trust_tier="first_party",
    egress_policy="external_http",
)
async def web_fetch(inp: WebFetchInput, ctx: NodeContext) -> WebFetchOutput:
    """Fetch a URL over HTTP(S) and return response bytes (base64)."""
    parsed = urlparse(str(inp.url))
    host = (parsed.hostname or "").lower()

    if allowed := _env_csv("JARVIS_ATOMIC_HTTP_ALLOWED_HOSTS"):
        if host not in allowed:
            raise ValueError("host not allowed")
    if host in _env_csv("JARVIS_ATOMIC_HTTP_BLOCKED_HOSTS"):
        raise ValueError("host blocked")

    method = inp.method.upper()
    if method not in _ALLOWED_METHODS:
        raise ValueError(f"method {method} not allowed")

    headers = _as_str_dict(inp.headers, "headers")
    params = _as_str_dict(inp.params, "params")

    timeout_seconds = inp.timeout_seconds or _env_float("JARVIS_ATOMIC_HTTP_TIMEOUT_SECONDS") or _DEFAULT_TIMEOUT
    max_bytes = inp.max_bytes or _env_int("JARVIS_ATOMIC_HTTP_MAX_BYTES") or _DEFAULT_MAX_BYTES

    if ctx.http is None:
        try:
            import httpx
        except ModuleNotFoundError as exc:  # pragma: no cover - runtime only
            raise RuntimeError("httpx is required for jarvis.web.fetch; install [runtime].") from exc
        async with httpx.AsyncClient(follow_redirects=inp.follow_redirects, timeout=timeout_seconds) as client:
            response = await client.request(
                method,
                str(inp.url),
                headers=headers,
                params=params,
                content=inp.body.encode("utf-8") if isinstance(inp.body, str) else None,
                json=inp.json_body,
            )
    else:
        response = await ctx.http.request(
            method,
            str(inp.url),
            headers=headers,
            params=params,
            content=inp.body.encode("utf-8") if isinstance(inp.body, str) else None,
            json=inp.json_body,
            timeout=timeout_seconds,
            follow_redirects=inp.follow_redirects,
        )

    content = response.content
    if len(content) > max_bytes:
        raise ValueError("response too large")

    return WebFetchOutput(
        status_code=response.status_code,
        headers=dict(response.headers),
        content_type=response.headers.get("content-type"),
        content_base64=base64.b64encode(content).decode("utf-8"),
        final_url=str(response.url),
        content_bytes=len(content),
    )
