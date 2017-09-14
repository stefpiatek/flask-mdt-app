import os

from secret_info import POSTGRES_CONNECTION, SECRET_KEY

basedir = os.path.abspath(os.path.dirname(__file__))

date_style = {'format': '%d-%b-%Y',
              'help': 'DD-MMM-YYYY'}

class Config:
    WTF_CSRF_ENABLED = True
    SECRET_KEY = os.environ.get('SECRET_KEY') or SECRET_KEY
    SQLALCHEMY_TRACK_MODIFICATIONS = True


    @staticmethod
    def init_app(app):
        pass


class DevelopmentConfig(Config):
    DEBUG = True
    TESTING = False
    DEBUG_TB_INTERCEPT_REDIRECTS = False
    DEBUG_TB_HOSTS = ('127.0.0.1')
    SQLALCHEMY_DATABASE_URI = (os.environ.get('TEST_DATABASE_URL') or
                               POSTGRES_CONNECTION + 'mdt_dev')


class TestingConfig(Config):
    DEBUG = False
    TESTING = True
    SQLALCHEMY_DATABASE_URI = (os.environ.get('TEST_DATABASE_URL') or
                               POSTGRES_CONNECTION + 'mdt_test')


class ProductionConfig(Config):
    DEBUG = False
    TESTING = False
    SQLALCHEMY_DATABASE_URI = (os.environ.get('TEST_DATABASE_URL') or
                               POSTGRES_CONNECTION + 'mdt_db')


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,

    'default': DevelopmentConfig
}
