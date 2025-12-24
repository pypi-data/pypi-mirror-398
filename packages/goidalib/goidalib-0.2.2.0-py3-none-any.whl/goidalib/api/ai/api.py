import aiohttp
from typing import Optional

class GoidaAIAPI:
    def __init__(self, client: aiohttp.ClientSession, token: str, base_url: str):
        self._client = client
        self.token = token
        self.base_url = base_url

    async def sync(self):
        """Sync AI database"""
        params = {
            "token": self.token,
        }
        async with self._client.post(f"{self.base_url}/ai/sync", params=params) as response:
            data = await response.json()
            return data