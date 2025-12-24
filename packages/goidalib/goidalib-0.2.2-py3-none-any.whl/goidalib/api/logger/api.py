import aiohttp
from typing import Optional

class LoggerAPI:
    def __init__(self, client: aiohttp.ClientSession, token: str, base_url: str):
        self._client = client
        self.token = token
        self.base_url = base_url

    async def get_logs(self):
        """Get actual logs(ADMIN ONLY)"""
        payload = {
            "token": self.token
        }
        async with self._client.get(f"{self.base_url}/logger/logs", params=payload) as response:
            data = await response.text()
            return data