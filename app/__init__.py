from flask import Flask
from config import Config
from flask_bootstrap import Bootstrap
from flaskext.mysql import MySQL

app = Flask(__name__)
app.config.from_object(Config)
bootstrap = Bootstrap(app)

mysql = MySQL()
app.config['MYSQL_DATABASE_USER'] = 'genome'
app.config['MYSQL_DATABASE_DB'] = 'hg19'
app.config['MYSQL_DATABASE_HOST'] = 'genome-mysql.soe.ucsc.edu'
mysql.init_app(app)


from app import routes