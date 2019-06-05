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
    
    results = getStixData('https://stix.colorado.edu/{}?region={}:{}-{}'.format(source, region, lowerBound, upperBound))
    conn = mysql.connect()
    cursor = conn.cursor()

    cursor.execute("SELECT tableName, shortLabel, longLabel, url, html from hg19.trackDb where tableName = 'affyU133Plus2'")
    data = cursor.fetchone()

    # cursor.execute("SELECT tableName, shortLabel, longLabel, url, html from hg19.trackDb where tableName = 'agilentCgh1x1m'")
    # result[0] = cursor.fetchone()
    
    
    
    
    if sortby!=None:
        results = sorted(results,reverse=True, key=lambda result: result[int(sortby)]) 

    searchForm = SearchForm()
    if searchForm.validate_on_submit():
        return redirect("/result/{}/{}:{}-{}".format(searchForm.dataSource.data, searchForm.region.data, searchForm.lowerBound.data, searchForm.upperBound.data))

    form = FilterResultsForm()
    if form.validate_on_submit():
        results = sorted(results,reverse = not form.Ascending.data, key=lambda result: result[int(form.sortBy.data)]) 
        return render_template('result.html', form=form, results = results, source = source, region = region, lowerBound = lowerBound, upperBound = upperBound)

# , data=data, data1=data1
    return render_template('result.html', data=data, searchForm=searchForm, form=form, results = results, source = source, region = region, lowerBound = lowerBound, upperBound = upperBound)

def getStixData(url):
    request = requests.get(url)
    soup = bs(request.text,"lxml")
    text = soup.text.split('\n') 
    results = []
    # conn = mysql.connect()
    # cursor = conn.cursor()

    for i in range(0,len(text)-1):
        temp = text[i].split("\t")
        split = temp[0].split("/")

        # cursor.execute("SELECT shortLabel, longLabel, html from hg19.trackDb where tableName = '{}'".format(temp[0]))
        # data = cursor.fetchone()
        # temp[0] = data #data[0]+ " - " +data[1]

        temp[1] = int(temp[1])
        temp[2] = int(temp[2])
        if len(split) == 2 :
            temp[0] = split[1]

        temp[0] = temp[0].split(".bed.gz")[0]
        temp.append(round(((temp[2]/temp[1])*100.0),10))

        if temp[2] > 0:
            results.append(temp)
    return results

def cleanHTML(html):