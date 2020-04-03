# MAPServer
Flask website hosting TCLEAN and RML image products.

## Test server locally

activate the virtual environment
    $ source .venv/bin/activate

set up the database connection 
    $ export SQLALCHEMY_DATABASE_URI="sqlite:////Users/ianczekala/Documents/MAPS-LP/MAPS/MAPS.db"

set up and run flask
    $ export FLASK_APP=maps.py
    $ flask run

All of the environment variables can be set by doing
    $ source mapserver_setup.sh
and then 
    $ flask run

## Install MAPSDB 

You need to install `mapsdb` into the current venv.

