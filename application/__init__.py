from flask import Flask
from config import Config
from flask_bootstrap import Bootstrap
from flaskext.mysql import MySQL

app = Flask(__name__)
app.config.from_object(Config)
bootstrap = Bootstrap(app)

mysql = MySQL()
mysql.init_app(app)


from app import routes