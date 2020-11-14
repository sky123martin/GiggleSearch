import os

class Config(object):
    SECRET_KEY = os.urandom(32)
    UPLOAD_FOLDER = 'FileInput'
    ALLOWED_EXTENSIONS = {'bed', 'bed.gz'}
    MYSQL_DATABASE_USER = 'genome'
    MYSQL_DATABASE_DB = 'hg19'
    MYSQL_DATABASE_HOST = 'genome-mysql.soe.ucsc.edu'