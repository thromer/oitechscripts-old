from collections.abc import Sequence

import google.auth.credentials
import google.auth.transport
from google.auth import environment_vars as environment_vars
from google.auth import exceptions as exceptions

def load_credentials_from_file(
    filename, scopes=None, default_scopes=None, quota_project_id=None, request=None
): ...
def load_credentials_from_dict(
    info, scopes=None, default_scopes=None, quota_project_id=None, request=None
): ...
def get_api_key_credentials(key): ...
def default(
    scopes: Sequence[str] | None = None,
    request: google.auth.transport.Request | None = None,
    quota_project_id: str | None = None,
    default_scopes: Sequence[str] | None = None,
) -> tuple[google.auth.credentials.Credentials, str | None]: ...
