import aiohttp
from typing import Optional

class AuthAPI:
    def __init__(self, client: aiohttp.ClientSession, token: str, base_url: str):
        self._client = client
        self.token = token
        self.base_url = base_url

    async def generate_token(self, tg_id: int):
        """(Re)Generate token for user"""
        params = {
            "token": self.token,
            "tg_id": tg_id,
        }
        async with self._client.post(f"{self.base_url}/auth/gen-token", params=params) as response:
            data = await response.json()
            return data
    
    async def get_user(self, tg_id: int):
        """Returns user info"""
        params = {
            "token": self.token,
            "tg_id": tg_id,
        }
        async with self._client.get(f"{self.base_url}/auth/get-user", params=params) as response:
            data = await response.json()
            return data
    
    async def get_me(self):
        """Returns info about current user"""
        params = {
            "token": self.token,
        }
        async with self._client.get(f"{self.base_url}/auth/get_me", params=params) as response:
            data = await response.json()
            return data