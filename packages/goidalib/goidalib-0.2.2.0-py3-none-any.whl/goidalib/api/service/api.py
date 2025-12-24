import aiohttp
from typing import Optional

class ServiceAPI:
    def __init__(self, client: aiohttp.ClientSession, token: str, base_url: str):
        self._client = client
        self.token = token
        self.base_url = base_url
    
    async def get_status(self):
        """Get service status"""
        async with self._client.get(f"{self.base_url}/check_status") as response:
            data = await response.json()
            return data

    async def update(self):
        """Update service"""
        params = {
            "token": self.token,
        }
        async with self._client.post(f"{self.base_url}/service/update", params=params) as response:
            data = await response.json()
            return data