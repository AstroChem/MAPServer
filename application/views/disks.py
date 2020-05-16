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

bp = Blueprint("disks", __name__)


@bp.route("/disks/")
@login_required
def disks():
    """
    Show all disks.
    """
    db = get_db()
    with db.begin():
        s = select([schema.disks.c.disk_id, schema.disks.c.disk_name])
        result = db.execute(s)
        disks_list = result.fetchall()

    return render_template("disks/disks.html", disks=disks_list)


@bp.route("/disks/<int:disk_id>/")
def disk(disk_id):
    """
    Display the summary page corresponding to a particular disk. List all the transitions available, and the links to their runs.
    """

    db = get_db()
    with db.begin():
        s = select([schema.disks]).where(schema.disks.c.disk_id == disk_id)
        result = db.execute(s)
        disk_params = result.first()

        # make a giant merge of all of the rows with this disk_id
        j = schema.measurement_sets.join(schema.disks).join(schema.transitions)
        # do an outer join with the runs, since there will be measurement sets that do not
        # have any runs
        j_runs = j.outerjoin(schema.runs)
        s = (
            select(
                [
                    # count the number of runs for each unique transition id
                    func.count(schema.runs.c.run_id).label("run_count"),
                    schema.transitions,
                ]
            )
            .reduce_columns()
            .select_from(j_runs)
            .where(schema.disks.c.disk_id == disk_id)
            .group_by(schema.transitions.c.transition_id)
        )

        result = db.execute(s)
        ms_list = result.fetchall()

    return render_template("disks/disk.html", disk_params=disk_params, ms_list=ms_list)


@bp.route("/transitions/")
@login_required
def transitions():
    """
    Show all transitions.
    """
    db = get_db()
    with db.begin():
        s = select([schema.transitions])
        result = db.execute(s)
        transitions_list = result.fetchall()

        s = select([schema.disks.c.disk_name, schema.disks.c.disk_id])
        result = db.execute(s)
        disk_pairs = result.fetchall()
        # sort this list alphabetically by disk name
        disk_pairs.sort(key=lambda tup: tup[0])

        # create a mapping of (disk_id, transition_id) to (num_ms, num_runs)
        # do this by a cross join of disks to transitions, which we accomplish by
        # doing a join with onclause=True
        # then, do an outer join with measurement sets and an outerjoin with runs
        # we needed to specify the onclause, because for somereason it wouldn't take both
        # automatically.
        # then, do a group-by and count to reduce these.

        # i think we need to split this into two group-by actions
        # see: http://www.dein.fr/writing-a-subquery-with-sqlalchemy-core.html
        # and https://www.tutorialspoint.com/sqlalchemy/sqlalchemy_core_using_aliases.htm
        # and https://docs.sqlalchemy.org/en/13/core/tutorial.html#using-aliases-and-subqueries
        # also sqlite text, ch 5, advanced techniques, subqueries

        # first, create the list of all (disk_id, transition_id) as an alias

        j = (
            schema.disks.join(schema.transitions, onclause=literal(True))
            .outerjoin(
                schema.measurement_sets,
                onclause=and_(
                    (schema.disks.c.disk_id == schema.measurement_sets.c.disk_id),
                    (
                        schema.transitions.c.transition_id
                        == schema.measurement_sets.c.transition_id
                    ),
                ),
            )
            .outerjoin(
                schema.runs,
                onclause=(
                    schema.measurement_sets.c.measurement_set_id
                    == schema.runs.c.measurement_set_id
                ),
            )
        )

        s = (
            select(
                [
                    schema.disks.c.disk_id,
                    schema.transitions.c.transition_id,
                    func.count(schema.measurement_sets.c.measurement_set_id).label(
                        "ms_count"
                    ),
                    func.count(schema.runs.c.run_id).label("run_count"),
                ]
            )
            .select_from(j)
            .group_by(schema.disks.c.disk_id, schema.transitions.c.transition_id)
        )

        # execute these two tables and join the result by disk_id, transition_id
        result = db.execute(s)
        # make this a dictionary indexed by disk_id, transition_id
        disk_transition_dict = {}
        for r in result:
            disk_transition_dict[(r["disk_id"], r["transition_id"])] = (
                r["ms_count"],
                r["run_count"],
            )

    return render_template(
        "disks/transitions.html",
        disk_pairs=disk_pairs,
        transitions=transitions_list,
        disk_transition_dict=disk_transition_dict,
    )


@bp.route("/disks/<int:disk_id>/transitions/<int:transition_id>/")
def disk_transition(disk_id, transition_id):
    """
    Display the set of runs corresponding to this disk / transition combination.
    """

    db = get_db()
    with db.begin():

        # the qualities unique to this disk-transition combo
        s = select([schema.disks, schema.transitions]).where(
            and_(
                (schema.disks.c.disk_id == disk_id),
                (schema.transitions.c.transition_id == transition_id),
            )
        )
        result = db.execute(s)
        combo_params = result.first()

        # the measurement sets that correspond to this disk-transition-combo
        j = schema.measurement_sets.join(schema.transitions).join(schema.disks)
        s = (
            select([schema.measurement_sets])
            .select_from(j)
            .where(
                and_(
                    (schema.disks.c.disk_id == disk_id),
                    (schema.transitions.c.transition_id == transition_id),
                )
            )
        )
        result = db.execute(s)
        ms_list = result.fetchall()

        # the runs that correspond to this disk-transition combo (all MS's)
        j = (
            schema.runs.join(schema.run_statuses)
            .join(
                schema.method_implementations,
                onclause=and_(
                    (
                        schema.runs.c.method_type_id
                        == schema.method_implementations.c.method_type_id
                    ),
                    (
                        schema.runs.c.method_version
                        == schema.method_implementations.c.method_version
                    ),
                ),
            )
            .join(schema.method_types)
            .join(schema.measurement_sets)
            .join(schema.disks)
            .join(schema.transitions)
        )
        s = (
            select(
                [
                    schema.runs,
                    schema.run_statuses.c.run_status,
                    schema.method_types.c.method_type,
                ]
            )
            .select_from(j)
            .where(
                and_(
                    (schema.disks.c.disk_id == disk_id),
                    (schema.transitions.c.transition_id == transition_id),
                )
            )
            .reduce_columns()
        )
        result = db.execute(s)
        runs_list = result.fetchall()

    return render_template(
        "disks/disk-transition.html",
        combo_params=combo_params,
        ms_list=ms_list,
        runs_list=runs_list,
    )
