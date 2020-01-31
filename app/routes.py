from __future__ import print_function
from flask import Flask, render_template, flash, request, redirect
from app import app
from app.forms import Search, uploadForm
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
from utility import *
from utility import session
import requests
import re
import json


parse = userInput()
search = giggle()

@app.route('/', methods=['GET', 'POST'])
@app.route('/<inputtype>', methods=['GET', 'POST'])
@app.route('/search', methods=['GET', 'POST'])
@app.route('/search/<inputtype>', methods=['GET', 'POST'])
def home(inputtype = None, error = None):

    if inputtype == None or inputtype == "manual":
        form = Search()
        inputtype = "manual"
        if form.validate_on_submit() and error == None:
            print("Recieved Input:", form.Input.data)
            out = parse.parseManualSearch(form.Input.data)
            if isinstance(out, str): # parsing error occured
                return render_template('home.html', form = form, inputtype=inputtype, error=out)
            else:
                return redirect("/result/{}/{}:{}-{}".format(out[0][3], out[0][0], out[0][1], out[0][2]))        
    elif inputtype == "file":
        form = uploadForm(CombinedMultiDict((request.files, request.form)))
        if form.validate_on_submit():
            f = form.file.data
            filename = secure_filename(f.filename)
            print("File Uploaded:", filename)
    else:
        return render_template('home.html', form = Search(), inputtype=inputtype, error="Unknown input type")
    
    print("Current Input Type: ", inputtype)
    return render_template('home.html', form = form, inputtype=inputtype, error = "")

@app.route("/error", methods=['GET', 'POST'])
def errorHandling(errorCode, errorMessage):
    return render_template('404.html')


@app.route("/result/<source>/<region>:<lowerBound>-<upperBound>", methods=['GET', 'POST'])
def result(source, region, lowerBound, upperBound):
    try:
        # Definition of forms:
        form = Search()
        print("Result recieved:", session.get('intervals', None))
        print("#")
        identifier = [region, lowerBound, upperBound]

        if form.validate_on_submit():
            out = parse.parseManualSearch(form.Input.data)
            if isinstance(out, str): # parsing error occured
                return render_template('home.html', form = form, inputtype="manual", error=out)
            else:
                return redirect("/result/{}/{}:{}-{}".format(out[0][3], out[0][0], out[0][1], out[0][2]))

        print("INITIATING SEARCH")
        start_total = time.time()
        start_task = time.time()

        overlap = search.single_overlap([region, lowerBound, upperBound, source.lower()])

        overlap.sort(key = lambda ele : ele[2], reverse = 1)

        end_task = time.time()
        print("#####")
        print("FILTERING FOR SPECIFIED CONSTRAINTS ({} seconds)".format(end_task - start_task))
        #Pagination
        # determining results displayed on current page
        
        page = 1
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
        # [0 filename, 1 total region, 2 overlap, 3 short name, 4 long name, 5 description, 6 short description, 7 ID]
        i = 1
        for name in overlap:
            name.append(i)
            i = i +1
        return render_template('result.html', form = form, results = overlap, allresults = overlap, searchtime = end_total - start_total, sessionIntervals= session['intervals'], numresults = len(overlap), source = source, identifier=identifier, page = 1, pageNums=pageNums)
    except:
        return render_template('home.html', form = form, inputtype="manual", error="Unexpected error found, try again.")

def getDataInfo(data, source):
    if source == "UCSC" or source == "ucsc":
        return UCSC().getUCSCData(data)
    else:
        return data
