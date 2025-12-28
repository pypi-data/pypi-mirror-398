from __future__ import annotations

import asyncio
from typing import Any, Mapping

import httpx

from .metadata import WolvesMetadataProvider
from .types import InitializeResponse, WolvesEvent, WolvesUser, build_ingest_event

RETRYABLE_CODES = {408, 500, 502, 503, 504, 522, 524, 599}

API_DEV = "https://wolves-nova-dev.azurewebsites.net/api"


class Network:
    def __init__(self, sdk_key: str, api: str = API_DEV) -> None:
        self._sdk_key = sdk_key
        self._api = api.rstrip("/")
        self._client = httpx.AsyncClient(timeout=httpx.Timeout(10.0))

    async def aclose(self) -> None:
        await self._client.aclose()

    def _headers(self) -> dict[str, str]:
        return {"Content-Type": "application/json", "wolves-api-key": self._sdk_key}

    async def fetch_config(
        self,
        user: WolvesUser,
        since_time: int | None = None,
        *,
        retries: int = 2,
        backoff: float = 1.0,
    ) -> InitializeResponse | None:
        body: dict[str, Any] = {"user": user.to_api_dict()}
        if since_time:
            body["sinceTime"] = since_time

        delay = backoff
        attempt = 0
        while attempt <= retries:
            try:
                resp = await self._client.post(
                    f"{self._api}/events/initialize",
                    headers=self._headers(),
                    json=body,
                )
                if resp.status_code >= 400:
                    if resp.status_code in RETRYABLE_CODES and attempt < retries:
                        await asyncio.sleep(delay)
                        delay *= 2
                        attempt += 1
                        continue
                    raise RuntimeError(f"Failed to fetch config: {resp.status_code} {resp.reason_phrase}")
                data = resp.json()
                if not isinstance(data, Mapping):
                    raise ValueError("Initialize response is not an object")
                return InitializeResponse.from_api_dict(data)
            except Exception as e:
                if attempt >= retries:
                    break
                await asyncio.sleep(delay)
                delay *= 2
                attempt += 1

        return None

    async def send_events(
        self,
        events: list[WolvesEvent],
        *,
        retries: int = 3,
        backoff: float = 1.0,
    ) -> None:
        payload_events = [build_ingest_event(e) for e in events]
        request_body = {"events": payload_events, "wolvesMetadata": WolvesMetadataProvider.get()}

        delay = backoff
        last_error: Exception | None = None
        attempt = 0
        while attempt <= retries:
            try:
                resp = await self._client.post(
                    f"{self._api}/events/ingest/batch",
                    headers=self._headers(),
                    json=request_body,
                )
                if resp.status_code >= 400:
                    if resp.status_code in RETRYABLE_CODES and attempt < retries:
                        await asyncio.sleep(delay)
                        delay *= 2
                        attempt += 1
                        continue
                    raise RuntimeError(f"Failed to log events: {resp.status_code} {resp.reason_phrase}")
                return
            except Exception as e:
                last_error = e
                if attempt >= retries:
                    break
                await asyncio.sleep(delay)
                delay *= 2
                attempt += 1

        if last_error is None:
            raise ValueError("retries must be >= 0")
        raise last_error
