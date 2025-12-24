from functools import lru_cache
from fastapi import Request
from src.config import Settings
from src.business.context import ServiceContext
from src.providers.factory import ProviderFactory

@lru_cache()
def get_settings() -> Settings:
    return Settings()

async def get_context(request: Request) -> ServiceContext:
    return request.app.state.context
