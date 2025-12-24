import aiohttp
from typing import Optional

class ModulesAPI:
    def __init__(self, client: aiohttp.ClientSession, token: str, base_url: str):
        self._client = client
        self.token = token
        self.base_url = base_url
    
    async def get_rate(self, module_id: str):
        """Get rate for module with given id"""
        payload = {
            "module_id": module_id
        }
        async with self._client.get(f"{self.base_url}/modules/rate", params=payload) as response:
            data = await response.json()
            return data
    
    async def rate_module(self, module_id: int, rating: str):
        """Rate module(like or dislike)"""
        val = rating.lower()
        if val not in ["like", "dislike"]:
            raise ValueError("Only like or dislike allowed")
        
        payload = {
            "module_id": module_id,
            "rating": val,
            "token": self.token
        }
        
        async with self._client.post(f"{self.base_url}/modules/rate", params=payload) as response:
            data = await response.json()
            return data
    
    async def search(self, query: str):
        """Search modules by query"""
        payload = {
            "query": query
        }
        async with self._client.get(f"{self.base_url}/modules/search", params=payload) as response:
            data = await response.json()
            return data
    
    async def modules(self):
        """Get all modules(ADMIN ONLY)"""
        payload = {
            "token": self.token
        }
        async with self._client.get(f"{self.base_url}/modules/modules", params=payload) as response:
            data = await response.json()
            return data
    
    async def module(self, module_id: int):
        """Get info about module by module_id"""
        async with self._client.get(f"{self.base_url}/modules/{module_id}") as response:
            data = await response.json()
            return data

    async def rnd(self, count: int):
        """Get random module"""
        payload = {
            "count": count
        }
        async with self._client.get(f"{self.base_url}/modules/rnd", params=payload) as response:
            data = await response.json()
            return data

    async def get_mod(self, path: str):
        """Get module file by path"""
        async with self._client.get(f"{self.base_url}/mod/{path}") as response:
            data = await response.json()
            return data
    async def get_lib(self, path: str):
        """Get library file by path"""
        async with self._client.get(f"{self.base_url}/lib/{path}") as response:
            data = await response.json()
            return data