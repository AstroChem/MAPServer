from flask import Flask

from werkzeug.security import check_password_hash, generate_password_hash

import os

from . import db


def create_app(test_config=None):
    application = Flask(__name__, instance_relative_config=True)
    application.config.from_mapping(
        SECRET_KEY="dev", DATABASE=os.environ["SQLALCHEMY_DATABASE_URI"]
    )

    if test_config is None:
        application.config.from_object("application.configuration.DevelopmentConfig")
        application.config.from_pyfile("config.cfg")
        # application.config.from_mapping(
        # MAPS_USER=os.environ["MAPS_USER"], MAPS_PASSWORD=os.environ["MAPS_PASSWORD"]
        # )

    else:
        # load the test config if passed in
        application.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(application.instance_path)
    except OSError:
        pass

    application.config["MAPS_HASHED_PASSWORD"] = generate_password_hash(
        application.config["MAPS_PASSWORD"]
    )

    from . import auth

    application.register_blueprint(auth.bp)

    from .main import main as main_blueprint

    application.register_blueprint(main_blueprint)
    application.add_url_rule("/", endpoint="index")

    # register the database with the app
    db.init_app(application)

    return application
