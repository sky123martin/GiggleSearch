from flask import session
from application import app
import mysql.connector
import sqlite3
import sys
from bs4 import BeautifulSoup as bs
from contextlib import contextmanager
import pandas as pd
import numpy as np 
import random
import subprocess
import time
import math
import re
import requests 

def retrieve_genomes():
    try:
        result_df = pd.read_csv("{}/outputs/genomes.csv".format(app.config["SERVER_PATH"]), index_col = False)
        return result_df

    except subprocess.TimeoutExpired as e:
        print('Time Out')
        logger.error("Time limit for current request exceed.")
        return 'Time limit for current request exceed.'

    except Exception as e:
        return str(e)

def parse_interval_input(search, ref_genome):
#     EXAMPLE
#     Input = "1:100-2000 2:100-2000 3:100-2000 1:1030-2000 in rn6"
#     Out = [[u'1:100-2000', u'rn6'], [u'2:100-2000', u'rn6'], [u'3:100-2000', u'rn6'], [u'1:1030-2000', u'rn6']])
    currentChromosome = ""
    intervals = search.replace(",", "").replace("c", "").replace("h", "").replace("r", "").replace("o", "").replace("m", "").split()
    print(intervals)
    cleaned_intervals = []
    
    for interval in intervals:
        try:
            chrom = interval.split(":")[0]
            bounds = interval.split(":")[1]
            lower = bounds.split("-")[0]
            upper = bounds.split("-")[1]
        except:
            return "interval {} does not meet formating guidelines of __:__-__".format(interval)

        if ":" not in interval or "-" not in interval:
            return "parser detects that this query is missing : or -"
        elif not chrom.isdigit():
            return "unable to find a valid chromosome number on interval {}".format(interval)
        elif not lower.isdigit():
            return "unable to find a valid lower bound on interval {}".format(interval)
        elif not upper.isdigit():
            return "unable to find a valid upper bound on interval {}".format(interval)

        if int(lower) > int(upper):
            return "interval, {}, has lower bound greater than upper bound".format(interval)

        if int(upper)-int(lower) > app.config["MAX_INTERVAL_SIZE"] :
                return "max interval size that can be proccessed is {}, try file input for larger intervals.".format(app.config["MAX_INTERVAL_SIZE"])

        cleaned_intervals.append([chrom + ":" + lower + "-" + upper, ref_genome]) 

    if len(cleaned_intervals) == 0:
        return "no valid intervals entered"

    if len(cleaned_intervals) > app.config["MAX_INTERVALS"]:
            return "max number of intervals exceeded (>{})".format(app.config["MAX_INTERVALS"])
    
    return cleaned_intervals


def interval_search(ref_genome, chrom, lower, upper):
    try:
        out_file_name = str(random.randint(0,sys.maxsize)) + '.csv'
        cmd = "(cd {} ; python3 query_indices.py --qi {}:{}-{} {} {} True)".format(app.config["SERVER_PATH"], chrom, lower, upper, ref_genome, out_file_name)
        proc = subprocess.check_output(cmd,
                                    stderr=None,
                                    shell=True,
                                    timeout=app.config["TIMEOUT"])

        result_df = pd.read_csv(app.config["SERVER_PATH"] + "/" + out_file_name, index_col = False)
        result_df["name"] = result_df["FILEID"]

        cmd = "(cd {} ; rm {})".format(app.config["SERVER_PATH"], out_file_name)
        proc = subprocess.check_output(cmd,
                                    stderr=None,
                                    shell=True,
                                    timeout=app.config["TIMEOUT"])

        return result_df[result_df["overlaps"] > 0]

    except subprocess.TimeoutExpired as e:
        print("Time limit for current request exceed.")
        return 'Time limit for current request exceed.'

    except Exception as e:
        return str(e)


def file_search(process_id, ref_genome, file_name):
    try:
        print(process_id)
        out_file_name = "outputs/" + str(process_id) + '.csv'
        cmd = "(cd {};  python3 query_indices.py --qf uploads/{}.{} {} {} True)".format(app.config["SERVER_PATH"], process_id, file_name.split(".", 1)[-1], ref_genome, out_file_name)
        proc = subprocess.check_output(cmd,
                                     stderr=None,
                                     shell=True,
                                     timeout=app.config["TIMEOUT"])
        result_df = pd.read_csv(app.config["SERVER_PATH"] + "/" + out_file_name, index_col = False)

        
        cmd = "(cd {} ; rm {})".format(app.config["SERVER_PATH"], out_file_name)
        proc = subprocess.check_output(cmd,
                                    stderr=None,
                                    shell=True,
                                    timeout=app.config["TIMEOUT"])

        # cmd = "(cd {} ; rm uploads/{}.{})".format(app.config["SERVER_PATH"], process_id, file_name.split(".", 1)[-1])
        # proc = subprocess.check_output(cmd,
        #                             stderr=None,
        #                             shell=True,
        #                             timeout=app.config["TIMEOUT"])
        
        result_df["name"] = result_df["FILEID"]

        return result_df[result_df["overlaps"] > 0]

    except subprocess.TimeoutExpired as e:
        print("Time limit for current request exceed.")
        return 'Time limit for current request exceed.'

    except Exception as e:
        return str(e)

def retrieve_metadata(ref_genome):
    try:
        out_file_name = "outputs/" + str(random.randint(0,sys.maxsize)) + '.csv'
        cmd = "(cd {};  python3 query_indices.py -f {} {})".format(app.config["SERVER_PATH"], ref_genome, out_file_name)
        print(cmd)
        proc = subprocess.check_output(cmd,
                                     stderr=None,
                                     shell=True,
                                     timeout=app.config["TIMEOUT"])
        
        metadata_df = pd.read_csv(app.config["SERVER_PATH"] + "/" + out_file_name, index_col = False)

        cmd = "(cd {} ; rm {})".format(app.config["SERVER_PATH"], out_file_name)
        proc = subprocess.check_output(cmd,
                                    stderr=None,
                                    shell=True,
                                    timeout=app.config["TIMEOUT"])

        return metadata_df

    except subprocess.TimeoutExpired as e:
        print('Time Out')
        logger.error("Time limit for current request exceed.")
        return 'Time limit for current request exceed.'

    except Exception as e:
        return str(e)


