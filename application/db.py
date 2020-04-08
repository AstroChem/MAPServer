from flask import current_app, g 
from flask.cli import with_appcontext

from sqlalchemy import create_engine
from mapsdb import schema 

# g is a special object that is unique for each request, so this connection only lasts 
# as long as the request
def get_db():

    if 'db' not in g:
        # load the database into globals
        engine = create_engine(current_app.config["DATABASE_URI"])
        conn = engine.connect()
        g.db = conn

    # return the instance too
    return g.db

def close_db(e=None):
    db = g.pop('db', None)

    if db is not None:
        db.close()

def init_app(app):
    app.teardown_appcontext(close_db)
    # no init command -- done in mapsdb itself