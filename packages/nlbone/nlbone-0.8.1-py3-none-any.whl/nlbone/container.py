from __future__ import annotations

from typing import Dict, Optional

from dependency_injector import containers, providers
from pydantic_settings import BaseSettings

from nlbone.adapters.auth.auth_service import AuthService as AuthService_IMP
from nlbone.adapters.auth.token_provider import ClientTokenProvider
from nlbone.adapters.cache.async_redis import AsyncRedisCache
from nlbone.adapters.cache.memory import InMemoryCache
from nlbone.adapters.cache.redis import RedisCache
from nlbone.adapters.db.postgres.engine import get_async_session_factory, get_sync_session_factory
from nlbone.adapters.http_clients import PricingService
from nlbone.adapters.http_clients.uploadchi import UploadchiClient
from nlbone.adapters.http_clients.uploadchi.uploadchi_async import UploadchiAsyncClient
from nlbone.core.ports.auth import AuthService
from nlbone.core.ports.cache import AsyncCachePort, CachePort
from nlbone.core.ports.files import AsyncFileServicePort, FileServicePort


class Container(containers.DeclarativeContainer):
    config = providers.Configuration(strict=False)

    sync_session_factory = providers.Singleton(get_sync_session_factory)
    async_session_factory = providers.Singleton(get_async_session_factory)

    # --- Event bus ---
    # event_bus: providers.Singleton[EventBusPort] = providers.Singleton(InMemoryEventBus)

    # --- Services ---
    auth: providers.Singleton[AuthService] = providers.Singleton(AuthService_IMP)
    token_provider = providers.Singleton(ClientTokenProvider, auth=auth, skew_seconds=30)
    file_service: providers.Singleton[FileServicePort] = providers.Singleton(
        UploadchiClient, token_provider=token_provider
    )
    afiles_service: providers.Singleton[AsyncFileServicePort] = providers.Singleton(
        UploadchiAsyncClient, token_provider=token_provider
    )
    pricing_service: providers.Singleton[PricingService] = providers.Singleton(
        PricingService, token_provider=token_provider
    )

    cache: providers.Singleton[CachePort] = providers.Selector(
        config.CACHE_BACKEND,
        memory=providers.Singleton(InMemoryCache),
        redis=providers.Singleton(RedisCache, url=config.REDIS_URL),
    )

    async_cache: providers.Singleton[AsyncCachePort] = providers.Selector(
        config.CACHE_BACKEND,
        memory=providers.Singleton(InMemoryCache),
        redis=providers.Singleton(AsyncRedisCache, url=config.REDIS_URL),
    )


def create_container(settings: Optional[BaseSettings | Dict] = None) -> Container:
    c = Container()
    if settings is not None:
        if isinstance(settings, BaseSettings):
            c.config.from_pydantic(settings)
        elif isinstance(settings, Dict):
            c.config.from_dict(settings)
    return c
