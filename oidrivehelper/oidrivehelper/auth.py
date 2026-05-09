import functools
from typing import TYPE_CHECKING, cast

import google_auth_oauthlib.flow
from flask import Blueprint, current_app, redirect, request, session, url_for


if TYPE_CHECKING:
    from collections.abc import Callable

    from flask.typing import ResponseValue


bp = Blueprint("auth", __name__, url_prefix="/auth")


SCOPES = [
    #    "https://www.googleapis.com/auth/drive",
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
        _get_client_secrets_config(), scopes=SCOPES
    )
    flow.redirect_uri = url_for("auth.oauth2callback", _external=True)
    authorization_url, state = flow.authorization_url(
        # access_type="offline"
        # include_granted_scopes="true",
    )
    session["code_verifier"] = cast(str, flow.code_verifier)
    session["state"] = state
    return redirect(authorization_url)


@bp.route("/oauth2callback")
def oauth2callback() -> ResponseValue:
    state = cast(str, session["state"])
    flow = google_auth_oauthlib.flow.Flow.from_client_config(
        _get_client_secrets_config(),
        scopes=SCOPES,
        state=state,
        code_verifier=cast(str, session["code_verifier"]),
    )
    flow.redirect_uri = url_for("auth.oauth2callback", _external=True)

    authorization_response = request.url
    _ = flow.fetch_token(authorization_response=authorization_response)

    credentials = flow.credentials
    session["credentials"] = {
        "token": credentials.token,
        "refresh_token": credentials.refresh_token,
        "token_uri": credentials.token_uri,
        "client_id": credentials.client_id,
        "client_secret": credentials.client_secret,
        "scopes": credentials.scopes,
    }

    return redirect(cast(str, session.get("next")) or "/")


def auth_required[**P, R: ResponseValue](view: Callable[P, R]) -> Callable[P, R]:
    @functools.wraps(view)
    def wrapped_view(*args: P.args, **kwargs: P.kwargs) -> R:
        if "credentials" not in session:
            print("wrapped_view getting credentials")
            session["next"] = request.full_path
            return cast(R, redirect(url_for("auth.authorize", _external=False)))
        print("wrapped_view returning")
        return view(*args, **kwargs)

    return wrapped_view
