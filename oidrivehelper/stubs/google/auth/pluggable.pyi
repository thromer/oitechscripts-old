from _typeshed import Incomplete
from google.auth import exceptions as exceptions, external_account as external_account

EXECUTABLE_SUPPORTED_MAX_VERSION: int
EXECUTABLE_TIMEOUT_MILLIS_DEFAULT: Incomplete
EXECUTABLE_TIMEOUT_MILLIS_LOWER_BOUND: Incomplete
EXECUTABLE_TIMEOUT_MILLIS_UPPER_BOUND: Incomplete
EXECUTABLE_INTERACTIVE_TIMEOUT_MILLIS_LOWER_BOUND: Incomplete
EXECUTABLE_INTERACTIVE_TIMEOUT_MILLIS_UPPER_BOUND: Incomplete

class Credentials(external_account.Credentials):
    interactive: Incomplete
    def __init__(self, audience, subject_token_type, token_url, credential_source, *args, **kwargs) -> None: ...
    def retrieve_subject_token(self, request): ...
    def revoke(self, request) -> None: ...
    @property
    def external_account_id(self): ...
    @classmethod
    def from_info(cls, info, **kwargs): ...
    @classmethod
    def from_file(cls, filename, **kwargs): ...
