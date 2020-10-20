from flask import session
from application import app
import mysql.connector
import sqlite3
from bs4 import BeautifulSoup as bs
from contextlib import contextmanager
import pandas as pd
import numpy as np 
import time
import math
import re
import requests 

chrBound = {
        "chr1":249000000,
        "chr2":242000000,
        "chr3":198000000,
        "chr4":186000000,
        "chr5":181000000,
        "chr6":170000000,
        "chr7":159000000,
        "chr8":146000000,
        "chr9":141000000,
        "chr10":133000000,
        "chr11":135000000,
        "chr12":134000000,
        "chr13":115000000,
        "chr14":107000000,
        "chr15":102000000,
        "chr16":90000000,
        "chr17":83000000,
        "chr18":78000000,
        "chr19":59000000,
        "chr20":63000000,
        "chr21":48000000,
        "chr22":49000000
    }
validSources = ["UCSC"]
maxIntervals = 20
maxIntervalSize = 1000000

@contextmanager
def connect_SQL_db(host, user):
    try:
        db = mysql.connector.connect(
                host=host,
                user=user
                )
        yield db
    except mysql.connector.Error as e:
        raise e
    else:
        db.close()

class userInput:

    def parseManualSearch(self, Input):
    #     Input = "chr1 100 : 2000 chr2 100 : 2000 chr3 100 : 2000 chr1 1030 : 2000 from UCSC"
    #     Out = [[u'chr1', u'100', u'2000', u'UCSC'], [u'chr2', u'100', u'2000', u'UCSC'], [u'chr3', u'100', u'2000', u'UCSC'], [u'chr1', u'1030', u'2000', u'UCSC']])
        currentChromosome = ""
        intervals = []
        source = str(Input.split()[-1].upper())
        currentInterval = []
        
        if source not in validSources:
            return "\"{}\" not a valid source.".format(source)
        
        try:
            for i in re.split('\W+',Input):
                if len(intervals) > maxIntervals:
                    return "Max interval exceeded, please convert to file format and proceed."

                if i[0:3].lower() == "chr":
                    if currentInterval == []:
                        currentInterval.append(str(i))
                    else:
                        return "Uncomplete interval detected in input. Check and make sure \"chr\" is used to signify chromosome"

                elif i.isdigit():
                    if len(currentInterval) == 0: #digit without chr 
                        if len(intervals) != 0:
                            currentInterval = [intervals[-1][0],int(i)]
                        else:
                            return "Interval entered without a chromosome specified."
                    elif len(currentInterval) == 1: # lower bound
                        currentInterval.append(int(i))
                    elif len(currentInterval) == 2: # chr lower and upper now complete
                        currentInterval.append(int(i))
                        currentInterval.append(source)
                        #check bounding
                        if int(currentInterval[1]) > int(currentInterval[2]):
                            return "Interval found with lower bound greater than upper bound."
                        elif chrBound[currentInterval[0]] < int(currentInterval[1]):
                            return "Lower bound out of chromosome range."
                        elif chrBound[currentInterval[0]] < int(currentInterval[2]):
                            return "Upper bound out of chromosome range(upper bound for {} is {}).".format(currentInterval[0],chrBound[currentInterval[0]])
                        elif int(currentInterval[2])-int(currentInterval[1])>maxIntervalSize:
                            return "Max interval size that can be proccessed is {}, try file input for larger intervals.".format(maxIntervalSize)
                        elif currentInterval not in intervals:
                            intervals.append(currentInterval)
                            currentInterval = []

            if len(intervals) == 0:
                return "No valid intervals entered."

            intervals.sort(key = lambda x : (x[0], x[1]))
            
            return intervals
        except:
            return "Incorrect input formatting."

class giggle:

    def __init__(self):
        pass

    def single_overlap(self,data):
        interface = 'https://stix.colorado.edu/{}?region={}:{}-{}'

        region = data[0]
        lowerBound = data[1]
        upperBound = data[2]
        source = data[3]

        start_task = time.time()
        url = interface.format(source.lower(), region, lowerBound, upperBound)
        print(url)
        val = requests.get(url)
        print("##")
        print("Giggle REQUEST + RETURN ({} seconds)".format(time.time() - start_task))
        
        start_task = time.time()
        soup = bs(val.text,"lxml")
        text = soup.text.split('\n') 
        results = []
        for i in range(0,len(text)-1):
            temp = text[i].split("\t")
            split = temp[0].split("/")
            temp[1] = int(temp[1])
            temp[2] = int(temp[2])
            if temp[2] > 0:
                if len(split) == 2 :
                    temp[0] = split[1]

                temp[0] = temp[0].split(".bed.gz")[0]
                if temp[0][-4:] != "Link":
                    results.append(temp)
        print("####")
        print("STIX OVERLAPPING REGIONS PARSED ({} seconds)".format(time.time() - start_task))
        return results
    
    def multiple_overlap(self,data): #TODO
        pass

class UCSC:
    def __init__(self):
        pass

    def getUCSCData(self, results):
        start_task = time.time()
        tablename = "hg19"
        with connect_SQL_db(app.config["UCSC_SQL_DB_HOST"], "genome") as db:
            df_metadata = pd.read_sql("SELECT tableName, shortLabel, longLabel, html from {}.trackDb order by tableName".format(tablename), con=db)
            df_results = pd.DataFrame(results, columns=["tableName","regionsize","overlap"])
            result = pd.merge(df_results, df_metadata, how='inner', on='tableName')
        result = result.fillna("")
        result = result.values.tolist()

        for data in result:
            data[5] = data[5].decode('latin-1') 
            if data[5] != "":
                data.append(self.getUCSCdescription(data[5]))
            else:
                data.append("")

        end_task = time.time()
        print("One Query with Pandas:", end_task - start_task)
        return result

    def getUCSCdescription(self, html):
        # Format of descriptions <H3>Description</H3> <P> ... <P> <h2>Description</h2> <p>
        if "Description" in html:
            result = re.search('^[ \t]*<[hH]{1}[0-9]{1}>[ \t]*Description[ \t]*<\/[hH]{1}[0-9]{1}>(.*?)<[pP]{1}>[ \t]*(.*?)<\/[pP]{1}>', html, flags = re.DOTALL)
            if result != None:
                htmldescr = result.group(0)
                index = htmldescr.find("<P>")
                if index == -1:
                    index = htmldescr.find("<p>")
                return htmldescr[index:len(htmldescr)]
        return ""