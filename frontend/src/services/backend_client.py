from __future__ import annotations

import logging
from time import perf_counter

import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from src.core.errors import BackendConnectionError, BackendResponseError
from src.domain.models import ChatResponseModel, HealthModel

logger = logging.getLogger(__name__)


class BackendClient:
    def __init__(self, base_url: str, timeout_seconds: int, chat_path: str, health_path: str):
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.chat_path = chat_path
        self.health_path = health_path

    def _url(self, path: str) -> str:
        normalized = path if path.startswith("/") else f"/{path}"
        return f"{self.base_url}{normalized}"

    @retry(
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.TransportError)),
        wait=wait_exponential(multiplier=0.3, min=0.3, max=2),
        stop=stop_after_attempt(3),
        reraise=True,
    )
    def _request(self, method: str, url: str, json_payload: dict | None = None) -> httpx.Response:
        with httpx.Client(timeout=self.timeout_seconds) as client:
            started = perf_counter()
            response = client.request(method, url, json=json_payload)
            elapsed_ms = int((perf_counter() - started) * 1000)
            logger.info("%s %s -> %s (%sms)", method, url, response.status_code, elapsed_ms)
            return response

    def health(self) -> HealthModel:
        url = self._url(self.health_path)
        try:
            response = self._request("GET", url)
        except (httpx.TimeoutException, httpx.TransportError) as exc:
            raise BackendConnectionError(f"Backend unreachable: {exc}") from exc

        if response.status_code >= 500:
            raise BackendConnectionError(f"Backend health check failed: {response.status_code}")

        try:
            payload = response.json()
            return HealthModel(**payload)
        except Exception as exc:  # noqa: BLE001
            raise BackendResponseError("Invalid health payload") from exc

    def chat(self, question: str) -> ChatResponseModel:
        url = self._url(self.chat_path)
        try:
            response = self._request("POST", url, json_payload={"question": question})
        except (httpx.TimeoutException, httpx.TransportError) as exc:
            raise BackendConnectionError(f"Chat request failed: {exc}") from exc

        if response.status_code == 400:
            detail = response.json().get("detail", "Question invalide")
            raise BackendResponseError(str(detail))
        if response.status_code == 429:
            raise BackendResponseError("Trop de requetes. Reessaie dans 1 minute.")
        if response.status_code == 502:
            raise BackendResponseError("Le modele n'a pas pu generer une reponse.")
        if response.status_code == 503:
            raise BackendResponseError("Service indisponible (index ou LLM).")
        if response.status_code >= 500:
            raise BackendConnectionError(f"Backend error: {response.status_code}")

        try:
            payload = response.json()
            return ChatResponseModel(**payload)
        except Exception as exc:  # noqa: BLE001
            raise BackendResponseError("Invalid chat payload") from exc