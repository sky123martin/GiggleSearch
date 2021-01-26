from flask import Flask
from application.config import Config
import subprocess

app = Flask(__name__)
app.config.from_object(Config)

from flask_bootstrap import Bootstrap

bootstrap = Bootstrap(app)
proc = subprocess.check_call("mkdir -p {}/uploads".format(app.config["SERVER_PATH"]), shell=True)
proc = subprocess.check_call("mkdir -p {}/outputs".format(app.config["SERVER_PATH"]), shell=True)

from application import routes