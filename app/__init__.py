from flask import Flask
from flask_bootstrap import Bootstrap
# from flask_moment import Moment

from werkzeug.security import check_password_hash, generate_password_hash

import os

bootstrap = Bootstrap()
# moment = Moment()

from . import db

def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY="dev",
        DATABASE=os.environ["SQLALCHEMY_DATABASE_URI"]
    )

    if test_config is None:
        app.config.from_object("app.config.DevelopmentConfig")
        app.config.from_pyfile("config.cfg")

    else:
        # load the test config if passed in 
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    app.config["MAPS_HASHED_PASSWORD"] = generate_password_hash(app.config["MAPS_PASSWORD"])

    bootstrap.init_app(app)
    # moment.init_app(app)

    print(app.config)

    from . import auth 
    app.register_blueprint(auth.bp)

    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)
    app.add_url_rule("/", endpoint="index")
 
    # register the database with the app
    db.init_app(app)
    
    return app

