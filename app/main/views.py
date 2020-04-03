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


@main.route("/")
def index():
    return render_template(
        "index.html",
        transitions_url=url_for(".transitions"),
        disks_url=url_for(".disks"),
    )


@main.route("/transitions/")
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
def disks():
    """
    Show all disks.
    """
    db = get_db()
    with db.begin():
        s = select([schema.disks])
        result = db.execute(s)
        disks_list = result.fetchall()

    return render_template("disks.html", disks=disks_list)


# @main.route('/transitions/<int:transition_id>/')
# def transition_id():
#     '''
#     Present a list of all disks imaged at that transition.
#     '''
#     pass

# @main.route('/<disk>/')
# def disk():
#     '''
#     Display the summary page corresponding to a particular disk. List all the transitions available, and the links to their runs.
#     '''
#     # want to think about using url_for()
#     pass

# @main.route('/run/<int:run_id>)
def run(run_id):
    """
    Show the run summary corresponding to the run_id.
    """
    pass


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
