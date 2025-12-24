from apppy.fastql.annotation import fastql_type_error
from apppy.fastql.errors import GraphQLServerError


@fastql_type_error
class MissingUserIdentityError(GraphQLServerError):
    """Error raised when a user's identity is missing"""

    def __init__(self) -> None:
        super().__init__("missing_user_identity")


@fastql_type_error
class UserIdentityServerError(GraphQLServerError):
    """Error raised when a user identity flow encountered an error on the server side"""

    def __init__(self, code: str) -> None:
        super().__init__(code)
