from typing import TYPE_CHECKING

import googleapiclient.discovery
from flask import Blueprint, session
from google.oauth2.credentials import Credentials

from .auth import auth_required


if TYPE_CHECKING:
    from flask.typing import ResponseValue

bp = Blueprint("drive", __name__)


@bp.route("/hello")
@auth_required
def hello() -> ResponseValue:
    print(f"{session["credentials"]=}")
    credentials = Credentials(**session["credentials"])
    print(f"{credentials.client_id=}")

    print("hello calling build")
    client = googleapiclient.discovery.build("oauth2", "v2", credentials=credentials)

    print("hello calling me")
    user = client.userinfo().v2().me().get().execute()
    return f"hello {user} (drive: /hello)"


@bp.route("/what")
@auth_required
def what() -> ResponseValue:
    return "what? (drive: /what)"
