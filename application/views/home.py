from flask import (
    render_template,
    session,
    redirect,
    url_for,
    current_app,
    g,
    send_from_directory,
)


from sqlalchemy import select, join, and_, func, literal, desc, asc
from mapsdb import schema

from flask import Blueprint

from application.db import get_db
from application.views.auth import login_required

bp = Blueprint("home", __name__)


@bp.route("/")
@login_required
def index():
    return render_template(
        "index.html",
        transitions_url=url_for("disks.transitions"),
        disks_url=url_for("disks.disks"),
    )


# this doesn't end in a slash because we are looking to mimic a filename
@bp.route("/<path:filename>")
def send_file(filename):
    return send_from_directory(current_app.config["MAPS_ROOT"], filename)


@bp.route("/glossary/")
def glossary():
    """
    List the id's with the corresponding type tables, like method implementations, methods, run_statuses.
    """
    db = get_db()
    with db.begin():
        s = select([schema.disks.c.disk_id, schema.disks.c.disk_name])
        result = db.execute(s)
        disks_list = result.fetchall()

        s = select([schema.run_statuses])
        result = db.execute(s)
        run_statuses_list = result.fetchall()

        s = select([schema.method_types])
        result = db.execute(s)
        method_types_list = result.fetchall()

        j = schema.method_implementations.join(schema.method_types)
        s = select(
            [schema.method_implementations, schema.method_types.c.method_type]
        ).select_from(j)
        result = db.execute(s)
        method_implementations_list = result.fetchall()

        s = select([schema.cube_types])
        result = db.execute(s)
        cube_types_list = result.fetchall()
        j = (
            schema.runs.join(schema.parameters)
            .join(schema.method_implementations)
            .join(schema.method_types)
        )
        s = (
            select(
                [
                    func.count(schema.runs.c.run_id).label("run_count"),
                    schema.method_types.c.method_type,  # this is essentially chosen at random
                    schema.parameters,
                ]
            )
            .select_from(j)
            .group_by(
                schema.parameters.c.parameter_id, schema.method_types.c.method_type
            )
            .reduce_columns()
        )
        result = db.execute(s)
        parameters_list = result.fetchall()

        key_list = result.keys()

    # create a header list excepting run_id and method_type
    header_set = set(key_list)
    header_set.remove("parameter_id")
    header_set.remove("method_type")
    header_set.remove("run_count")
    header_set.remove("npix")
    header_set.remove("cell_size")

    return render_template(
        "glossary.html",
        disks_list=disks_list,
        run_statuses_list=run_statuses_list,
        method_types_list=method_types_list,
        method_implementations_list=method_implementations_list,
        cube_types_list=cube_types_list,
        parameters_list=parameters_list,
        parameters_header_set=header_set,
    )
