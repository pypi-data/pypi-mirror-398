import time

import pytest
from supabase.client import AsyncSupabaseAuthClient as NativeSupabaseAuthAsyncClient

from apppy.auth.errors.user import UserSessionInvalidDataError
from apppy.env import Env
from apppy.env.fixtures import env_ci  # noqa: F401
from apppy.sb.auth import SupabaseAuthSettings


async def test_client_options_with_storage_invalid_model(env_ci: Env):  # noqa: F811
    settings = SupabaseAuthSettings(env=env_ci)

    with pytest.raises(UserSessionInvalidDataError):
        settings.client_options_with_storage(session_data={"my_session_key": "my_session_value"})


async def test_client_options_without_storage(env_ci: Env):  # noqa: F811
    settings = SupabaseAuthSettings(env=env_ci)
    client_options = settings.client_options_without_storage()

    # Assert that we cannot read the session back using the
    # default supabase storage key
    session = await client_options.storage.get_item("supabase.auth.token")
    assert session is None


async def test_gotrue_client_get_session(env_ci: Env):  # noqa: F811
    settings = SupabaseAuthSettings(env=env_ci)
    client_options = settings.client_options_with_storage(
        session_data={
            "access_token": "my_access_token",
            "refresh_token": "my_refresh_token",
            "expires_at": int(time.time()) + 15 * 60,
            "expires_in": 900,
            "token_type": "Bearer",
            "user": {
                "id": "my_user_id",
                "app_metadata": {},
                "user_metadata": {},
                "aud": "authenticated",
                "created_at": "2024-02-28T15:04:05Z",
            },
        },
    )

    auth_client: NativeSupabaseAuthAsyncClient = await settings.create_auth_client(client_options)

    # Assert that we can read the session back
    session = await auth_client.get_session()
    assert session is not None
    assert session.access_token == "my_access_token"
    assert session.refresh_token == "my_refresh_token"
