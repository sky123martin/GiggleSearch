import os

class Config(object):
    SECRET_KEY = os.urandom(32) # needed for CRSV which is used for forms
    
    # UCSC CONFIG VARS
    UCSC_BIG_DATA_LINK = ""
    UCSC_SQL_DB_HOST = "genome-mysql.soe.ucsc.edu"
    UCSC_SQL_DB_USER = "genome"
    UCSC_API = "https://api.genome.ucsc.edu/"

    # Path to Giggle Index
    SERVER_PATH = "../GiggleIndexServer"

    TIMEOUT = 1000

    # restrictions for interval input
    MAX_INTERVALS = 20
    MAX_INTERVAL_SIZE = 1000000000 # Base pairs

    # restrictions for interval input
    ACCEPTED_FILE_FORMATS = [".bed.gz"]
