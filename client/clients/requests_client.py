import json
from typing import Optional, Dict, Any, List

import requests


AUTH_HEADERS = {
    "Authorization": "Bearer test-token",
}


class RequestsUserClient:
    def __init__(self, base_url: str = "http://localhost:3100/users"):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()

    def _request(
        self,
        method: str,
        path: str = "",
        json_body: Optional[Dict[str, Any]] = None,
    ) -> Optional[Any]:
        url = f"{self.base_url}{path}"
        headers = dict(AUTH_HEADERS)
        if json_body is not None:
            headers["Content-Type"] = "application/json"

        try:
            resp = self.session.request(
                method=method,
                url=url,
                json=json_body,
                headers=headers,
                timeout=5,
            )
            if resp.status_code in (200, 201):
                if resp.text:
                    return resp.json()
                return None
            if resp.status_code == 204:
                return None
            print(f"[requests] HTTP {resp.status_code} on {method} {url}: {resp.text[:200]}")
            return None
        except requests.RequestException as e:
            print(f"[requests] error on {method} {url}: {e}")
            return None

    def create_user(self, user_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        return self._request("POST", "", user_data)

    def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        return self._request("GET", f"/{user_id}")

    def get_all_users(self) -> Optional[List[Dict[str, Any]]]:
        result = self._request("GET", "")
        if isinstance(result, list):
            return result
        return None

    def update_user(self, user_id: str, user_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        return self._request("PUT", f"/{user_id}", user_data)

    def delete_user(self, user_id: str) -> bool:
        _ = self._request("DELETE", f"/{user_id}")
        return True

    def close(self) -> None:
        self.session.close()

