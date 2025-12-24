import asyncio
import datetime
import uuid
from typing import Any, get_args

import gotrue
import gotrue.errors
import gotrue.helpers
import postgrest
import psycopg
from argon2 import PasswordHasher
from fastapi_lifespan_manager import LifespanManager
from gotrue.constants import STORAGE_KEY as DEFAULT_STORAGE_KEY
from pydantic import Field
from storage3.constants import DEFAULT_TIMEOUT as DEFAULT_STORAGE_CLIENT_TIMEOUT
from supabase.client import AsyncClient as NativeSupabaseAsyncClient
from supabase.client import AsyncSupabaseAuthClient as NativeSupabaseAuthAsyncClient

# AsyncAuthClient as NativeSupabaseAuthAsyncClient,
from supabase.client import (
    create_async_client,
)
from supabase.lib.client_options import AsyncClientOptions as NativeSupabaseAsyncClientOptions

from apppy.auth.errors.user import (
    UserSessionInvalidDataError,
    UserSessionRefreshMissingSessionError,
    UserSignInInvalidCredentialsError,
    UserSignInServerError,
    UserSignOutServerError,
    UserSignUpAlreadyExistsError,
    UserSignUpInvalidCredentialsError,
    UserSignUpServerError,
    UserSignUpTooManyRetriesError,
)
from apppy.auth.jwt import JwtAuthContext
from apppy.db.postgres import PostgresClient
from apppy.env import Env, EnvSettings
from apppy.logger import WithLogger


class OAuthSessionStorage(gotrue.AsyncSupportedStorage, WithLogger):
    """
    A storage implementation for Supabase Auth that
    that uses a predefined session and integrates
    natively with OAuth flows.
    """

    def __init__(self, session: dict[str, Any]):
        self._session = session

    async def get_item(self, key: str) -> str | None:
        return self._session.get(key)

    async def set_item(self, key: str, value: str) -> None:
        self._session[key] = value

    async def remove_item(self, key: str) -> None:
        self._session.pop(key, None)


class SupabaseAuthSessionStorage(gotrue.AsyncSupportedStorage, WithLogger):
    """
    A storage implementation for Supabase Auth
    that uses a predefined session and integrates
    natively with the Supabase authentication flow.
    """

    def __init__(self, session_data: dict[str, Any], storage_key: str):
        try:
            session = gotrue.helpers.model_validate(gotrue.Session, session_data)
        except Exception as e:
            raise UserSessionInvalidDataError(session_data) from e

        session_json = gotrue.helpers.model_dump_json(session)
        self._session_storage: dict[str, Any] = {}
        self._session_storage[storage_key] = session_json

    async def get_item(self, key: str) -> str | None:
        return self._session_storage.get(key)

    async def set_item(self, key: str, value: str) -> None:
        self._session_storage[key] = value

    async def remove_item(self, key: str) -> None:
        self._session_storage.pop(key, None)


class SupabaseAuthSettings(EnvSettings):
    # SUPABASE_AUTH_API_ANON_KEY
    api_anon_key: str = Field()
    # SUPABASE_AUTH_API_KEY
    api_key: str = Field(exclude=True)
    # SUPABASE_AUTH_API_URL
    api_url: str = Field()
    # SUPABASE_AUTH_AUTO_REFRESH_TOKEN
    auto_refresh_token: bool = Field(default=True)
    # SUPABASE_AUTH_FLOW_TYPE
    flow_type: gotrue.AuthFlowType = Field(default="pkce")
    # SUPABASE_AUTH_PERSIST_SESSION
    persist_session: bool = Field(default=True)
    # SUPABASE_AUTH_POSTGREST_CLIENT_TIMEOUT
    postgrest_client_timeout: int = Field(
        default=postgrest.constants.DEFAULT_POSTGREST_CLIENT_TIMEOUT
    )
    # SUPABASE_AUTH_MAX_USER_SIGNUP_RETRIES
    max_user_signup_retries: int = Field(default=2)
    # SUPABASE_AUTH_REQUIRE_EMAIL_CONFIRMATION
    require_email_confirmation: bool = Field(default=True)
    # SUPABASE_AUTH_STORAGE_CLIENT_TIMEOUT
    storage_client_timeout: int = Field(default=DEFAULT_STORAGE_CLIENT_TIMEOUT)
    # SUPABASE_AUTH_STORAGE_KEY
    storage_key: str = Field(default=DEFAULT_STORAGE_KEY)

    def __init__(self, env: Env) -> None:
        super().__init__(env=env, domain_prefix="SUPABASE_AUTH")

    async def create_auth_client(
        self,
        client_options: NativeSupabaseAsyncClientOptions,
    ) -> NativeSupabaseAuthAsyncClient:
        native_anon_async_client: NativeSupabaseAsyncClient = await create_async_client(
            supabase_url=self.api_url,
            supabase_key=self.api_anon_key,
            options=client_options,
        )

        return native_anon_async_client.auth

    def _create_client_options(
        self, storage: gotrue.AsyncSupportedStorage | None
    ) -> NativeSupabaseAsyncClientOptions:
        return NativeSupabaseAsyncClientOptions(
            auto_refresh_token=self.auto_refresh_token,
            flow_type=self.flow_type,
            persist_session=(False if storage is None else self.persist_session),
            postgrest_client_timeout=self.postgrest_client_timeout,
            storage=storage
            or gotrue.AsyncMemoryStorage(),  # Use dummy AsyncMemoryStorage if storage is None
            storage_client_timeout=self.storage_client_timeout,
        )

    def client_options_for_oauth(self, session: dict[str, Any]) -> NativeSupabaseAsyncClientOptions:
        """
        Supabase client options specifically for OAuth flows.
        """
        return self._create_client_options(storage=OAuthSessionStorage(session))

    def client_options_with_storage(
        self, session_data: dict[str, Any], storage_key: str | None = None
    ) -> NativeSupabaseAsyncClientOptions:
        return self._create_client_options(
            storage=SupabaseAuthSessionStorage(
                session_data=session_data,
                storage_key=(storage_key if storage_key is not None else self.storage_key),
            )
        )

    def client_options_without_storage(self) -> NativeSupabaseAsyncClientOptions:
        return self._create_client_options(storage=None)


class SupabaseAuthAdmin(WithLogger):
    def __init__(
        self,
        settings: SupabaseAuthSettings,
        lifespan: LifespanManager,
        postgres_client: PostgresClient,
    ):
        self._settings = settings
        self._postgres_client = postgres_client

        lifespan.add(self._auth_admin_async_client)

    async def _auth_admin_async_client(self):
        native_anon_async_client = await create_async_client(
            supabase_url=self._settings.api_url,
            supabase_key=self._settings.api_key,
        )

        self._supabase_auth_admin = native_anon_async_client.auth.admin
        yield {"supbase_auth_admin": self._supabase_auth_admin}

        self._logger.info("Closing Supabase Auth Admin client")
        await self._supabase_auth_admin.close()

    def _normalize_result_row(self, row: dict) -> dict:
        def _normalize_key(key: str):
            if key == "raw_app_meta_data":
                return "app_metadata"
            elif key == "raw_user_meta_data":
                return "user_metadata"

            return key

        return {
            _normalize_key(k): str(v) if isinstance(v, uuid.UUID | datetime.datetime) else v
            for k, v in row.items()
        }

    async def create_user(self, attributes: gotrue.AdminUserAttributes) -> gotrue.User:
        auth_user_query = """
            SELECT *
            FROM auth.users
            WHERE email = %(email)s
            LIMIT 1
        """
        try:
            result_set = await self._postgres_client.db_query_async(
                auth_user_query, {"email": attributes["email"]}
            )

            if result_set is None or len(result_set) != 1:
                user_resp = await self._supabase_auth_admin.create_user(attributes)
                return user_resp.user
            else:
                user_dict = self._normalize_result_row(result_set[0])
                user_resp = gotrue.helpers.parse_user_response(user_dict)
                return user_resp.user
        except psycopg.DatabaseError as e:
            self._logger.exception("Lookup during create user encountered an api error")
            raise UserSignUpServerError("auth_user_lookup_error") from e
        except gotrue.errors.AuthApiError as e:
            if e.code == "user_already_exists":
                self._logger.warning(
                    "Attempted user creation for user that already exists",
                    extra={
                        "email": attributes["email"],
                    },
                )
                raise UserSignUpAlreadyExistsError() from e
            self._logger.exception(
                "Create user encountered an auth api error",
                extra={"error_name": e.name},
            )
            raise UserSignUpServerError(e.code) from e


class SupabaseAuth(WithLogger):
    def __init__(
        self,
        settings: SupabaseAuthSettings,
        supabase_auth_admin: SupabaseAuthAdmin,
    ) -> None:
        self._settings = settings
        self._password_hasher = PasswordHasher()
        self._supabase_auth_admin = supabase_auth_admin

    async def auth_async_client(
        self,
        client_options: NativeSupabaseAsyncClientOptions,
    ) -> NativeSupabaseAuthAsyncClient:
        return await self._settings.create_auth_client(client_options)

    def client_options_with_session(
        self, auth_ctx: JwtAuthContext
    ) -> NativeSupabaseAsyncClientOptions:
        """
        Returns a client options instance that can be used
        with the session information from the given JwtAuthContext.
        """
        session_data = auth_ctx.raw_session
        if session_data is None:
            return self._settings.client_options_without_storage()

        return self._settings.client_options_with_storage(
            session_data=session_data,
        )

    def is_native_supabase_provider(self, provider: str) -> bool:
        return provider in get_args(gotrue.Provider)

    @property
    def require_email_confirmation(self) -> bool:
        return self._settings.require_email_confirmation

    async def user_session_login_id_token(
        self,
        credentials: gotrue.SignInWithIdTokenCredentials,
    ) -> gotrue.AuthResponse:
        try:
            client_options = self._settings.client_options_without_storage()
            auth_async_client: NativeSupabaseAuthAsyncClient = await self.auth_async_client(
                client_options
            )
            auth_resp: gotrue.AuthResponse = await auth_async_client.sign_in_with_id_token(
                credentials
            )

            return auth_resp
        except gotrue.errors.AuthApiError as e:
            self._logger.exception(
                "Login with id token encountered an auth api error",
                extra={"error_name": e.name, "error_code": e.code, "error_message": e.message},
            )
            raise UserSignInServerError(e.code) from e
        except gotrue.errors.CustomAuthError as e:
            self._logger.exception(
                "Login with id token encountered an auth custom error",
                extra={"error_name": e.name, "error_code": e.code, "error_message": e.message},
            )
            raise UserSignInServerError(e.code) from e

    async def user_session_login_oauth_finalize(
        self,
        session: dict[str, Any],
        params: gotrue.CodeExchangeParams,
    ) -> gotrue.AuthResponse:
        try:
            client_options = self._settings.client_options_for_oauth(session)
            auth_async_client: NativeSupabaseAuthAsyncClient = await self.auth_async_client(
                client_options
            )
            auth_resp: gotrue.AuthResponse = await auth_async_client.exchange_code_for_session(
                params
            )

            return auth_resp
        except gotrue.errors.AuthApiError as e:
            self._logger.exception(
                "Oauth login finalize encountered an auth api error",
                extra={"error_name": e.name, "error_code": e.code, "error_message": e.message},
            )
            raise UserSignInServerError(e.code) from e
        except gotrue.errors.CustomAuthError as e:
            self._logger.exception(
                "OAuth login finalize encountered an auth custom error",
                extra={"error_name": e.name, "error_code": e.code, "error_message": e.message},
            )
            raise UserSignInServerError(e.code) from e

    async def user_session_login_oauth(
        self,
        session: dict[str, Any],
        credentials: gotrue.SignInWithOAuthCredentials,
    ) -> gotrue.OAuthResponse:
        try:
            client_options = self._settings.client_options_for_oauth(session)
            auth_async_client: NativeSupabaseAuthAsyncClient = await self.auth_async_client(
                client_options
            )
            oauth_resp: gotrue.OAuthResponse = await auth_async_client.sign_in_with_oauth(
                credentials
            )

            return oauth_resp
        except gotrue.errors.AuthApiError as e:
            self._logger.exception(
                "Login with oauth encountered an auth api error",
                extra={"error_name": e.name, "error_code": e.code, "error_message": e.message},
            )
            raise UserSignInServerError(e.code) from e
        except gotrue.errors.CustomAuthError as e:
            self._logger.exception(
                "Login with oauth encountered an auth custom error",
                extra={"error_name": e.name, "error_code": e.code, "error_message": e.message},
            )
            raise UserSignInServerError(e.code) from e

    async def user_session_login_password(
        self, credentials: gotrue.SignInWithPasswordCredentials
    ) -> gotrue.AuthResponse:
        try:
            client_options = self._settings.client_options_without_storage()
            auth_async_client: NativeSupabaseAuthAsyncClient = await self.auth_async_client(
                client_options
            )
            auth_resp: gotrue.AuthResponse = await auth_async_client.sign_in_with_password(
                credentials
            )

            return auth_resp
        except gotrue.errors.AuthApiError as e:
            if e.message == "Invalid login credentials":
                raise UserSignInInvalidCredentialsError() from e

            self._logger.exception(
                "Login with password encountered an auth api error",
                extra={"error_name": e.name, "error_code": e.code, "error_message": e.message},
            )
            raise UserSignInServerError(e.code) from e
        except gotrue.errors.CustomAuthError as e:
            self._logger.exception(
                "Login with password encountered an auth custom error",
                extra={"error_name": e.name, "error_code": e.code, "error_message": e.message},
            )
            raise UserSignInServerError(e.code) from e

    async def user_session_logout(self, options: gotrue.SignOutOptions) -> None:
        client_options = self._settings.client_options_without_storage()
        auth_async_client: NativeSupabaseAuthAsyncClient = await self.auth_async_client(
            client_options
        )
        try:
            await auth_async_client.sign_out(options)
        except gotrue.errors.AuthError as e:
            self._logger.exception(
                "Logout encountered an auth error",
                extra={"error_name": e.name, "error_code": e.code, "error_message": e.message},
            )
            raise UserSignOutServerError(e.code) from e

    async def user_session_refresh(self, refresh_token: str) -> gotrue.AuthResponse:
        try:
            client_options = self._settings.client_options_without_storage()
            auth_async_client: NativeSupabaseAuthAsyncClient = await self.auth_async_client(
                client_options
            )
            auth_resp: gotrue.AuthResponse = await auth_async_client.refresh_session(refresh_token)
            return auth_resp
        except gotrue.errors.AuthSessionMissingError as e:
            raise UserSessionRefreshMissingSessionError() from e

    async def user_sign_up(
        self, credentials: gotrue.SignUpWithPasswordCredentials
    ) -> gotrue.AuthResponse:
        attempt = 0
        while attempt < self._settings.max_user_signup_retries:
            try:
                client_options = self._settings.client_options_without_storage()
                auth_async_client = await self.auth_async_client(client_options)
                auth_resp: gotrue.AuthResponse = await auth_async_client.sign_up(credentials)
                return auth_resp
            except gotrue.errors.AuthRetryableError:
                self._logger.warning(
                    "Encountered an AuthRetryableError with signing up a Supabase user. Retrying.",
                    extra={
                        "attempt": attempt,
                        "email": credentials.get("email"),
                        "phone": credentials.get("phone"),
                    },
                )
                attempt += 1
                await asyncio.sleep(0.5)
            except gotrue.errors.AuthInvalidCredentialsError as e:
                self._logger.exception(
                    e.message,
                    extra={"email": credentials.get("email"), "phone": credentials.get("phone")},
                )
                raise UserSignUpInvalidCredentialsError() from e
            except gotrue.errors.AuthApiError as e:
                if e.code == "user_already_exists":
                    self._logger.warning(
                        "Attempted sign up of user that already exists",
                        extra={
                            "email": credentials.get("email"),
                            "phone": credentials.get("phone"),
                        },
                    )
                    raise UserSignUpAlreadyExistsError() from e
                self._logger.exception(
                    "Sign up encountered an auth api error",
                    extra={"email": credentials.get("email"), "phone": credentials.get("phone")},
                )
                raise UserSignUpServerError(e.code) from e

        self._logger.error(
            "Too many retry attempts to sign up a Supabase user",
            extra={
                "attempts": attempt,
                "email": credentials.get("email"),
                "phone": credentials.get("phone"),
            },
        )
        raise UserSignUpTooManyRetriesError()

    async def user_sign_up_id_token(
        self,
        provider: str,
        attributes: gotrue.AdminUserAttributes,
    ) -> None:
        user: gotrue.User = await self._supabase_auth_admin.create_user(attributes)
        if user is None:
            raise UserSignUpServerError("user_creation_failed_in_sign_up_id_token")
