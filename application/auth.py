import functools

from flask import (
    Blueprint,
    current_app,
    flash,
    g,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.security import check_password_hash, generate_password_hash

from application.db import get_db

bp = Blueprint("auth", __name__, url_prefix="/auth")


@bp.route("/login", methods=("GET", "POST"))
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        error = None

        if username == "ALMA-MAPS":
            if not check_password_hash(
                current_app.config.get("MAPS_HASHED_PASSWORD"), password
            ):
                error = "Incorrect password."
        else:
            error = "Incorrect username."

        print(error)
        if error is None:
            session.clear()
            session["user_id"] = current_app.config.get("MAPS_USER")
            return redirect(url_for("index"))

        flash(error)

    return render_template("auth/login.html")


@bp.before_app_request
def load_logged_in_user():
    user_id = session.get("user_id")
    if user_id is None:
        g.user = None
    else:
        # the one user we have
        g.user = 1


@bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


# this decorator makes each view check that the user is logged in
def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for("auth.login"))

        return view(**kwargs)

    return wrapped_view
