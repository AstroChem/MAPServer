import os

class Config(object):
    """Base config, uses staging database server."""
    DEBUG = False
    TESTING = False
    DATABASE_URI = os.environ['SQLALCHEMY_DATABASE_URI']
    MAPS_ROOT = os.environ["MAPS_ROOT"]
    SECRET_KEY = "super-secret"
    
class DevelopmentConfig(Config):
    DEBUG = True

class TestingConfig(Config):
    DEBUG = True

    