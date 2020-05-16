import os


class Config(object):
    """Base config."""

    DEBUG = False
    TESTING = False
    DATABASE_URI = os.environ["SQLALCHEMY_DATABASE_URI"]
    MAPS_ROOT = os.environ["MAPS_ROOT"]
    SECRET_KEY = b"\x19\xb6\xed\xb1d\xe1\x08\xe0\xb7\xbe\x15\xd0\xf8s\xfe\xc8"


class DevelopmentConfig(Config):
    DEBUG = True


class TestingConfig(Config):
    DEBUG = True
