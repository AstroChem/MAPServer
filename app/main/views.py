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

from sqlalchemy import select
from mapsdb import schema

from app.db import get_db
from app.auth import login_required


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

    return render_template("transitions.html", transitions=transitions_list)


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

    # make a giant merge of all of the rows with this disk_id

    # Disk name, parameters

    # transitions  which (Mol / QN / Freq) they correspond to and which have available measurement sets, how many runs they have

    # return render_template("disk.html", disk_dictionary=disk_dictionary)
    pass


@main.route("/runs/")
def runs():
    """
    Show all runs
    """

    db = get_db()
    with db.begin():
        # create a giant join to get all the important run properties

        s = select([schema.runs])
        result = db.execute(s)
        runs_list = result.fetchall()

    return render_template("runs.html", runs=runs_list)


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

    script, div = components(p)

    return render_template(
        "run_id.html", run_id=run_id, script=script, bokeh_plot_div=div
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
@main.route("/imgs/<path:filename>")
def send_file(filename):
    return send_from_directory(
        "/Users/ianczekala/Documents/MAPS/NRAO/IMLup/C18O/", filename
    )
