"""Healthcheck contract for the standalone agent app."""
from __future__ import annotations

from fastapi.testclient import TestClient

import web_app


def test_healthcheck_ok():
    client = TestClient(web_app.app)
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["product"] == "AllCPR Site Operations Agent"
    assert body["version"] == "v0.8b1"

