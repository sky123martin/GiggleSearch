from app import app, mysql
from flask import session
from bs4 import BeautifulSoup as bs
import pandas as pd 
import numpy as np 
from multiprocessing.dummy import Pool as ThreadPool 
import multiprocessing
from flaskext.mysql import MySQL
import time
import math
import requests
import re


class userInput:
    def parseManualSearch(self, Input):
        ExtractedNumbers = re.findall('[0-9]{1,2}[ \t]*[0-9]{1,100}[ \t]*[:]*[ \t]*[0-9]{1,100}', Input, flags = re.IGNORECASE | re.LOCALE | re.MULTILINE)
        Source = re.findall('[A-Za-z]{3,4}$', Input, flags = re.IGNORECASE | re.LOCALE | re.MULTILINE)
        if ExtractedNumbers != None and Source != None:
            print("Intervals Entered:",ExtractedNumbers)
            print("Source Entered:",Source)
            intervals = []
            for x in ExtractedNumbers:
                out = re.findall('[0-9]{1,100}', x)
                out.append(Source[0])
                out[0] = "chr" + out[0]
                if out != None:
                    intervals.append(out)

            if len(intervals)>1:
                intervals.sort(key = lambda x : (x[0], x[1]))
                print("Intervals:", intervals)
                sortedintv = []
                temp = [intervals[0]]
                for i in range(1,len(intervals)):
                    if intervals[i-1][0] != intervals[i][0]:
                        sortedintv.append(temp)
                        temp = []
                    temp.append(intervals[i])
                if temp != []:
                    sortedintv.append(temp)
                session['intervals'] = sortedintv
                session["LenIntervals"] = len(intervals)
            else:
                session['intervals'] = intervals
                session["LenIntervals"] = len(intervals)

            return intervals, Source
        else:
            print("Parser Error: No Match Found")
        return "Parser Error: No Match Found for input " + Input

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
        request = requests.get(url)
        print("##")
        print("Giggle REQUEST + RETURN ({} seconds)".format(time.time() - start_task))
        
        start_task = time.time()
        soup = bs(request.text,"lxml")
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
        conn = mysql.connect()
        cursor = conn.cursor()
        query = "SELECT tableName, shortLabel, longLabel, html from hg19.trackDb order by tableName"
        cursor.execute(query)
        orderedlist = []

        for row in cursor:
            orderedlist.append(row)
        orderedlist = pd.DataFrame(orderedlist, columns=["tableName", "shortLabel", "longLabel", "html"])
        dfresults = pd.DataFrame(results, columns=["tableName","regionsize","overlap"])
        result = pd.merge(dfresults, orderedlist, how='inner', on='tableName')
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