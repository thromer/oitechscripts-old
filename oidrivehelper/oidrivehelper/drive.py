from typing import TYPE_CHECKING, cast

import googleapiclient.discovery
from flask import Blueprint, g
from google.oauth2.credentials import Credentials

from .auth import auth_required


if TYPE_CHECKING:
    from flask.typing import ResponseValue

bp = Blueprint("drive", __name__)


@bp.route("/hello")
@auth_required
def hello() -> ResponseValue:
    oauth2_client = googleapiclient.discovery.build(
        "oauth2", "v2", credentials=cast(Credentials, g.credentials)
    )
    user = oauth2_client.userinfo().v2().me().get().execute()
    return f"hello {user} (drive: /hello)"
