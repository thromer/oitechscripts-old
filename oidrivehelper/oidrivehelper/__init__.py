from dataclasses import asdict, dataclass

from flask import Flask

from . import auth, drive


@dataclass
class AppConfig:
    CLIENT_SECRETS_CONFIG: dict[str, dict[str, str]]


def create_app(config: AppConfig) -> Flask:
    app = Flask(__name__, instance_relative_config=True)
    _ = app.config.from_mapping(asdict(config))

    app.register_blueprint(auth.bp)
    app.register_blueprint(drive.bp)

    return app
