"""Vercel ASGI entry point with rewrite-path restoration."""

from urllib.parse import parse_qsl, urlencode

from backend.app.main import app as fastapi_app


async def app(scope, receive, send):
    """Restore the public API path passed through Vercel's function rewrite."""
    if scope["type"] == "http":
        query = parse_qsl(scope.get("query_string", b"").decode(), keep_blank_values=True)
        public_path = next((value for key, value in query if key == "__path"), None)
        if public_path is not None:
            scope = dict(scope)
            restored = f"/api/{public_path.lstrip('/')}"
            scope["path"] = restored
            scope["raw_path"] = restored.encode()
            scope["query_string"] = urlencode(
                [(key, value) for key, value in query if key != "__path"],
                doseq=True,
            ).encode()
    await fastapi_app(scope, receive, send)


__all__ = ["app"]

