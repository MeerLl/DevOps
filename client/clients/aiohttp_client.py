from typing import Optional, Dict, Any, List

import aiohttp


AUTH_HEADERS = {
    "Authorization": "Bearer test-token",
}


class AiohttpUserClient:
    def __init__(self, base_url: str = "http://localhost:3100/users"):
        self.base_url = base_url.rstrip("/")
        self._session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self) -> "AiohttpUserClient":
        self._session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5.0))
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        if self._session:
            await self._session.close()
            self._session = None

    async def _ensure_session(self) -> aiohttp.ClientSession:
        if self._session is None:
            self._session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5.0))
        return self._session

    async def _request(
        self,
        method: str,
        path: str = "",
        json_body: Optional[Dict[str, Any]] = None,
    ) -> Optional[Any]:
        session = await self._ensure_session()
        url = f"{self.base_url}{path}"
        headers = dict(AUTH_HEADERS)
        if json_body is not None:
            headers["Content-Type"] = "application/json"

        try:
            async with session.request(
                method=method,
                url=url,
                json=json_body,
                headers=headers,
            ) as resp:
                if resp.status in (200, 201):
                    text = await resp.text()
                    if text:
                        return await resp.json()
                    return None
                if resp.status == 204:
                    return None
                text = await resp.text()
                print(f"[aiohttp] HTTP {resp.status} on {method} {url}: {text[:200]}")
                return None
        except aiohttp.ClientError as e:
            print(f"[aiohttp] error on {method} {url}: {e}")
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

