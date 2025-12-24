import aiohttp
from typing import Optional

class CheckerAPI:
    def __init__(self, client: aiohttp.ClientSession, token: str, base_url: str):
        self._client = client
        self.token = token
        self.base_url = base_url

    async def verdict(self, source: str, hash: str, status: str, reason: Optional[str] = None):
        """Set verfict for something(ADMIN ONLY)"""
        payload = {
            "token": self.token,
            "source": source,
            "hash": hash,
            "status": status,
            "reason": reason,
        }
        async with self._client.post(f"{self.base_url}/checker/verdict", params=payload) as response:
            data = await response.json()
            return data