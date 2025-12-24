from fastapi_lifespan_manager import LifespanManager
from pydantic import Field
from supabase import AsyncClient as NativeSupabaseAsyncClient
from supabase import Client as NativeSupabaseClient
from supabase.client import create_async_client, create_client

from apppy.env import Env, EnvSettings
from apppy.logger import WithLogger

_SUPABASE_MICRO_MAX_CONNS = 200
_SUPABASE_SMALL_MAX_CONNS = 400


class SupabaseClientSettings(EnvSettings):
    # SUPABASE_API_ANON_KEY
    api_anon_key: str = Field()
    # SUPABASE_API_KEY
    api_key: str = Field(exclude=True)
    # SUPABASE_API_URL
    api_url: str = Field()

    def __init__(self, env: Env) -> None:
        super().__init__(env=env, domain_prefix="SUPABASE")


class SupabaseClient(WithLogger):
    def __init__(
        self,
        settings: SupabaseClientSettings,
        lifespan: LifespanManager | None,
    ) -> None:
        self._settings = settings
        self._native_internal_client: NativeSupabaseClient = create_client(
            supabase_url=settings.api_url, supabase_key=settings.api_key
        )

        if lifespan is not None:
            lifespan.add(self.__create_async_client)

    async def __create_async_client(self):
        self._logger.info("Creating native_internal_async_client")
        self._native_internal_async_client = await create_async_client(
            supabase_url=self._settings.api_url,
            supabase_key=self._settings.api_key,
        )

        yield {"native_internal_async_client": self._native_internal_async_client}

        self._logger.info("Closing native_internal_async_client")

    @property
    def internal_client(self) -> NativeSupabaseClient:
        return self._native_internal_client

    @property
    def internal_async_client(self) -> NativeSupabaseAsyncClient:
        assert self._native_internal_async_client is not None, (
            "Attempting to use internal_async_client when a LifespanManager was never supplied "
            + "(try supplying a LifespanManager or using internal_client)"
        )
        return self._native_internal_async_client
