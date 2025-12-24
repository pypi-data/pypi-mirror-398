import aiohttp
from typing import Optional

class ReposAPI:
    def __init__(self, client: aiohttp.ClientSession, token: str, base_url: str):
        self._client = client
        self.token = token
        self.base_url = base_url

    async def add_repo(self, url: str):
        """Suggest repo(add repo if admin)"""
        payload = {
            "url": url,
            "token": self.token
        }
        async with self._client.post(f"{self.base_url}/repos/add", params=payload) as response:
            data = await response.json()
            return data

    async def remove_repo(self, url: str, reason: None | str = None):
        """Remove repo(ADMIN ONLY)"""
        payload = {
            "url": url,
            "token": self.token,
        }
        if reason:
            payload["reason"] = reason
        
        async with self._client.delete(f"{self.base_url}/repos/remove", params=payload) as response:
            data = await response.json()
            return data
    
    async def scan(self):
        """Rescan repos for new modules(ADMIN ONLY)"""
        payload = {
            "token": self.token
        }

        data = []
        async with self._client.get(f"{self.base_url}/repos/scan", params=payload) as response:
            async for line in response.content:
                if line:
                    line_str = line.decode('utf-8').strip()
                    if line_str.startswith("data: "):
                        data.append(line_str[6:])
            
            return data