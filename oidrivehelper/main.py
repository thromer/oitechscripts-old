import base64
import json
import os
from pprint import pprint
from typing import TYPE_CHECKING, cast

import flask
import google_auth_oauthlib.flow  # pyright: ignore[reportMissingTypeStubs]
from google.cloud.firestore_v1 import Client as FirestoreClient
from google.cloud.secretmanager_v1 import SecretManagerServiceClient
from google.oauth2 import id_token
from google.oauth2.credentials import Credentials


if TYPE_CHECKING:
    from flask.typing import ResponseValue

SCOPES = [
    #    "https://www.googleapis.com/auth/drive",
    #    "https://www.googleapis.com/auth/gmail.send",
    # "https://www.googleapis.com/auth/userinfo.email",
    # "https://www.googleapis.com/auth/userinfo.profile",
    "openid"
]

# TODO: Globals are not thrilling, but until we split into multiple files:
# TODO: Would be nice to cache the secrets on disk in dev with a TTL.
secret_manager_client = SecretManagerServiceClient()
client_secrets_config = cast(
    dict[str, dict[str, str]],
    json.loads(
        secret_manager_client.access_secret_version(  # pyright: ignore[reportUnknownMemberType]
            request={
                "name": (
                    "projects/69808963210/secrets/oidrivehelper-client-secret/versions/latest"
                )
            }
        ).payload.data.decode()
    ),
)
flask_secret_key = secret_manager_client.access_secret_version(  # pyright: ignore[reportUnknownMemberType]
    request={"name": "projects/69808963210/secrets/flask-secret-key/versions/latest"}
).payload.data.decode()
database = FirestoreClient()
app = flask.Flask(__name__)
app.secret_key = flask_secret_key


@app.route("/")
def index() -> ResponseValue:
    # TODO: try firestore first
    if "credentials" not in flask.session:
        return flask.redirect("authorize")
    return f"{flask.session.get("uid")=}"

    # Load the credentials from the session.
    # credentials = google.oauth2.credentials.Credentials(**flask.session["credentials"])  # pyright: ignore[reportAny]

    # client = googleapiclient.discovery.build("oauth2", "v2", credentials=credentials)  # pyright: ignore[reportUnknownVariableType,reportUnknownMemberType]

    # return client.userinfo().v2().me().get().execute()  # pyright: ignore[reportUnknownMemberType,reportUnknownVariableType]


@app.route("/authorize")
def authorize() -> ResponseValue:
    flow = google_auth_oauthlib.flow.Flow.from_client_config(  # pyright: ignore[reportUnknownMemberType]
        client_secrets_config, scopes=SCOPES
    )
    flow.redirect_uri = flask.url_for("oauth2callback", _external=True)
    authorization_url, state = cast(
        tuple[str, str],
        flow.authorization_url(  # pyright: ignore[reportUnknownMemberType]
            access_type="offline"  # , include_granted_scopes="true"
        ),
    )
    flask.session["code_verifier"] = cast(str, flow.code_verifier)
    flask.session["state"] = state
    return flask.redirect(authorization_url)


@app.route("/oauth2callback")
def oauth2callback() -> ResponseValue:
    # Specify the state when creating the flow in the callback so that it can
    # verify the authorization server response.
    state = cast(str, flask.session["state"])
    flow = google_auth_oauthlib.flow.Flow.from_client_config(  # pyright: ignore[reportUnknownMemberType]
        client_secrets_config,
        scopes=SCOPES,
        state=state,
        code_verifier=cast(str, flask.session["code_verifier"]),
    )
    flow.redirect_uri = flask.url_for("oauth2callback", _external=True)

    # Use the authorization server's response to fetch the OAuth 2.0 tokens.
    authorization_response = flask.request.url
    flow.fetch_token(authorization_response=authorization_response)  # pyright: ignore[reportUnknownMemberType]

    # Store the credentials in the session.
    credentials = flow.credentials
    if not isinstance(credentials, Credentials):
        msg = f"credentials are of wrong type {type(credentials)}"
        raise TypeError(msg)
    credentials = cast(Credentials, flow.credentials)

    credentials_dict = {
        "token": credentials.token,  # pyright: ignore[reportUnknownMemberType]
        "refresh_token": credentials.refresh_token,  # pyright: ignore[reportUnknownMemberType]
        "token_uri": credentials.token_uri,  # pyright: ignore[reportUnknownMemberType]
        "client_id": credentials.client_id,  # pyright: ignore[reportUnknownMemberType]
        "client_secret": credentials.client_secret,  # pyright: ignore[reportUnknownMemberType]
        "scopes": credentials.scopes,  # pyright: ignore[reportUnknownMemberType]
    }
    flask.session["credentials"] = credentials_dict

    import google.auth.transport.requests

    # fun fun
    id_info = id_token.verify_oauth2_token(
        flow.oauth2session.token["id_token"],
        google.auth.transport.requests.Request(),
        credentials.client_id,
    )
    pprint(["id_info", id_info])
    raw = flow.oauth2session.token["id_token"]
    payload = json.loads(base64.urlsafe_b64decode(raw.split(".")[1] + "=="))
    uid = payload["sub"]
    flask.session["uid"] = uid
    print(f"{uid=}")

    pprint(credentials_dict)
    # TODO: Persist the refresh token !!!
    doc = database.document(f"apps/oidrivehelper/users/{uid}")
    x = doc.get()
    y = x.to_dict() or {}
    y["credentials"] = credentials_dict
    _ = doc.set(y)

    return flask.redirect(flask.url_for("index"))


if __name__ == "__main__":
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
    app.run("localhost", 8080, debug=True)
