from typing import Optional, Dict, Any, List

import httpx


AUTH_HEADERS = {
    "Authorization": "Bearer test-token",
}


class HttpxUserClient:
    def __init__(self, base_url: str = "http://localhost:3100/users"):
        self.base_url = base_url.rstrip("/")
        self._client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self) -> "HttpxUserClient":
        self._client = httpx.AsyncClient(timeout=5.0)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None

    async def _ensure_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=5.0)
        return self._client

    async def _request(
        self,
        method: str,
        path: str = "",
        json_body: Optional[Dict[str, Any]] = None,
    ) -> Optional[Any]:
        client = await self._ensure_client()
        url = f"{self.base_url}{path}"
        headers = dict(AUTH_HEADERS)
        if json_body is not None:
            headers["Content-Type"] = "application/json"

        try:
            resp = await client.request(
                method=method,
                url=url,
                json=json_body,
                headers=headers,
            )
            if resp.status_code in (200, 201):
                if resp.text:
                    return resp.json()
                return None
            if resp.status_code == 204:
                return None
            print(f"[httpx] HTTP {resp.status_code} on {method} {url}: {resp.text[:200]}")
            return None
        except httpx.RequestError as e:
            print(f"[httpx] error on {method} {url}: {e}")
            return None

    async def create_user(self, user_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        return await self._request("POST", "", user_data)

    async def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        return await self._request("GET", f"/{user_id}")

    async def get_all_users(self) -> Optional[List[Dict[str, Any]]]:
        result = await self._request("GET", "")
        if isinstance(result, list):
            return result
        return None

    async def update_user(self, user_id: str, user_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        return await self._request("PUT", f"/{user_id}", user_data)

    async def delete_user(self, user_id: str) -> bool:
        _ = await self._request("DELETE", f"/{user_id}")
        return True

