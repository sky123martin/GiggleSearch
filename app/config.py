import os
import app

class Config(object):
    SECRET_KEY = os.environ.get('SECRET') or 'you-will-never-guess'