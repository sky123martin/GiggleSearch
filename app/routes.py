from __future__ import print_function
from flask import Flask, render_template, flash, request, redirect, session
from app import app
from app.forms import SearchForm, FilterResultsForm, Search#, FileUploadForm
from bs4 import BeautifulSoup as bs
from flask_wtf import Form
from flask_wtf.file import FileField
from werkzeug import secure_filename
from werkzeug.datastructures import CombinedMultiDict
import pandas as pd 
import numpy as np 
from multiprocessing.dummy import Pool as ThreadPool 
import multiprocessing
from flaskext.mysql import MySQL
import time
import math
import requests
import re

mysql = MySQL()
app.config['MYSQL_DATABASE_USER'] = 'genome'
app.config['MYSQL_DATABASE_DB'] = 'hg19'
app.config['MYSQL_DATABASE_HOST'] = 'genome-mysql.soe.ucsc.edu'
mysql.init_app(app)

@app.route('/', methods=['GET', 'POST'])
@app.route('/search', methods=['GET', 'POST'])
@app.route('/search/<inputtype>', methods=['GET', 'POST'])
def home(inputtype = None):
    if inputtype == None or inputtype == "manual":
        form = Search()
        inputtype = "manual"
        if form.validate_on_submit():
            print("Recieved Input:", form.Input.data)
            return parseManualSearch(form.Input.data)
    # else:
    #     inputtype = "file"
    #     form = FileUploadForm(CombinedMultiDict((request.files, request.form)))
    #     if form.validate_on_submit():
    #         f = form.file.data
    #         filename = secure_filename(f.filename)
    #         print("File Uploaded:", filename)
    #         print(f)

    print("Current Input Type: ", inputtype)
    return render_template('home.html', form = form, inputtype=inputtype)

def parseManualSearch(Input):
    ExtractedNumbers = re.findall('[0-9]{1,2}[ \t]*[0-9]{1,100}[ \t]*[:]*[ \t]*[0-9]{1,100}', Input, flags = re.IGNORECASE | re.LOCALE | re.MULTILINE)
    Source = re.findall('[A-Za-z]{3,4}$', Input, flags = re.IGNORECASE | re.LOCALE | re.MULTILINE)
        # ^[chromosomeCHROMOSOME]{0,10}[ \t]*[0-9]{1,2}[ \t]*([0-9]*[ \t]*:[ \t]*[0-9]*[ \t]*[ \t,&+])*from[ \t][A-Za-z]*
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

        return redirect("/result/{}/{}:{}-{}".format(Source[0], intervals[0][0], intervals[0][1], intervals[0][2]))
    else:
        print("Parser Error: No Match Found")
    return "Parser Error: No Match Found for input " + Input

@app.route("/result/<source>/<combined>", methods=['GET', 'POST'])
@app.route("/result/<source>/<combined>/pg:<page>", methods=['GET', 'POST'])
@app.route("/result/<source>/<combined>/pg:<page>/srt:<sort>-<asc>", methods=['GET', 'POST'])
@app.route("/result/<source>/<region>:<lowerBound>-<upperBound>", methods=['GET', 'POST'])
@app.route("/result/<source>/<region>:<lowerBound>-<upperBound>/pg:<page>", methods=['GET', 'POST'])
@app.route("/result/<source>/<region>:<lowerBound>-<upperBound>/pg:<page>/srt:<sort>-<asc>", methods=['GET', 'POST'])

def result(combined = None, source = None, region = None, lowerBound= None, upperBound = None, page=None, sort = None, asc = None):
    # Definition of forms:
    filterForm = FilterResultsForm()
    form = Search()
    print("Result recieved:", session.get('intervals', None))
    print("#")
    if combined == None:
        identifier = region + ":" + lowerBound + "-" + upperBound
    else:
        identifier = "combined"

    if filterForm.validate_on_submit():
        print("FILTERING SEARCH")
        return redirect("/result/{}/{}/pg:1/srt:{}-{}".format(source, identifier, filterForm.sortBy.data, filterForm.ascending.data))

    if form.validate_on_submit():
        print("Recieved Input:",form.Input.data)
        return parseManualSearch(form.Input.data)

    print("INITIATING SEARCH")
    start_total = time.time()

    if combined == None:
        overlap = getStixData([region, lowerBound, upperBound, source.lower()])
    elif combined == "combined":
        intevals = session.get('intervals', None)
        combinedIntervals = condenseintervals(intevals)
        pool = ThreadPool(len(combinedIntervals))
        allresults = pool.map(getStixData, combinedIntervals)
        if len(combinedIntervals) > 1:
            overlap = aggregate(allresults)

    start_task = time.time()

    if sort != None:
        overlap.sort(key = lambda ele : ele[int(sort)], reverse = bool(asc))
    else:
        overlap.sort(key = lambda ele : ele[2], reverse = 1)

    end_task = time.time()
    print("#####")
    print("FILTERING FOR SPECIFIED CONSTRAINTS ({} seconds)".format(end_task - start_task))
    #Pagination
    # determining results displayed on current page
    if page == None:
        page = 1
    else:
        page = int(page)

    maxpage = int(math.ceil(len(overlap)/10.0))
    if page < 7 or maxpage < 10:
        if maxpage < 10:
            pageNums = list(range(1, maxpage + 1))
        else:
            pageNums = list(range(1, 11))
    else:
        if maxpage < (page + 4):
            pageNums = list(range(page-5, maxpage + 1))
        else:
            pageNums = list(range(page-5, page + 5))
    currentpage = overlap[(page*10-10):(page*10)]
    print("Pagination",pageNums, page, maxpage)

    # make array of links for pages
    start_task = time.time()
    overlap = getDataInfo(overlap, source) #generic function to handle data information gathering
    end_task = time.time()
    print("########")
    print("DATA SOURCE INFOMATION COLLECTED ({} seconds)".format(end_task - start_task))
     
    currentpage = overlap[(page*10-10):(page*10)]

    end_total = time.time()
    print("##########")
    print("TOTAL SEARCH TIME ELAPSED {}".format(end_total - start_total))
    print("####################")
    print("RENDERING RESULTS {}-{}".format(page*10-10,page*10))
    print("########################################")
    return render_template('result.html', page = page, form = form, filterform = filterForm, pageNums=pageNums, results = currentpage, allresults = overlap, searchtime = end_total - start_total, numresults = len(overlap), source = source, identifier=identifier)

def aggregate(array):
    OGArray = pd.DataFrame(array[0], columns = ['tablename' , 'total', 'overlap'])
    test = pd.DataFrame(array[0], columns = ['tablename' , 'total', 'overlap'])
    for i in array:
        temp = pd.DataFrame(i, columns = ['tablename' , 'total', 'overlap'])
        OGArray = pd.merge(OGArray, temp, how="outer", on=['tablename', 'total']).fillna(0)
        test = pd.merge(test, temp, how="outer", on=['tablename', 'total']).fillna(0)
        OGArray['overlap'] = OGArray['overlap_x'] + OGArray['overlap_y']
        OGArray = OGArray[['tablename' , 'total', 'overlap']]

    # print(OGArray.head())
    # print(test.head())
    return OGArray.values.tolist()

def getStixData(data):
    region = data[0]
    lowerBound = data[1]
    upperBound = data[2]
    source = data[3]
    start_task = time.time()
    url = 'https://stix.colorado.edu/{}?region={}:{}-{}'.format(source.lower(), region, lowerBound, upperBound)
    print(url)
    request = requests.get(url)
    print("##")
    print("STIX REQUEST + RETURN ({} seconds)".format(time.time() - start_task))
    
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

def getDataInfo(data, source):
    if source == "UCSC" or source == "ucsc":
        return getUCSCData(data)
    else:
        return data

def getUCSCData(results):
    # Dataformat: [tablename, regionsize, overlap, shortname, longname, html, description]
    # 1. Query all at once and sort results
    print(results[1])
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
    result = pd.merge(dfresults, orderedlist, how='left', on='tableName')
    result = result.fillna("")
    result = result.values.tolist()

    for data in result:
        if data[5] != "":
            data.append(getUCSCdescription(data[5]))
        else:
            data.append("")

    end_task = time.time()
    print("One Query with Pandas:", end_task - start_task)

    ## 2. With multithreading on individual queries
    # start_task = time.time()
    # pool = ThreadPool(100) 
    # end = pool.map(queryUCSC, results)
    # end_task = time.time()
    # print("Multithreading:", end_task - start_task)
    # print(results)

    ### 3. Without multi threading on individual queries
    # start_task = time.time()
    # conn = mysql.connect()
    # cursor = conn.cursor()
    # final = []
    # for temp in results:
    #     final.append(queryUCSC(temp))
    # end_task = time.time()

    # print("Normal:",end_task-start_task)
    return result
 
def queryUCSC(tablename):
        conn = mysql.connect()
        cursor = conn.cursor()
        query = "SELECT shortLabel, longLabel, html from hg19.trackDb where tableName = '{}'".format(tablename[0])
        cursor.execute(query)
        data = cursor.fetchone()
        if data != None:
            tablename[0] = data[0] + ":  " + data[1]
            if data[2] == "":
               tablename.append("No further information on dataset found.") 
            else:
                tablename.append(data[2])
                tablename.append(getUCSCdescription(data[2]))
        else:
           tablename.append("No further information on dataset found.")
        return tablename

def getUCSCdescription(html):
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
    
def condenseintervals(intervals):
    CI = []
    for chrom in intervals:
        for interval in chrom:
            if len(CI) == 0:
                CI.append(interval)
            elif CI[len(CI)-1][0] == interval[0]:
                if CI[len(CI)-1][2] > interval[1] and CI[len(CI)-1][2] < interval[2]:
                    CI[len(CI)-1][2] = interval[2]
                elif CI[len(CI)-1][2] < interval[1]:
                    CI.append(interval)
            else:
                CI.append(interval)
    return CI