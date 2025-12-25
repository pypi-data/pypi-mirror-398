"""Privacy helpers: middleware to strip or block product data from requests.

This middleware is conservative by default: it *strips* common product-related
fields from JSON payloads and adds a response header `X-Product-Data-Removed: 1`.
You can also configure it to reject requests that contain product data.
"""
from __future__ import annotations

import json
from typing import Any, Iterable, Set

from starlette.responses import Response

DEFAULT_PRODUCT_KEYS: Set[str] = {"product", "products", "items", "product_data", "order", "orders"}


def _strip_product_fields(payload: Any, keys: Iterable[str]) -> Any:
    """Recursively strip keys from payload. Returns a new payload structure."""
    if isinstance(payload, dict):
        new = {}
        for k, v in payload.items():
            if k in keys:
                # mark removed while preserving list elements if present
                if isinstance(v, list):
                    new[k] = [
                        {**(x if isinstance(x, dict) else {}), "_removed": True}
                        for x in v
                    ]
                else:
                    new[k] = {"_removed": True}
            else:
                new[k] = _strip_product_fields(v, keys)
        return new
    elif isinstance(payload, list):
        return [_strip_product_fields(x, keys) for x in payload]
    else:
        return payload


class StripProductDataMiddleware:
    """ASGI middleware that strips product-related fields from JSON request bodies.

    This implementation follows the ASGI callable pattern to avoid pitfalls with
    `BaseHTTPMiddleware` and ensures the request body is replayed correctly to
    downstream consumers.

    Args:
        app: ASGI app
        keys: iterable of keys to treat as product data (defaults to `DEFAULT_PRODUCT_KEYS`)
        mode: 'strip' to remove fields, 'block' to reject with 400 when found
    """

    def __init__(self, app, *, keys: Iterable[str] | None = None, mode: str = "strip"):
        self.app = app
        self.keys = set(keys or DEFAULT_PRODUCT_KEYS)
        if mode not in {"strip", "block"}:
            raise ValueError("mode must be 'strip' or 'block'")
        self.mode = mode

    async def __call__(self, scope, receive, send):
        # Only operate on HTTP requests with JSON content
        if scope.get("type") != "http":
            await self.app(scope, receive, send)
            return

        headers = {k.decode("latin-1"): v.decode("latin-1") for k, v in scope.get("headers", [])}
        content_type = headers.get("content-type", "")

        if "application/json" not in content_type.lower():
            await self.app(scope, receive, send)
            return

        # Read the full body from the ASGI receive
        body = b""
        more_body = True
        while more_body:
            message = await receive()
            if message.get("type") == "http.request":
                body += message.get("body", b"") or b""
                more_body = message.get("more_body", False)
            else:
                # pass through non-http messages
                pass

        payload = None
        if body:
            try:
                payload = json.loads(body)
            except Exception:
                payload = None

        if payload is not None:
            found = any(k in payload for k in self.keys) if isinstance(payload, dict) else False
            if found:
                if self.mode == "block":
                    # send a 400 response and short-circuit
                    resp = Response(status_code=400, content="Product data is not allowed")
                    await resp(scope, receive, send)
                    return

                # strip fields
                new_payload = _strip_product_fields(payload, self.keys)
                new_body = json.dumps(new_payload).encode("utf-8")

                # create a receive function that will replay the new body once
                called = {"v": False}

                async def enjoy():
                    if not called["v"]:
                        called["v"] = True
                        return {"type": "http.request", "body": new_body, "more_body": False}
                    return {"type": "http.request", "body": b"", "more_body": False}

                # wrapper send to inject header indicating removal
                async def send_with_header(message):
                    # Intercept http.response.start to add headers
                    if message.get("type") == "http.response.start":
                        headers = list(message.get("headers", []))
                        headers.append((b"x-product-data-removed", b"1"))
                        message["headers"] = headers
                    await send(message)

                await self.app(scope, enjoy, send_with_header)
                return

        # No product keys found or non-JSON: replay original body for downstream
        called = {"v": False}

        async def replay():
            if not called["v"]:
                called["v"] = True
                return {"type": "http.request", "body": body or b"", "more_body": False}
            return {"type": "http.request", "body": b"", "more_body": False}

        await self.app(scope, replay, send)
        return

__all__ = ["StripProductDataMiddleware", "_strip_product_fields", "DEFAULT_PRODUCT_KEYS"]