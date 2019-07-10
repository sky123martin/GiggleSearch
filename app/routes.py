from __future__ import print_function
from flask import Flask, render_template, flash, redirect
from app import app
from app.forms import SearchForm, FilterResultsForm, Search
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

mysql = MySQL()
app.config['MYSQL_DATABASE_USER'] = 'genome'
app.config['MYSQL_DATABASE_DB'] = 'hg19'
app.config['MYSQL_DATABASE_HOST'] = 'genome-mysql.soe.ucsc.edu'
mysql.init_app(app)

@app.route('/', methods=['GET', 'POST'])
@app.route('/home', methods=['GET', 'POST'])
@app.route('/search', methods=['GET', 'POST'])
def home():
    form = Search()
    if form.validate_on_submit():
        print("Recieved Input:",form.Input.data)
        return parseSearch(form.Input.data)

    return render_template('home.html', form=form)

def parseSearch(Input):
    result = re.search('^([0-9]*[ \t]*:[ \t]*[0-9]*[ \t]*[chromosome]{0,10}[ \t]*[0-9]{1,2}[ \t]*[ \t,&+])*from[ \t][A-Za-z]*', Input, flags = re.IGNORECASE | re.LOCALE | re.MULTILINE)
    if result != None:
        print("Match Found:",result.group(0))
        str = result.group(0)
        numbers = [ int(s) for s in str.split() if s.isdigit()]
        word_list = str.split()
        return redirect("/result/{}/chr{}:{}-{}".format(word_list[-1].lower(), numbers[2], numbers[0], numbers[1]))
    else:
        print("Parser Error: No Match Found")

@app.route("/result/<source>/<region>:<lowerBound>-<upperBound>", methods=['GET', 'POST'])
@app.route("/result/<source>/<region>:<lowerBound>-<upperBound>/pg:<page>", methods=['GET', 'POST'])
@app.route("/result/<source>/<region>:<lowerBound>-<upperBound>/pg:<page>/srt:<sort>-<asc>", methods=['GET', 'POST'])

def result(source, region, lowerBound, upperBound, page=None, sort = None, asc = None):
    # Definition of forms:
    filterForm = FilterResultsForm()
    form = Search()

    print("#")

    if filterForm.validate_on_submit():
        print("FILTERING SEARCH")
        return redirect("/result/{}/{}:{}-{}/pg:1/srt:{}-{}".format(source, region, lowerBound, upperBound, filterForm.sortBy.data, filterForm.ascending.data))

    if form.validate_on_submit():
        print("Recieved Input:",form.Input.data)
        return parseSearch(form.Input.data)

    print("INITIATING SEARCH")
    start_total = time.time()

    overlap = getStixData(source.lower(), region, lowerBound, upperBound)

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
    print(len(overlap),len(overlap)/10,math.ceil(len(overlap)/10))
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
    return render_template('result.html', page = page, form = form, filterform = filterForm, pageNums=pageNums, results = currentpage, searchtime = end_total - start_total, numresults = len(overlap), source = source, region = region, lowerBound = lowerBound, upperBound = upperBound)

def getStixData(source, region, lowerBound, upperBound):
    start_task = time.time()
    url = 'https://stix.colorado.edu/{}?region={}:{}-{}'.format(source, region, lowerBound, upperBound)
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
            # temp.append(round(((temp[2]/temp[1])*100.0),10))
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
    
