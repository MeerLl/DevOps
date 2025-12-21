import json
import urllib.request
import urllib.error
from typing import Optional, Dict, Any, List
from contextlib import closing


AUTH_HEADERS = {
    "Authorization": "Bearer test-token",
}


class UrllibUserClient:
    def __init__(self, base_url: str = "http://localhost:3100/users"):
        self.base_url = base_url.rstrip("/")

    def _request(
        self,
        method: str,
        path: str = "",
        data: Optional[Dict[str, Any]] = None,
    ) -> Optional[Any]:
        url = f"{self.base_url}{path}"
        body_bytes = None
        headers = dict(AUTH_HEADERS)

        if data is not None:
            body_bytes = json.dumps(data).encode("utf-8")
            headers["Content-Type"] = "application/json"

        req = urllib.request.Request(
            url,
            data=body_bytes,
            method=method,
            headers=headers,
        )

        try:
            with closing(urllib.request.urlopen(req)) as resp:
                raw = resp.read().decode("utf-8") or ""
                if not raw:
                    return None
                return json.loads(raw)
        except urllib.error.HTTPError as e:
            if e.code in (200, 204):
                return None
            print(f"[urllib] HTTP error {e.code} on {method} {url}: {e}")
            return None
        except urllib.error.URLError as e:
            print(f"[urllib] URL error on {method} {url}: {e}")
            return None
        except json.JSONDecodeError as e:
            print(f"[urllib] JSON decode error on {method} {url}: {e}")
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

