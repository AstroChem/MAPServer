from flask import (
    render_template,
    session,
    redirect,
    url_for,
    current_app,
    g,
    send_from_directory,
)
from . import main

from sqlalchemy import select, join, and_, func, literal, desc, asc
from mapsdb import schema

from application.db import get_db
from application.auth import login_required


import os
import pandas as pd
import numpy as np
from bokeh.plotting import figure
from bokeh.models import ColumnDataSource
from bokeh.embed import components
from bokeh.palettes import Dark2_5 as palette
import itertools


@main.route("/")
@login_required
def index():
    return render_template(
        "index.html",
        transitions_url=url_for(".transitions"),
        disks_url=url_for(".disks"),
    )


@main.route("/transitions/")
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
        "transitions.html",
        disk_pairs=disk_pairs,
        transitions=transitions_list,
        disk_transition_dict=disk_transition_dict,
    )


@main.route("/disks/")
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

    print(disks_list)

    return render_template("disks.html", disks=disks_list)


@main.route("/disks/<int:disk_id>/")
def disk(disk_id):
    """
    Display the summary page corresponding to a particular disk. List all the transitions available, and the links to their runs.
    """
    print("disk_id", disk_id)

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
                    schema.measurement_sets,
                    schema.transitions,
                ]
            )
            .select_from(j_runs)
            .where(schema.disks.c.disk_id == disk_id)
            .group_by(schema.transitions.c.transition_id)
        ).reduce_columns()
        result = db.execute(s)
        ms_list = result.fetchall()

    return render_template("disk.html", disk_params=disk_params, ms_list=ms_list)


@main.route("/disks/<int:disk_id>/transitions/<int:transition_id>/")
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

        print(result.keys())

    return render_template(
        "disk-transition.html",
        combo_params=combo_params,
        ms_list=ms_list,
        runs_list=runs_list,
    )


@main.route("/runs/")
def runs():
    """
    Show all runs
    """

    db = get_db()
    with db.begin():
        # create a giant join to get all the important run properties

        j = (
            schema.runs.join(schema.run_statuses)
            .join(schema.measurement_sets)
            .join(schema.disks)
            .join(schema.transitions)
        )
        s = select(
            [
                schema.runs,
                schema.run_statuses.c.run_status,
                schema.disks.c.disk_name,
                schema.transitions.c.transition_id,
                schema.transitions.c.molecule_name,
                schema.transitions.c.quantum_number,
            ]
        ).select_from(j)
        result = db.execute(s)
        runs_list = result.fetchall()

    return render_template("runs.html", runs_list=runs_list)


@main.route("/runs/<int:run_id>/")
def run(run_id):
    """
    Show the run summary corresponding to the run_id.
    """

    # get the loss.csv fname from the run_id
    db = get_db()
    with db.begin():
        s = select([schema.runs.c.output_dir]).where(schema.runs.c.run_id == run_id)
        result = db.execute(s)
        rel_output_dir = result.first()[0]

    fname = os.path.join(current_app.config["MAPS_ROOT"], rel_output_dir, "losses.csv")
    df = pd.read_csv(fname)
    # drop the columns that are nan
    df = df.dropna(axis=1)
    source = ColumnDataSource(df)

    colors = itertools.cycle(palette)

    p = figure(title="Losses", x_axis_label="Iteration", y_axis_label="Loss")
    for key in [
        "tot",
        "nll",
        "entropy",
        "sparsity",
        "TV_image",
        "TV_channel",
        "UV_sparsity",
    ]:
        if key in df.columns:
            p.line(
                x="index",
                y=key,
                source=source,
                line_width=2,
                legend_label=key,
                color=next(colors),
            )

    bokeh_script, bokeh_plot_div = components(p)

    # get the disk_parameters
    db = get_db()
    with db.begin():

        s = select([schema.cube_types])
        result = db.execute(s)
        cube_types = result.fetchall()

        # create a join with runs, disk_id, etc.
        j = (
            schema.runs.join(schema.measurement_sets)
            .join(schema.disks)
            .join(schema.transitions)
        )

        s = (
            select(
                [schema.runs, schema.disks, schema.measurement_sets, schema.transitions]
            )
            .where(schema.runs.c.run_id == run_id)
            .select_from(j)
        ).reduce_columns()
        result = db.execute(s)
        combo_params = result.first()

        j = schema.runs.join(schema.parameters)
        s = (
            select([schema.parameters])
            .select_from(j)
            .where(schema.runs.c.run_id == run_id)
        )
        run_parameters = db.execute(s).first()

        # get all cubes produced for this run
        j = schema.cubes.join(schema.runs).join(schema.cube_types)
        s = (
            select([schema.cubes.c.cube_id, schema.cube_types.c.cube_type])
            .select_from(j)
            .where(schema.runs.c.run_id == run_id)
        ).reduce_columns()
        result = db.execute(s)
        print(result.keys())
        cubes_list = result.fetchall()
        print("cubes_list", cubes_list)

        # go through and produce a nested list of cube, cube_images

        # for each cube, get all the images and image paths
        j = (
            schema.cubes.join(schema.runs)
            .join(schema.cube_types)
            .join(schema.cube_images)
        )
        s = (
            select([schema.cube_images])
            .select_from(j)
            .where(
                and_(
                    (schema.cubes.c.cube_type_id == 0), (schema.runs.c.run_id == run_id)
                )
            )
            .order_by(asc(schema.cube_images.c.frequency))
        )

        result = db.execute(s)
        cube_images = result.fetchall()
        image_paths = ["/" + cube_image["image_path"] for cube_image in cube_images]

        print(image_paths)

    return render_template(
        "run_id.html",
        cube_types=cube_types,
        combo_params=combo_params,
        run_parameters=run_parameters,
        run_id=run_id,
        image_paths=image_paths,
        bokeh_script=bokeh_script,
        bokeh_plot_div=bokeh_plot_div,
    )


@main.route("/cube/<int:cube_id>/")
# @main.route('/cube/<int:cube_id_1>/<int:cube_id_2>') # compare two cubes with slider
def cube(cube_id):
    """
    View the image cube corresponding to a particular run_id
    """

    # load the image cube corresponding to this cube_id
    print("loading {:}".format(cube_id))

    # the list of paths corresponding to the images we want to display
    image_paths = ["/imgs/image_chan_{:02}.png".format(i) for i in range(4)]
    # print(image_paths)
    # the header information we need to plot analysis tools
    # header = {}

    # print(url_for(image_paths[0]))

    # get the paths for the images from the database
    # template against them to create the HTML

    # load the relevant CSS
    # script the JS to it
    # render

    return render_template("cube.html", image_paths=image_paths)


# this doesn't end in a slash because we are looking to mimic a filename
@main.route("/<path:filename>")
def send_file(filename):
    return send_from_directory(current_app.config["MAPS_ROOT"], filename)
