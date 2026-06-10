"""
Flask route tests — OrchestratorAgent and file I/O are mocked.
"""
import json
import os
import tempfile
from unittest.mock import patch, MagicMock

import pytest

import app as flask_app


@pytest.fixture()
def client(tmp_path):
    """Flask test client with DATA_FILE redirected to a temp directory."""
    data_file = str(tmp_path / "headlines.json")
    with patch.object(flask_app, "DATA_FILE", data_file, create=True), \
         patch("app.DATA_FILE", data_file):
        flask_app.app.config["TESTING"] = True
        with flask_app.app.test_client() as c:
            yield c, data_file


# ── GET / ─────────────────────────────────────────────────────────────────────

def test_index_returns_200(client):
    c, _ = client
    resp = c.get("/")
    assert resp.status_code == 200
    assert b"Daily Headlines" in resp.data


# ── GET /api/headlines ────────────────────────────────────────────────────────

def test_api_headlines_empty_when_no_file(client):
    c, _ = client
    resp = c.get("/api/headlines")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["updated_at"] is None
    assert data["headlines"] == []


def test_api_headlines_returns_cached_data(client):
    c, data_file = client
    payload = {"updated_at": "2026-01-01T09:00:00", "headlines": [
        {"rank": 1, "title": "Test Headline", "source": "BBC", "link": "http://bbc.com",
         "category": "Tech", "why": "important"}
    ]}
    with open(data_file, "w", encoding="utf-8") as f:
        json.dump(payload, f)

    resp = c.get("/api/headlines")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["updated_at"] == "2026-01-01T09:00:00"
    assert len(data["headlines"]) == 1
    assert data["headlines"][0]["title"] == "Test Headline"


# ── POST /api/refresh ─────────────────────────────────────────────────────────

def test_api_refresh_returns_headlines(client):
    c, data_file = client
    fake_headlines = [
        {"rank": 1, "title": "Fresh News", "source": "Reuters",
         "link": "http://r.com/1", "category": "Business", "why": "big deal"}
    ]

    with patch("app.OrchestratorAgent") as MockOrch:
        MockOrch.return_value.run.return_value = fake_headlines
        resp = c.post("/api/refresh")

    assert resp.status_code == 200
    data = resp.get_json()
    assert data["status"] == "ok"
    assert len(data["headlines"]) == 1
    assert data["headlines"][0]["title"] == "Fresh News"
    assert "updated_at" in data


def test_api_refresh_writes_data_file(client):
    c, data_file = client
    fake_headlines = [
        {"rank": 1, "title": "Written to disk", "source": "S",
         "link": "http://x.com", "category": "Tech", "why": "w"}
    ]

    with patch("app.OrchestratorAgent") as MockOrch:
        MockOrch.return_value.run.return_value = fake_headlines
        c.post("/api/refresh")

    assert os.path.exists(data_file)
    with open(data_file, encoding="utf-8") as f:
        saved = json.load(f)
    assert saved["headlines"][0]["title"] == "Written to disk"
    assert saved["updated_at"] is not None


def test_api_refresh_returns_500_on_error(client):
    c, _ = client
    with patch("app.OrchestratorAgent") as MockOrch:
        MockOrch.return_value.run.side_effect = RuntimeError("API down")
        resp = c.post("/api/refresh")

    assert resp.status_code == 500
    data = resp.get_json()
    assert data["status"] == "error"
    assert "API down" in data["message"]


def test_api_refresh_subsequent_load_reflects_new_data(client):
    """After a refresh, /api/headlines should return the new data."""
    c, data_file = client
    fake_headlines = [
        {"rank": 1, "title": "Brand New Story", "source": "CNN",
         "link": "http://cnn.com", "category": "Health", "why": "health"}
    ]

    with patch("app.OrchestratorAgent") as MockOrch:
        MockOrch.return_value.run.return_value = fake_headlines
        c.post("/api/refresh")

    resp = c.get("/api/headlines")
    data = resp.get_json()
    assert data["headlines"][0]["title"] == "Brand New Story"
