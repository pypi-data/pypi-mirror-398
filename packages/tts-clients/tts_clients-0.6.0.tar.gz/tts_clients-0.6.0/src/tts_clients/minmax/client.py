import os
from typing import Any

import httpx
from pydantic import BaseModel

from .models import TextToAudioRequest, TextToAudioResponse


_DEFAULT_HOST = "https://api.minimaxi.chat/v1"


def _default_headers(api_key: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}


class MiniMaxT2AClient:
    """
    MiniMax T2A v2 Client
    """
    def __init__(
        self,
        api_key: str | None = None,
        group_id: str | None = None,
        host: str = _DEFAULT_HOST,
        *,
        httpx_client: httpx.Client | None = None,
        timeout: float = 60.0,
    ) -> None:
        self._api_key = api_key or os.environ.get("MINIMAX_API_KEY")
        self._group_id = group_id or os.environ.get("MINIMAX_GROUP_ID")
        self._base_url = host.rstrip("/")
        self._timeout = timeout
        self._client = httpx_client

    def text_to_audio(self, req: TextToAudioRequest) -> TextToAudioResponse:
        return self._run_sync(
            "t2a_v2",
            req.model_dump(exclude_none=True),
            TextToAudioResponse,
        )

    def _endpoint(self, path: str) -> str:
        return f"{self._base_url}/{path}?GroupId={self._group_id}"

    def _run_sync(self, path: str, body: dict[str, Any], model: type[BaseModel]):
        client = self._client or httpx.Client(timeout=self._timeout)
        try:
            r = client.post(
                self._endpoint(path),
                headers=_default_headers(self._api_key),
                json=body,
            )
            r.raise_for_status()
            return model.model_validate(r.json())
        finally:
            if not self._client:
                client.close()
