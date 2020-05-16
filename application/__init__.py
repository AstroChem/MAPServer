from flask import Flask

from werkzeug.security import check_password_hash, generate_password_hash

import os

from . import db


def create_app(test_config=None):
    application = Flask(__name__)
    application.config.from_mapping(DATABASE=os.environ["SQLALCHEMY_DATABASE_URI"])

    if test_config is None:
        application.config.from_object("application.configuration.Config")
        application.config.from_mapping(
            MAPS_USER=os.environ["MAPS_USER"], MAPS_PASSWORD=os.environ["MAPS_PASSWORD"]
        )

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

    # register our blueprints
    from .views import auth
    from .views import errors
    from .views import home
    from .views import disks
    from .views import runs

    application.register_blueprint(auth.bp)
    application.register_blueprint(errors.bp)
    application.register_blueprint(home.bp)
    application.register_blueprint(disks.bp)
    application.register_blueprint(runs.bp)

    # register the database with the app
    db.init_app(application)

    return application
