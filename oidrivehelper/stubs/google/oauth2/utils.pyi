import abc
import enum
from _typeshed import Incomplete
from google.auth import exceptions as exceptions

class ClientAuthType(enum.Enum):
    basic = 1
    request_body = 2

class ClientAuthentication:
    client_auth_type: Incomplete
    client_id: Incomplete
    client_secret: Incomplete
    def __init__(self, client_auth_type, client_id, client_secret=None) -> None: ...

class OAuthClientAuthHandler(metaclass=abc.ABCMeta):
    def __init__(self, client_authentication=None) -> None: ...
    def apply_client_authentication_options(self, headers, request_body=None, bearer_token=None) -> None: ...

def handle_error_response(response_body) -> None: ...
