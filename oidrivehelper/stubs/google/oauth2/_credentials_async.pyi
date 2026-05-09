from _typeshed import Incomplete
from google.auth import exceptions as exceptions
from google.oauth2 import credentials as oauth2_credentials

class Credentials(oauth2_credentials.Credentials):
    token: Incomplete
    expiry: Incomplete
    async def refresh(self, request) -> None: ...
    async def before_request(self, request, method, url, headers) -> None: ...

class UserAccessTokenCredentials(oauth2_credentials.UserAccessTokenCredentials): ...
