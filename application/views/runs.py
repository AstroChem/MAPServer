from flask import (
    render_template,
    session,
    redirect,
    url_for,
    current_app,
    g,
    send_from_directory,
)


import os
import pandas as pd
import numpy as np
from bokeh.plotting import figure
from bokeh.models import ColumnDataSource
from bokeh.embed import components
from bokeh.palettes import Dark2_5 as palette
import itertools

from sqlalchemy import select, join, and_, func, literal, desc, asc
from mapsdb import schema

from flask import Blueprint

from application.db import get_db
from application.views.auth import login_required

bp = Blueprint("runs", __name__)


@bp.route("/runs/")
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
            .join(schema.method_implementations)
            .join(schema.method_types)
        )
        s = (
            select(
                [
                    schema.runs,
                    schema.run_statuses.c.run_status,
                    schema.method_implementations,
                    schema.method_types.c.method_type,
                    schema.disks.c.disk_name,
                    schema.transitions.c.transition_id,
                    schema.transitions.c.molecule_name,
                    schema.transitions.c.quantum_number,
                ]
            )
            .reduce_columns()
            .select_from(j)
        )
        result = db.execute(s)
        runs_list = result.fetchall()

    return render_template("runs/runs.html", runs_list=runs_list)


@bp.route("/runs/<int:run_id>/")
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
    if os.path.exists(fname):
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
    else:
        bokeh_script = None
        bokeh_plot_div = None

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
        cubes_list = result.fetchall()

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
            .order_by(desc(schema.cube_images.c.frequency))
        )

        result = db.execute(s)
        cube_images = result.fetchall()
        image_paths = ["/" + cube_image["image_path"] for cube_image in cube_images]

    return render_template(
        "runs/run_id.html",
        cube_types=cube_types,
        combo_params=combo_params,
        run_parameters=run_parameters,
        run_id=run_id,
        image_paths=image_paths,
        bokeh_script=bokeh_script,
        bokeh_plot_div=bokeh_plot_div,
    )
