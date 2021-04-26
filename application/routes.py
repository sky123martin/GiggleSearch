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
    genomes = utility.retrieve_genomes()
    genomes = genomes["GENOME"].unique()

    # interval search
    if request.method == 'POST' and intervalform.validate_on_submit() and error == "":
        print("Recieved Input:", intervalform.interval.data, intervalform.refGenome.data)
        if intervalform.refGenome.data=="": # parsing error occured
            return home("select reference genome")
        out = utility.parse_interval_input(intervalform.interval.data, intervalform.refGenome.data)
        if isinstance(out, str): # parsing error occured
            return home(out)
        else:
            session['intervals'] = [[int(i[0].split(":")[0]), int(i[0].split(":")[1].split("-")[0]), int(i[0].split(":")[1].split("-")[1]), i[1]] for i in out]
            session["LenIntervals"] = len(out)
            return redirect("/search/{}/{}".format(intervalform.refGenome.data,out[0][0]))   

    # file search
    elif request.method == 'POST' and error == "": # and 
        filename = secure_filename(fileform.file.data.filename)
        # check if the post request has the file part
        if 'file' not in request.files:
            return home("No selected file")
        
        result = request.form
        ref_genome = result['reference genome']

        file = request.files['file']

        if file.filename == '':
            return home("No selected file")
       
        if ref_genome == "":
            return home("No reference genome")

        if file.filename.split(".",1)[-1] not in app.config["ACCEPTED_FILE_FORMATS"]:
            return home("File {} is not an acceptable file format, accepted types:{}".format(file.filename, app.config["ACCEPTED_FILE_FORMATS"]))

        print("Recieved Input:",ref_genome, file.filename)
        if file:
            file_name = secure_filename(file.filename)
            process_id = str(random.randint(0,sys.maxsize))
            file.save(app.config["SERVER_PATH"] +  "/uploads/" + str(process_id) + "." + file_name.split(".", 1)[-1])
            return redirect("/search/{}/{}/{}".format(process_id, ref_genome, file_name))   

    return render_template('home.html', fileform = fileform, intervalform = intervalform, genomes = genomes, error = error)

@app.route("/search/<string:process_id>/<string:ref_genome>/<string:file_name>", methods=['GET', 'POST'])
def fileResult(process_id, ref_genome, file_name):
    print("INITIATING SEARCH")
    start_total = time.time()
    start_task = time.time()
    
    result_df = utility.file_search(process_id, ref_genome, file_name)
    if isinstance(result_df, str): # parsing error occured
        return home(result_df)

    end_task = time.time()
    print("#####")
    print("SEARCH COMPLETED ({} seconds)".format(end_task - start_task))

    result_df.reset_index(inplace=True)
    result_df = result_df.fillna("").sort_values("combo_score", ascending=False)
    result_df = result_df.to_dict(orient='records')
    results_json = json.dumps(result_df, indent=2)

    projects_df = utility.retrieve_projects(ref_genome)
    if isinstance(projects_df, str): # parsing error occured
        return home(projects_df)

    projects_df = projects_df.to_dict(orient='records')
    projects_json = json.dumps(projects_df, indent=2)

    end_total = time.time()

    print("##########")
    print("TOTAL SEARCH TIME ELAPSED {}".format(end_total - start_total))
    print("####################")

    return render_template('result.html',
                            results = results_json,
                            projects = projects_json,
                            searchtime = end_total - start_total,
                            file_name = file_name,
                            ref_genome = ref_genome
                            )

@app.route("/search/<string:ref_genome>/<string:chrom>:<int:lower>-<int:upper>", methods=['GET', 'POST'])
def intervalResult(ref_genome, chrom, lower, upper):
        print("INITIATING SEARCH")
        start_total = time.time()
        start_task = time.time()
        
        result_df = utility.interval_search(ref_genome, chrom, lower, upper)
        if isinstance(result_df, str): # parsing error occured
            return home(result_df)

        end_task = time.time()
        print("#####")
        print("SEARCH COMPLETED ({} seconds)".format(end_task - start_task))

        result_df.reset_index(inplace=True)
        result_df = result_df.fillna("").sort_values("overlaps", ascending=False)
        result_df = result_df.to_dict(orient='records')
        results_json = json.dumps(result_df, indent=2)

        projects_df = utility.retrieve_projects(ref_genome)
        if isinstance(projects_df, str): # parsing error occured
            return home(projects_df)

        projects_df = projects_df.to_dict(orient='records')
        projects_json = json.dumps(projects_df, indent=2)

        end_total = time.time()

        print("##########")
        print("TOTAL SEARCH TIME ELAPSED {}".format(end_total - start_total))
        print("####################")

        return render_template('result.html',
                                results = results_json,
                                projects = projects_json,
                                searchtime = end_total - start_total,
                                chrom = chrom,
                                lower_bound = lower,
                                upper_bound = upper,
                                ref_genome = ref_genome
                                )

@app.route("/<path:utter_none_sense>", methods=['GET', 'POST'])
@app.route("/error", methods=['GET', 'POST'])
def errorHandling(utter_none_sense):
    return render_template('404.html', utter_none_sense = "\"\\" + utter_none_sense +  "\"" + " does not exist.")

def getDataInfo(data, source):
    if source == "UCSC" or source == "ucsc":
        return UCSC.getUCSCData(data)
    else:
        return data

