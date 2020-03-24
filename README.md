# MAPServer
Flask website hosting TCLEAN and RML image products.

## Test server locally

activate the virtual environment
    $ source .venv/bin/activate

set up the database connection 
    $ export SQLALCHEMY_DATABASE_URI="sqlite:////Users/ianczekala/Documents/MAPS/MAPS.db"

set up and run flask
    $ export FLASK_APP=maps.py
    $ flask run

## Install MAPSDB 

Need to install `mapsdb` using the current venv.