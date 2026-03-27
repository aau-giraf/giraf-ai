"""Tests for CORS middleware configuration.

These tests construct a minimal FastAPI app with CORSMiddleware to verify
the middleware behaves correctly, since the main app configures CORS at
module import time based on settings.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.testclient import TestClient


def _make_app(allowed_origins: list[str]) -> FastAPI:
    app = FastAPI()

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_methods=["GET", "POST"],
        allow_headers=["Authorization", "Content-Type"],
    )

    @app.get("/test")
    async def test_endpoint() -> dict[str, str]:
        return {"ok": "true"}

    return app


def test_cors_allows_configured_origin() -> None:
    app = _make_app(["https://giraf.example.com"])
    client = TestClient(app)
    resp = client.get(
        "/test",
        headers={"Origin": "https://giraf.example.com"},
    )
    assert resp.status_code == 200
    assert resp.headers["access-control-allow-origin"] == "https://giraf.example.com"


def test_cors_rejects_unknown_origin() -> None:
    app = _make_app(["https://giraf.example.com"])
    client = TestClient(app)
    resp = client.get(
        "/test",
        headers={"Origin": "https://evil-attacker.com"},
    )
    assert resp.status_code == 200
    assert "access-control-allow-origin" not in resp.headers


def test_cors_preflight_returns_allowed_methods() -> None:
    app = _make_app(["https://giraf.example.com"])
    client = TestClient(app)
    resp = client.options(
        "/test",
        headers={
            "Origin": "https://giraf.example.com",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Authorization",
        },
    )
    assert resp.status_code == 200
    assert resp.headers["access-control-allow-origin"] == "https://giraf.example.com"
    assert "POST" in resp.headers["access-control-allow-methods"]


def test_cors_preflight_rejects_disallowed_method() -> None:
    app = _make_app(["https://giraf.example.com"])
    client = TestClient(app)
    resp = client.options(
        "/test",
        headers={
            "Origin": "https://giraf.example.com",
            "Access-Control-Request-Method": "DELETE",
        },
    )
    assert "DELETE" not in resp.headers.get("access-control-allow-methods", "")


def test_no_cors_headers_when_no_origin() -> None:
    app = _make_app(["https://giraf.example.com"])
    client = TestClient(app)
    resp = client.get("/test")
    assert "access-control-allow-origin" not in resp.headers
