from _typeshed import Incomplete
from google.auth import credentials as credentials, crypt as crypt, exceptions as exceptions

IAM_RETRY_CODES: Incomplete

class Signer(crypt.Signer):
    def __init__(self, request, credentials, service_account_email) -> None: ...
    @property
    def key_id(self) -> None: ...
    def sign(self, message): ...
