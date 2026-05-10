import json
import os
from typing import cast

from google.cloud.secretmanager_v1 import SecretManagerServiceClient

from oidrivehelper import AppConfig, create_app


if __name__ == "__main__":
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"  # No-op in prod
    # Without this fetch_token throws if we get more scopes than requested.
    # Perhaps app should listen for the scope_changed signal and log
    # See oauthlib/oauth2/rfc6749/parameters.py
    os.environ["OAUTHLIB_RELAX_TOKEN_SCOPE"] = "1"

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
        request={
            "name": "projects/69808963210/secrets/flask-secret-key/versions/latest"
        }
    ).payload.data.decode()

    app = create_app(config=AppConfig(CLIENT_SECRETS_CONFIG=client_secrets_config))
    app.secret_key = flask_secret_key
    app.run("localhost", 8080, debug=True)
