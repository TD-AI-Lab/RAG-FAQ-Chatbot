import httpx
import pytest

from src.core.errors import BackendConnectionError, BackendResponseError
from src.services.backend_client import BackendClient


def test_backend_client_health_ok(monkeypatch):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"status": "ok", "index_ready": True, "llm_ready": True})

    transport = httpx.MockTransport(handler)

    def fake_request(self, method, url, json_payload=None):
        with httpx.Client(transport=transport, timeout=10) as client:
            return client.request(method, url, json=json_payload)

    monkeypatch.setattr("src.services.backend_client.BackendClient._request", fake_request)

    client = BackendClient("http://localhost:8000", 20, "/chat", "/health")
    health = client.health()
    assert health.status == "ok"


def test_backend_client_chat_400(monkeypatch):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(400, json={"detail": "Question too short"})

    transport = httpx.MockTransport(handler)

    def fake_request(self, method, url, json_payload=None):
        with httpx.Client(transport=transport, timeout=10) as client:
            return client.request(method, url, json=json_payload)

    monkeypatch.setattr("src.services.backend_client.BackendClient._request", fake_request)

    client = BackendClient("http://localhost:8000", 20, "/chat", "/health")
    with pytest.raises(BackendResponseError):
        client.chat("x")


def test_backend_client_connection_error(monkeypatch):
    def fake_request(self, method, url, json_payload=None):
        raise httpx.ConnectError("cannot connect")

    monkeypatch.setattr("src.services.backend_client.BackendClient._request", fake_request)

    client = BackendClient("http://localhost:8000", 20, "/chat", "/health")
    with pytest.raises(BackendConnectionError):
        client.chat("hello")