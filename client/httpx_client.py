import httpx
import asyncio
from typing import Optional, Dict, Any, List

class HttpxUserClient:
    def __init__(self, base_url: str = "http://localhost:3000"):
        self.base_url = base_url.rstrip('/')
        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer mock-token'
        }
    
    async def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        async with httpx.AsyncClient() as client:
            response = await client.request(
                method=method,
                url=url,
                json=data,
                headers=self.headers
            )
            
            if response.status_code >= 400:
                raise Exception(f"HTTP Error {response.status_code}: {response.text}")
            
            return response.json() if response.text else {}
    
    async def get_all_users(self) -> List[Dict[str, Any]]:
        return await self._make_request('GET', 'users')
    
    async def get_user(self, user_id: str) -> Dict[str, Any]:
        return await self._make_request('GET', f'users/{user_id}')
    
    async def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        return await self._make_request('POST', 'users', user_data)
    
    async def update_user(self, user_id: str, user_data: Dict[str, Any]) -> Dict[str, Any]:
        return await self._make_request('PUT', f'users/{user_id}', user_data)
    
    async def delete_user(self, user_id: str) -> Dict[str, Any]:
        return await self._make_request('DELETE', f'users/{user_id}')


async def demo_httpx_client():
    client = HttpxUserClient()
    
    try:
        users = await client.get_all_users()
        print(f"Всего пользователей: {len(users)}")
        
        if users:
            first_user = await client.get_user(users[0]['id'])
            print(f"Первый пользователь: {first_user}")
            
            new_user = await client.create_user({
                "username": "new_user",
                "email": "new@example.com"
            })
            print(f"Создан пользователь: {new_user}")
            
            updated_user = await client.update_user(new_user['id'], {
                "username": "updated_user"
            })
            print(f"Обновленный пользователь: {updated_user}")
            
            delete_result = await client.delete_user(new_user['id'])
            print(f"Результат удаления: {delete_result}")
            
    except Exception as e:
        print(f"Ошибка: {e}")
