# MAPServer
Flask website hosting TCLEAN and RML image products.

## Running Docker 

You can start the docker container using a script including the following lines: 

    # the location of the MAPS folder lab share
    MAPS_ROOT_SOURCE="/home/ian/MAPS_Share/MAPS"

    # the mount point inside the docker container
    MAPS_ROOT_CONTAINER="/home/maps/extern"

    # start the image and use a bind mount to give access to the lab share inside the container
    docker run --name maps -d -p 8000:5000 -e SQLALCHEMY_DATABASE_URI="sqlite:///${MAPS_ROOT_CONTAINER}/MAPS.db" -e MAPS_ROOT="${MAPS_ROOT_CONTAINER}/" -e MAPS_USER="test-username" -e MAPS_PASSWORD="test-password" --mount type=bind,source=${MAPS_ROOT_SOURCE},target=${MAPS_ROOT_CONTAINER},readonly iancze/maps:latest

## Testing the server locally outside of Docker

activate the virtual environment
    
    $ source venv/bin/activate

set up the database connection 
    
    $ export SQLALCHEMY_DATABASE_URI="sqlite:////Users/ianczekala/Documents/MAPS-LP/MAPS/MAPS.db"

set up and run flask
    
    $ export FLASK_APP=maps.py
    $ flask run

All of the environment variables can be set by doing
    
    $ source mapserver_setup.sh

and then 
    
    $ flask run
