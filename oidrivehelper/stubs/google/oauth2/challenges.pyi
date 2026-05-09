import abc
from _typeshed import Incomplete
from google.auth import exceptions as exceptions
from google.oauth2 import webauthn_handler_factory as webauthn_handler_factory
from google.oauth2.webauthn_types import AuthenticationExtensionsClientInputs as AuthenticationExtensionsClientInputs, GetRequest as GetRequest, PublicKeyCredentialDescriptor as PublicKeyCredentialDescriptor

REAUTH_ORIGIN: str
SAML_CHALLENGE_MESSAGE: str
WEBAUTHN_TIMEOUT_MS: int

def get_user_password(text): ...

class ReauthChallenge(metaclass=abc.ABCMeta):
    @property
    @abc.abstractmethod
    def name(self): ...
    @property
    @abc.abstractmethod
    def is_locally_eligible(self): ...
    @abc.abstractmethod
    def obtain_challenge_input(self, metadata): ...

class PasswordChallenge(ReauthChallenge):
    @property
    def name(self): ...
    @property
    def is_locally_eligible(self): ...
    def obtain_challenge_input(self, unused_metadata): ...

class SecurityKeyChallenge(ReauthChallenge):
    @property
    def name(self): ...
    @property
    def is_locally_eligible(self): ...
    def obtain_challenge_input(self, metadata): ...

class SamlChallenge(ReauthChallenge):
    @property
    def name(self): ...
    @property
    def is_locally_eligible(self): ...
    def obtain_challenge_input(self, metadata) -> None: ...

AVAILABLE_CHALLENGES: Incomplete
