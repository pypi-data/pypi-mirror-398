from dataclasses import dataclass

import psycopg

# AsyncAuthClient as NativeSupabaseAuthAsyncClient,
from apppy.db.postgres import PostgresClient
from apppy.logger import WithLogger
from apppy.sb.identity.errors import MissingUserIdentityError, UserIdentityServerError


@dataclass
class UserIdentityResponse:
    name: str
    email: str
    phone: str


class SupabaseIdentity(WithLogger):
    def __init__(
        self,
        postgres_client: PostgresClient,
    ) -> None:
        self._postgres_client = postgres_client

    async def user_identity(self, user_id: str):
        auth_user_identity_query = """
            SELECT *
            FROM auth.identities
            WHERE user_id = %(user_id)s
            LIMIT 1
        """
        try:
            result_set = await self._postgres_client.db_query_async(
                auth_user_identity_query, {"user_id": user_id}
            )

            if result_set is not None and len(result_set) == 1:
                return result_set[0]

            raise MissingUserIdentityError()
        except psycopg.DatabaseError as e:
            self._logger.exception("Lookup for user identity encountered an api error")
            raise UserIdentityServerError("auth_user_identity_lookup_error") from e
