import wsgiref.simple_server
from collections.abc import Callable, Mapping, Sequence

import requests_oauthlib
from _typeshed import Incomplete
from google.oauth2.credentials import Credentials

class Flow:
    client_type: Incomplete
    client_config: Incomplete
    oauth2session: Incomplete
    code_verifier: Incomplete
    autogenerate_code_verifier: Incomplete
    def __init__(
        self,
        oauth2session: requests_oauthlib.OAuth2Session,
        client_type: str,
        client_config: Mapping[str, Mapping[str, str]],  # Source says Mapping[str, Any]
        redirect_uri: str | None = ...,
        code_verifier: str | None = ...,
        autogenerate_code_verifier: bool = True,
    ) -> None: ...
    @classmethod
    def from_client_config(
        cls,
        client_config: Mapping[str, Mapping[str, str]],  # Source says Mapping[str, Any]
        scopes: Sequence[str],
        state: str | Callable[[], str] | None = ...,
        code_verifier: str | None = ...,
    ) -> Flow: ...
    @classmethod
    def from_client_secrets_file(cls, client_secrets_file, scopes, **kwargs): ...
    @property
    def redirect_uri(self): ...
    @redirect_uri.setter
    def redirect_uri(self, value) -> None: ...
    def authorization_url(
        self, access_type: str | None = ..., include_granted_scopes: bool | None = ...
    ) -> tuple[str, str]: ...
    def fetch_token(
        self, authorization_response: str | None = ...
    ) -> Mapping[str, str]: ...
    @property
    def credentials(self) -> Credentials: ...
    def authorized_session(self): ...

class InstalledAppFlow(Flow):
    redirect_uri: Incomplete
    def run_local_server(
        self,
        host: str = "localhost",
        bind_addr=None,
        port: int = 8080,
        authorization_prompt_message=...,
        success_message=...,
        open_browser: bool = True,
        redirect_uri_trailing_slash: bool = True,
        timeout_seconds=None,
        token_audience=None,
        browser=None,
        **kwargs,
    ): ...

class _WSGIRequestHandler(wsgiref.simple_server.WSGIRequestHandler):
    def log_message(self, format, *args) -> None: ...

class _RedirectWSGIApp:
    last_request_uri: Incomplete
    def __init__(self, success_message) -> None: ...
    def __call__(self, environ, start_response): ...

class WSGITimeoutError(AttributeError): ...
