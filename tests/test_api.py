"""Integration tests for the FastAPI endpoints."""
from __future__ import annotations

import os
import tempfile

import pytest

_tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
_tmp.close()
os.environ["CBR_DB_PATH"] = _tmp.name


@pytest.fixture(scope="module")
def client():
    from fastapi.testclient import TestClient
    from api.main import app
    from case_base.db import init_db
    init_db()
    with TestClient(app) as c:
        yield c


def test_create_case(client):
    resp = client.post("/cases", json={"problem": "Cannot reset password", "solution": "Use forgot password link.", "metadata": {}})
    assert resp.status_code == 201
    data = resp.json()
    assert data["case_id"] > 0
    assert data["problem"] == "Cannot reset password"


def test_get_case(client):
    resp = client.post("/cases", json={"problem": "Order missing", "solution": "Check courier.", "metadata": {"type": "delivery"}})
    case_id = resp.json()["case_id"]

    resp2 = client.get(f"/cases/{case_id}")
    assert resp2.status_code == 200
    assert resp2.json()["solution"] == "Check courier."


def test_get_missing_case(client):
    resp = client.get("/cases/99999")
    assert resp.status_code == 404


def test_query_endpoint(client):
    # Seed a case first
    client.post("/cases", json={"problem": "My invoice is wrong", "solution": "Email billing@example.com.", "metadata": {}})
    resp = client.post("/query", json={"problem": "I have a billing problem", "top_k": 3})
    assert resp.status_code == 200
    data = resp.json()
    assert "answer" in data
    assert isinstance(data["top_matches"], list)


def test_delete_case(client):
    resp = client.post("/cases", json={"problem": "To delete", "solution": "Delete me.", "metadata": {}})
    case_id = resp.json()["case_id"]
    del_resp = client.delete(f"/cases/{case_id}")
    assert del_resp.status_code == 204
    assert client.get(f"/cases/{case_id}").status_code == 404
