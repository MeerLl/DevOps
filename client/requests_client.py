import requests
import json
from typing import Optional, Dict, Any

class RequestsUserClient:
    def __init__(self, base_url: str = "http://localhost:3000"):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Authorization': 'Bearer mock-token'
        })
    
    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        response = self.session.request(
            method=method,
            url=url,
            json=data
        )
        
        if response.status_code >= 400:
            raise Exception(f"HTTP Error {response.status_code}: {response.text}")
        
        return response.json() if response.text else {}
    
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