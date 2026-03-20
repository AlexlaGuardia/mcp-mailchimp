"""Async Mailchimp Marketing API client."""

import hashlib
from typing import Any

import httpx


class MailchimpError(Exception):
    """Mailchimp API error with status code and details."""

    def __init__(self, title: str, detail: str, status: int):
        self.title = title
        self.detail = detail
        self.status = status
        super().__init__(f"{status} {title}: {detail}")


class MailchimpClient:
    """Lightweight async client for the Mailchimp Marketing API v3."""

    def __init__(self, api_key: str):
        if "-" not in api_key:
            raise ValueError(
                "Invalid API key format. Expected: xxxxxxxxxx-usXX"
            )
        self.api_key = api_key
        self.dc = api_key.rsplit("-", 1)[-1]
        self.base_url = f"https://{self.dc}.api.mailchimp.com/3.0"
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            auth=("apikey", api_key),
            headers={"Accept": "application/json"},
            timeout=30.0,
        )

    @staticmethod
    def subscriber_hash(email: str) -> str:
        """MD5 hash of lowercase email — Mailchimp's subscriber identifier."""
        return hashlib.md5(email.lower().strip().encode()).hexdigest()

    async def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        resp = await self._client.request(method, path, **kwargs)
        if resp.status_code == 204:
            return {"success": True}
        try:
            data = resp.json()
        except Exception:
            data = {"title": "Parse Error", "detail": resp.text}
        if resp.status_code >= 400:
            raise MailchimpError(
                data.get("title", "Unknown Error"),
                data.get("detail", "No details provided"),
                resp.status_code,
            )
        return data

    async def get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        return await self._request("GET", path, params=params)

    async def post(self, path: str, json: dict[str, Any] | None = None) -> Any:
        return await self._request("POST", path, json=json or {})

    async def patch(self, path: str, json: dict[str, Any]) -> Any:
        return await self._request("PATCH", path, json=json)

    async def put(self, path: str, json: dict[str, Any]) -> Any:
        return await self._request("PUT", path, json=json)

    async def delete(self, path: str) -> Any:
        return await self._request("DELETE", path)

    async def close(self) -> None:
        await self._client.aclose()
