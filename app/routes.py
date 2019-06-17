from flask import Flask, render_template, flash, redirect
from app import app
from app.forms import SearchForm, FilterResultsForm
from bs4 import BeautifulSoup as bs
from flaskext.mysql import MySQL
import requests

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
        return redirect("/result/{}/{}:{}-{}".format(form.dataSource.data, form.region.data, form.lowerBound.data, form.upperBound.data))
    return render_template('search.html', title='Region of Interest:', form=form)

@app.route("/result/<source>/<region>:<lowerBound>-<upperBound>", methods=['GET', 'POST'])
@app.route("/result/<source>/<sortby>/<region>:<lowerBound>-<upperBound>", methods=['GET', 'POST'])
def result(source, region, lowerBound, upperBound, sortby = None):
    
    overlap = getStixData(source, region, lowerBound, upperBound)

    conn = mysql.connect()
    cursor = conn.cursor()
    results = getUCSCData(overlap, conn, cursor)
    
    if sortby != None:
        results = sorted(results,reverse=True, key=lambda result: result[int(sortby)]) 

    searchForm = SearchForm()
    if searchForm.validate_on_submit():
        return redirect("/result/{}/{}:{}-{}".format(searchForm.dataSource.data, searchForm.region.data, searchForm.lowerBound.data, searchForm.upperBound.data))

    form = FilterResultsForm()
    if form.validate_on_submit():
        results = sorted(results,reverse = not form.Ascending.data, key=lambda result: result[int(form.sortBy.data)]) 
        return render_template('result.html', form=form, results = results, source = source, region = region, lowerBound = lowerBound, upperBound = upperBound)

    return render_template('result.html', searchForm=searchForm, form=form, results = results, source = source, region = region, lowerBound = lowerBound, upperBound = upperBound)

def getStixData(source, region, lowerBound, upperBound):
    url = 'https://stix.colorado.edu/{}?region={}:{}-{}'.format(source, region, lowerBound, upperBound)
    request = requests.get(url)
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
        if len(results)>50: #FIXME: TO LIMIT LOADING TIME, SEPERATE INDIVIDUAL PAGES 0-10 then 10-20 ect 
            break
    return results

def getUCSCData(results, conn, cursor):
    conn = mysql.connect()
    cursor = conn.cursor()
    for temp in results:
        query = "SELECT shortLabel, longLabel, html from hg19.trackDb where tableName = '{}'".format(temp[0])
        cursor.execute(query)
        data = cursor.fetchone()
        if data != None:
            temp[0] = data[0] + ":  " + data[1]
            temp.append(data[2])
        else:
            temp.append("No extra info")
    return results

def cleanHTML(html):
    #FIXME extract description for main page for mini view in main page
    #below is fix that didn't work to display html
    html = html.replace("&", " &amp; ")
    html = html.replace("<", " &lt; ")
    html = html.replace(">", " &gt; ")
    return html