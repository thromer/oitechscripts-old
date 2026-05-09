from dataclasses import dataclass
from google.auth import exceptions as exceptions

@dataclass(frozen=True)
class PublicKeyCredentialDescriptor:
    id: str
    transports: list[str] | None = ...
    def to_dict(self): ...

@dataclass
class AuthenticationExtensionsClientInputs:
    appid: str | None = ...
    def to_dict(self): ...

@dataclass
class GetRequest:
    origin: str
    rpid: str
    challenge: str
    timeout_ms: int | None = ...
    allow_credentials: list[PublicKeyCredentialDescriptor] | None = ...
    user_verification: str | None = ...
    extensions: AuthenticationExtensionsClientInputs | None = ...
    def to_json(self) -> str: ...

@dataclass(frozen=True)
class AuthenticatorAssertionResponse:
    client_data_json: str
    authenticator_data: str
    signature: str
    user_handle: str | None

@dataclass(frozen=True)
class GetResponse:
    id: str
    response: AuthenticatorAssertionResponse
    authenticator_attachment: str | None
    client_extension_results: dict | None
    @staticmethod
    def from_json(json_str: str): ...
