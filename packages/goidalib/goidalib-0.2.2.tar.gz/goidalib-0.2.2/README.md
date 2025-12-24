# This library is for GoidaHeta project. GoidaHeta currently in development.

### Example usage:
```py

from goidalib import GoidaHetaAPIClient
import asyncio

async def main():
    async with GoidaHetaAPIClient(base_url="http://localhost:8000",token="your_token_here") as client:
        # Example usage of the AuthAPI
        user_info = await client.auth.get_user(tg_id=123456789)
        print("User Info:", user_info)

if __name__ == "__main__":
    asyncio.run(main())

```
