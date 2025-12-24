import aiohttp

class GoidaHetaAPIClient:
    API_PREFIX = "/api/v1"
    def __init__(self, base_url: str, token: str):
        cleaned_url = base_url.rstrip('/')
        if not cleaned_url.endswith(self.API_PREFIX):
            self.base_url = cleaned_url + self.API_PREFIX
        else:
            self.base_url = cleaned_url
        self.client = aiohttp.ClientSession()
        self.token = token
        if not self.token:
            raise ValueError("Token required!")
        # перенес imports сюда, чтобы сделать их де-факто приватными
        from .api.auth.api import AuthAPI
        from .api.modules.api import ModulesAPI
        from .api.checker.api import CheckerAPI
        from .api.logger.api import LoggerAPI
        from .api.repos.api import ReposAPI
        from .api.ai.api import GoidaAIAPI
        from .api.service.api import ServiceAPI

        self.ai = GoidaAIAPI(self.client, token=self.token, base_url=self.base_url)        
        self.auth = AuthAPI(self.client, token=self.token, base_url=self.base_url)
        self.checker = CheckerAPI(self.client, token=self.token, base_url=self.base_url)
        self.modules = ModulesAPI(self.client, token=self.token, base_url=self.base_url)
        self.logger = LoggerAPI(self.client, token=self.token, base_url=self.base_url)
        self.repos = ReposAPI(self.client,token=self.token, base_url=self.base_url)
        self.ai = GoidaAIAPI(self.client, token=self.token, base_url=self.base_url)
        self.service = ServiceAPI(self.client, token=self.token, base_url=self.base_url)

    async def close(self):
        if not self.client.closed:
            await self.client.close()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

