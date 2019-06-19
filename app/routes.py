from __future__ import print_function
from flask import Flask, render_template, flash, redirect
from app import app
from app.forms import SearchForm, FilterResultsForm
from bs4 import BeautifulSoup as bs
from flaskext.mysql import MySQL
import time
import requests
import re

mysql = MySQL()
app.config['MYSQL_DATABASE_USER'] = 'genome'
app.config['MYSQL_DATABASE_DB'] = 'hg19'
app.config['MYSQL_DATABASE_HOST'] = 'genome-mysql.soe.ucsc.edu'
mysql.init_app(app)

@app.route('/')
@app.route('/index')
@app.route('/home')
def index():
    return render_template('index.html')

@app.route('/search', methods=['GET', 'POST'])
def search():
    form = SearchForm()
    if form.validate_on_submit():
        return redirect("/result/{}/{}:{}-{}?result:1-10".format(form.dataSource.data, form.region.data, form.lowerBound.data, form.upperBound.data))
    return render_template('search.html', title='Region of Interest:', form=form)

@app.route("/result/<source>/<region>:<lowerBound>-<upperBound>", methods=['GET', 'POST'])
@app.route("/result/<source>/<region>:<lowerBound>-<upperBound>/pg:<page>", methods=['GET', 'POST'])
def result(source, region, lowerBound, upperBound, page=None):
    # Definition of forms:
    filterForm = FilterResultsForm()
    searchForm = SearchForm()
    print("#")
    if searchForm.validate_on_submit():
        print("REDIRECTING SEARCH")
        return redirect("/result/{}/{}:{}-{}".format(searchForm.dataSource.data, searchForm.region.data, searchForm.lowerBound.data, searchForm.upperBound.data))

    print("INITIATING SEARCH")
    start_total = time.time()

    overlap = getStixData(source, region, lowerBound, upperBound)

    start_task = time.time()
    if filterForm.validate_on_submit():
        overlap = sorted(overlap,reverse = not filterForm.Ascending.data, key=lambda result: overlap[int(filterForm.sortBy.data)]) 
    else:
        overlap = sorted(overlap,reverse = not filterForm.Ascending.data, key=lambda result: overlap[1])
    end_task = time.time()
    print("#####")
    print("FILTERING FOR SPECIFIED CONSTRAINTS ({} seconds)".format(end_task - start_task))

    # determining results displayed on current page
    if page == None:
        page = 1
        currentpage = overlap[0:10]
    else:
        page = int(page)
        currentpage = overlap[(page*10-10):(page*10)]


    # make array of links for pages


    start_task = time.time()
    currentpage = getDataInfo(currentpage, source) #generic function to handle data information gathering
    end_task = time.time()
    print("########")
    print("DATA SOURCE INFOMATION COLLECTED ({} seconds)".format(end_task - start_task))

    end_total = time.time()
    print("##########")
    print("TOTAL SEARCH TIME ELAPSED {}".format(end_total - start_total))
    print("####################")
    print("RENDERING RESULTS {}-{}".format(page*10-10,page*10))
    print("########################################")
    return render_template('result.html', page = page, searchForm=searchForm, form = filterForm, results = currentpage, searchtime = end_total - start_total, numresults = len(overlap), source = source, region = region, lowerBound = lowerBound, upperBound = upperBound)

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
            temp.append(round(((temp[2]/temp[1])*100.0),10))
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
    conn = mysql.connect()
    cursor = conn.cursor()
    for temp in results:
        query = "SELECT shortLabel, longLabel, html from hg19.trackDb where tableName = '{}'".format(temp[0])
        cursor.execute(query)
        data = cursor.fetchone()
        if data != None:
            temp[0] = data[0] + ":  " + data[1]
            if data[2] == "":
               temp.append("No further information on dataset found.") 
            else:
                temp.append(data[2])
                temp.append(getUCSCdescription(data[2]))
        else:
            temp.append("No further information on dataset found.")
    return results

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
    
