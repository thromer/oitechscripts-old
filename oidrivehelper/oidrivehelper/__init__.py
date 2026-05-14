import os
from dataclasses import asdict, dataclass

from dotenv import load_dotenv
from flask import Blueprint, Flask

from . import auth, drive, index


@dataclass
class AppConfig:
    CLIENT_SECRETS_CONFIG: dict[str, dict[str, str]]


index_bp = Blueprint("index", __name__)


def create_app(config: AppConfig) -> Flask:
    _ = load_dotenv()
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"  # No-op in prod
    # Without this fetch_token throws if we get more scopes than requested.
    # Perhaps app should listen for the scope_changed signal and log
    # See oauthlib/oauth2/rfc6749/parameters.py
    os.environ["OAUTHLIB_RELAX_TOKEN_SCOPE"] = "1"

    app = Flask(__name__, instance_relative_config=True)
    _ = app.config.from_mapping(asdict(config))

    app.register_blueprint(index.bp)
    app.register_blueprint(auth.bp)
    app.register_blueprint(drive.bp)

    return app
