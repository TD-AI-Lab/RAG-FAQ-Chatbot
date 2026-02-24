from fastapi.testclient import TestClient

from src.api.deps import get_app_settings
from src.app import app


class DummySettings:
    def __init__(self, openai_api_key: str | None):
        self.openai_api_key = openai_api_key
        self.max_question_length = 1000
        self.rate_limit_per_minute = 0
        self.rate_limit_max_clients = 5000


def test_health_endpoint(monkeypatch):
    monkeypatch.setattr("src.api.routes.is_index_ready", lambda settings: True)
    app.dependency_overrides[get_app_settings] = lambda: DummySettings("k")
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    app.dependency_overrides.clear()


def test_cors_allows_local_streamlit_origin():
    client = TestClient(app)
    response = client.options(
        "/chat",
        headers={
            "Origin": "http://localhost:8501",
            "Access-Control-Request-Method": "POST",
        },
    )
    assert response.status_code in (200, 204)
    assert response.headers.get("access-control-allow-origin") == "http://localhost:8501"


def test_chat_validation_empty_question(monkeypatch):
    monkeypatch.setattr("src.api.routes.is_index_ready", lambda settings: True)
    app.dependency_overrides[get_app_settings] = lambda: DummySettings("k")
    client = TestClient(app)
    response = client.post("/chat", json={"question": " "})
    assert response.status_code == 400
    app.dependency_overrides.clear()


def test_chat_success(monkeypatch):
    monkeypatch.setattr("src.api.routes.is_index_ready", lambda settings: True)
    monkeypatch.setattr(
        "src.api.routes.ask",
        lambda question: {
            "answer": "Rep",
            "sources": [{"id": "1", "question": "Q", "url": "https://x", "score": 0.9, "rank": 1}],
            "debug": {},
        },
    )

    app.dependency_overrides[get_app_settings] = lambda: DummySettings("k")
    client = TestClient(app)
    response = client.post("/chat", json={"question": "Comment faire ?"})
    assert response.status_code == 200
    assert response.json()["answer"] == "Rep"
    app.dependency_overrides.clear()
