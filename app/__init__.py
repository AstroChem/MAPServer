from flask import Flask
from flask_bootstrap import Bootstrap
# from flask_moment import Moment
from config import config

bootstrap = Bootstrap()
# moment = Moment()

from . import db

def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    bootstrap.init_app(app)
    # moment.init_app(app)

    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)


    # register the database with the app
    db.init_app(app)
    
    return app

