import functools
from typing import TYPE_CHECKING, Never, TypedDict, cast

import google_auth_oauthlib.flow
from flask import Blueprint, current_app, g, redirect, request, session, url_for
from google.oauth2.credentials import Credentials


# See https://developers.google.com/identity/protocols/oauth2/web-server


if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from flask.typing import ResponseValue


bp = Blueprint("auth", __name__, url_prefix="/auth")


class CredentialsDict(TypedDict):
    token: str | None
    refresh_token: str | None
    token_uri: str | None
    client_id: str | None
    client_secret: str | None
    scopes: Sequence[str] | None


def credentials_to_dict(credentials: Credentials) -> CredentialsDict:
    return {
        "token": credentials.token,
        "refresh_token": credentials.refresh_token,
        "token_uri": credentials.token_uri,
        "client_id": credentials.client_id,
        "client_secret": credentials.client_secret,
        "scopes": credentials.granted_scopes,
    }


_SCOPES = [
    "https://www.googleapis.com/auth/drive",
    #    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
    "openid",
]


def _get_client_secrets_config() -> dict[str, dict[str, str]]:
    return cast(dict[str, dict[str, str]], current_app.config["CLIENT_SECRETS_CONFIG"])


@bp.route("/authorize")
def authorize() -> ResponseValue:
    flow = google_auth_oauthlib.flow.Flow.from_client_config(
        _get_client_secrets_config(), scopes=_SCOPES
    )
    flow.redirect_uri = url_for("auth.oauth2callback", _external=True)
    authorization_url, state = flow.authorization_url(
        access_type="offline", include_granted_scopes="true", prompt="consent"
    )
    session["code_verifier"] = cast(str, flow.code_verifier)
    session["state"] = state
    return redirect(authorization_url)


@bp.route("/oauth2callback")
def oauth2callback() -> ResponseValue:
    state = cast(str, session["state"])
    flow = google_auth_oauthlib.flow.Flow.from_client_config(
        _get_client_secrets_config(),
        scopes=_SCOPES,
        state=state,
        code_verifier=cast(str, session["code_verifier"]),
    )
    flow.redirect_uri = url_for("auth.oauth2callback", _external=True)

    authorization_response = request.url
    _ = flow.fetch_token(authorization_response=authorization_response)
    credentials = flow.credentials
    granted_scopes = credentials.granted_scopes or []
    missing_scopes = set(_SCOPES).difference(granted_scopes)
    if missing_scopes:
        msg = f"Can't proceed without these scopes: {' '.join(missing_scopes)}"
        raise RuntimeError(msg)

    set_session_credentials(credentials)
    return redirect(cast(str, session.get("next")) or "/")


def get_session_credentials() -> CredentialsDict | dict[str, Never]:
    return cast(CredentialsDict | dict[str, Never], session.get("credentials") or {})


def set_session_credentials(credentials: Credentials) -> None:
    session["credentials"] = credentials_to_dict(credentials)


def auth_required[**P, R: ResponseValue](view: Callable[P, R]) -> Callable[P, R]:
    @functools.wraps(view)
    def wrapped_view(*args: P.args, **kwargs: P.kwargs) -> R:
        credentials_dict = get_session_credentials()
        scopes_granted = set(credentials_dict.get("scopes") or [])
        if not set(_SCOPES).issubset(scopes_granted):
            session["next"] = request.full_path
            return cast(R, redirect(url_for("auth.authorize", _external=False)))
        g.credentials = Credentials.from_authorized_user_info(credentials_dict)
        response = view(*args, **kwargs)
        set_session_credentials(g.credentials)
        return response

    return wrapped_view
