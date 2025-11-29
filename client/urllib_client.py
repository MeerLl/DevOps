import urllib.request
import urllib.parse
import json
from typing import Optional, Dict, Any

class UrllibUserClient:
    def __init__(self, base_url: str = "http://localhost:3000"):
        self.base_url = base_url.rstrip('/')
        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer mock-token' 
        }
    
    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        if data:
            data_bytes = json.dumps(data).encode('utf-8')
        else:
            data_bytes = None
        
        req = urllib.request.Request(
            url,
            data=data_bytes,
            method=method,
            headers=self.headers
        )
        
        try:
            with urllib.request.urlopen(req) as response:
                response_data = response.read().decode('utf-8')
                return json.loads(response_data) if response_data else {}
        except urllib.error.HTTPError as e:
            error_data = e.read().decode('utf-8')
            raise Exception(f"HTTP Error {e.code}: {error_data}")
    
    def get_all_users(self) -> list:
        return self._make_request('GET', 'users')
    
    def get_user(self, user_id: str) -> Dict[str, Any]:
        return self._make_request('GET', f'users/{user_id}')
    
    def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        return self._make_request('POST', 'users', user_data)
    
    def update_user(self, user_id: str, user_data: Dict[str, Any]) -> Dict[str, Any]:
        return self._make_request('PUT', f'users/{user_id}', user_data)
    
    def delete_user(self, user_id: str) -> Dict[str, Any]:
        return self._make_request('DELETE', f'users/{user_id}')