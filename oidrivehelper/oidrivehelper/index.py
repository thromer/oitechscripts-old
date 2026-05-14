from typing import TYPE_CHECKING

from flask import Blueprint, render_template


if TYPE_CHECKING:
    from flask.typing import ResponseValue


bp = Blueprint("index", __name__)


@bp.route("/")
def index() -> ResponseValue:
    return render_template("index.html")
