from __future__ import print_function
from application import app

from flask import Flask, render_template, flash, request, redirect, session
from application.forms import Search, fileForm, intervalForm
from bs4 import BeautifulSoup as bs
from flask_wtf import Form
from flask_wtf.file import FileField
from werkzeug import secure_filename
from werkzeug.datastructures import CombinedMultiDict
import pandas as pd 
import numpy as np 
import random
import sys
import time
import math
import re
import json

from application import utility

@app.route('/', methods=['GET', 'POST'])
def home(error = ""):
    intervalform = intervalForm()
    fileform = fileForm(CombinedMultiDict((request.files, request.form)))

    # interval search
    if request.method == 'POST' and intervalform.validate_on_submit() and error == "":
        print("Recieved Input:", intervalform.Input.data)
        out = utility.parse_interval_input(intervalform.Input.data)
        if isinstance(out, str): # parsing error occured
            return render_template('home.html', fileform = fileform, intervalform = intervalform, error = out)
        else:
            session['intervals'] = [[int(i[0].split(":")[0]), int(i[0].split(":")[1].split("-")[0]), int(i[0].split(":")[1].split("-")[1]), i[1]] for i in out]
            session["LenIntervals"] = len(out)
            return redirect("/search/{}/{}".format(out[0][1],out[0][0]))   

    # file search
    elif request.method == 'POST' and error == "": #fileform.validate_on_submit() and 
        filename = secure_filename(fileform.file.data.filename)
        # check if the post request has the file part
        if 'file' not in request.files:
            return render_template('home.html', fileform = fileform, intervalform = intervalform, error = "No selected file")
        
        result = request.form
        ref_genome = result['reference genome']

        file = request.files['file']

        if file.filename == '':
            return render_template('home.html', fileform = fileform, intervalform = intervalform, error = "No selected file")
       
        if ref_genome == "":
            return render_template('home.html', fileform = fileform, intervalform = intervalform, error = "No reference genome")

        if file:
            file_name = secure_filename(file.filename)
            process_id = str(random.randint(0,sys.maxsize))
            file.save(app.config["SERVER_PATH"] +  "/uploads/" + str(process_id) + file_name.split(".", 1)[-1])
            return redirect("/search/{}/{}/{}".format(process_id, ref_genome, file_name))   

    return render_template('home.html', fileform = fileform, intervalform = intervalform, error = error)

@app.route("/search/<string:process_id>/<string:ref_genome>/<string:file_name>", methods=['GET', 'POST'])
def fileResult(process_id, ref_genome, file_name):
    form = Search()
    intervalform = intervalForm()
    fileform = fileForm(CombinedMultiDict((request.files, request.form)))

    if request.method == 'POST' and fileform.validate_on_submit():
        filename = secure_filename(fileform.file.data.filename)
        # check if the post request has the file part
        if 'file' not in request.files:
            return render_template('home.html', fileform = fileform, intervalform = intervalform, error = "No selected file")
        
        result = request.form
        ref_genome = result['reference genome']

        file = request.files['file']

        if file.filename == '':
            return render_template('home.html', fileform = fileform, intervalform = intervalform, error = "No selected file")
    
        if ref_genome == "":
            return render_template('home.html', fileform = fileform, intervalform = intervalform, error = "No reference genome")

        if file:
            file_name = secure_filename(file.filename)
            process_id = str(random.randint(0,sys.maxsize))
            file.save(app.config["SERVER_PATH"] +  "/uploads/" + str(process_id) + file_name.split(".", 1)[-1])
            return redirect("/search/{}/{}/{}".format(process_id, ref_genome, file_name))   

    out = utility.file_search(process_id, ref_genome, file_name)

    print("INITIATING SEARCH")
    start_total = time.time()
    start_task = time.time()
    
    if isinstance(out, str): # parsing error occured
        return render_template('home.html', fileform = fileform, intervalform = intervalform, error = out)
    else:
        result_df = out

    end_task = time.time()
    print("#####")
    print("SEARCH COMPLETED ({} seconds)".format(end_task - start_task))

    # make array of links for pages
    start_task = time.time()

    out = utility.retrieve_metadata(ref_genome) #generic function to handle data information gathering
    if isinstance(out, str): # parsing error occured
        return render_template('home.html', fileform = fileform, intervalform = intervalform, error = out)
    else:
        metadata_df = out

    result_df = pd.merge(result_df,
                         metadata_df,
                         left_on ="name",
                         right_on ="NAME",
                         how ="left")
    print(result_df)
    result_df.sort_values("overlaps", inplace=True)

    end_task = time.time()
    print("########")
    print("DATA SOURCE INFOMATION COLLECTED ({} seconds)".format(end_task - start_task))

    #Pagination
    # determining results displayed on current page
    
    current_page = 1
    number_pages = int(math.ceil(len(result_df.index)/10.0))
    if current_page < 7 or number_pages < 10:
        if number_pages < 10:
            displayed_page_numbers = list(range(1, number_pages + 1))
        else:
            displayed_page_numbers  = list(range(1, 11))
    else:
        if number_pages < (page + 4):
            displayed_page_numbers  = list(range(current_page-5, number_pages + 1))
        else:
            displayed_page_numbers  = list(range(current_page-5, current_page + 5))

    # EDIT BELOW
    current_page_results = result_df.iloc[(current_page*10-10):(current_page*10)]
    print("Pagination", displayed_page_numbers, current_page, number_pages)
    
    end_total = time.time()
    print("##########")
    print("TOTAL SEARCH TIME ELAPSED {}".format(end_total - start_total))
    print("####################")
    print("RENDERING RESULTS {}-{}".format(current_page*10-10, current_page*10))
    print("########################################")
    # [0 filename, 1 total region, 2 overlap, 3 short name, 4 long name, 5 description, 6 short description, 7 ID]
    result_df.reset_index(inplace=True)
    print(result_df.columns)

    result_df = result_df.fillna("").sort_values("fishers_two_tail")# FIX ME SHOULD this be asc
    results = result_df[["NAME", "file_size", "overlaps", "SHORTNAME", "LONGNAME", "LONGINFO", "SHORTINFO", "index", "combo_score"]].to_numpy()

    return render_template('file_result.html',
                            form = fileform,
                            results = results.tolist(),
                            searchtime = end_total - start_total,
                            file_name = file_name,
                            ref_genome = ref_genome,
                            numresults = len(result_df.index),
                            source = ref_genome,
                            page = 1,
                            pageNums = displayed_page_numbers)

@app.route("/search/<string:ref_genome>/<string:chrom>:<int:lower>-<int:upper>", methods=['GET', 'POST'])
def intervalResult(ref_genome, chrom, lower, upper):
    form = Search()
    intervalform = intervalForm()
    fileform = fileForm(CombinedMultiDict((request.files, request.form)))
    
    current_interval = [str(chrom) + ":" + str(lower) + "-" + str(upper), ref_genome]
    if session.get('intervals', None) == None:
        session["intervals"] = [[chrom, lower, upper, ref_genome] ]
        
    print("Result recieved:", session.get('intervals', None))
    print("#")

    if form.validate_on_submit():
        out = utility.parse_interval_input(form.Input.data)
        if isinstance(out, str): # parsing error occured
            return render_template('home.html', fileform = fileform, intervalform = intervalform, error = out)
        else:
            session['intervals'] = [[int(i[0].split(":")[0]), int(i[0].split(":")[1].split("-")[0]), int(i[0].split(":")[1].split("-")[1]), i[1]] for i in out]
            return redirect("/result/{}/{}".format(out[0][1], out[0][0]))

    print("INITIATING SEARCH")
    start_total = time.time()
    start_task = time.time()

    out = utility.interval_search(ref_genome, chrom, lower, upper)

    if isinstance(out, str): # parsing error occured
        return render_template('home.html', fileform = fileform, intervalform = intervalform, error = out)
    else:
        result_df = out

    end_task = time.time()
    print("#####")
    print("SEARCH COMPLETED ({} seconds)".format(end_task - start_task))

    # make array of links for pages
    start_task = time.time()

    out = utility.retrieve_metadata(ref_genome) #generic function to handle data information gathering
    if isinstance(out, str): # parsing error occured
        return render_template('home.html', fileform = fileform, intervalform = intervalform, error = out)
    else:
        metadata_df = out

    result_df = pd.merge(result_df,
                         metadata_df,
                         left_on ="name",
                         right_on ="NAME",
                         how ="left")
    print(result_df)
    result_df.sort_values("overlaps", ascending=False, inplace=True)

    end_task = time.time()
    print("########")
    print("DATA SOURCE INFOMATION COLLECTED ({} seconds)".format(end_task - start_task))

    #Pagination
    # determining results displayed on current page
    
    current_page = 1
    number_pages = int(math.ceil(len(result_df.index)/10.0))
    if current_page < 7 or number_pages < 10:
        if number_pages < 10:
            displayed_page_numbers = list(range(1, number_pages + 1))
        else:
            displayed_page_numbers  = list(range(1, 11))
    else:
        if number_pages < (page + 4):
            displayed_page_numbers  = list(range(current_page-5, number_pages + 1))
        else:
            displayed_page_numbers  = list(range(current_page-5, current_page + 5))

    # EDIT BELOW
    current_page_results = result_df.iloc[(current_page*10-10):(current_page*10)]
    print("Pagination", displayed_page_numbers, current_page, number_pages)
    
    end_total = time.time()
    print("##########")
    print("TOTAL SEARCH TIME ELAPSED {}".format(end_total - start_total))
    print("####################")
    print("RENDERING RESULTS {}-{}".format(current_page*10-10, current_page*10))
    print("########################################")
    # [0 filename, 1 total region, 2 overlap, 3 short name, 4 long name, 5 description, 6 short description, 7 ID]
    result_df.reset_index(inplace=True)
    print(result_df.columns)
    result_df = result_df.fillna("")
    results = result_df[["NAME", "size", "overlaps", "SHORTNAME", "LONGNAME", "LONGINFO", "SHORTINFO", "index"]].to_numpy()

    print(session.get('intervals', None))
    return render_template('interval_result.html',
                            current_interval = current_interval,
                            current_interval_split = [chrom, lower, upper, ref_genome],
                            form = form,
                            results = results.tolist(),
                            searchtime = end_total - start_total,
                            sessionIntervals = session['intervals'],
                            numresults = len(result_df.index),
                            source = ref_genome,
                            page = 1,
                            pageNums = displayed_page_numbers)
    # except:
    #     return render_template('home.html', form = form, inputtype="manual", error="Unexpected error found, try again.")

    # except:
    #     return render_template('404.html', utterNoneSense = "Unexpected error found, try again.")

@app.route("/<path:utter_none_sense>", methods=['GET', 'POST'])
@app.route("/error", methods=['GET', 'POST'])
def errorHandling(utter_none_sense):
    return render_template('404.html', utter_none_sense = "\"\\" + utter_none_sense +  "\"" + " does not exist.")

def getDataInfo(data, source):
    if source == "UCSC" or source == "ucsc":
        return UCSC.getUCSCData(data)
    else:
        return data

