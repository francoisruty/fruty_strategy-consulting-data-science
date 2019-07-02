# -*- coding: utf-8 -*-
from datetime import datetime
import string
printable = set(string.printable)
import os

import psycopg2
import pandas as pd
import matplotlib
matplotlib.use('Agg')
#cf https://stackoverflow.com/questions/2801882/generating-a-png-with-matplotlib-when-display-is-undefined
import matplotlib.pyplot as plt
import numpy as np

conn = psycopg2.connect("dbname='" + os.environ["PG_DATABASE"] + "' user='" + os.environ["PG_USER"] + "' host='postgres' password='" + os.environ["PG_PASSWORD"] + "'")
#Note: I had tried autocommit on false and manual commits because I thought it would help performance, but it brought issues due to concurrency I think
conn.autocommit = True
cur = conn.cursor()

def replaceSpecialChars(string):
    return filter(lambda x: x in printable, string)

def replaceAccents(string):
    string = string.replace("é","e")
    string = string.replace("ê","e")
    string = string.replace("è","e")
    string = string.replace("à","a")
    string = string.replace("â","a")
    string = string.replace("Â","A")
    string = string.replace("ù","u")
    string = string.replace("ô","o")
    string = string.replace("î","i")
    string = string.replace("ï","i")
    return string

def replaceCharForColumns(string):
    string = string.replace("-","_")
    string = string.replace("/","_")
    string = string.replace(" ","_")
    string = string.replace("(","_")
    string = string.replace(")","_")
    return string

def translateDate(string):
    try:
        string = string.lower()
    except Exception as e:
        print(e)
        print(string)
        raise Exception("pb with str.lower")
    string = replaceSpecialChars(string)
    months_fr = ["janvier","fvrier","fevrier","mars","avril","mai","juin","juillet","aout","aot","septembre","octobre","novembre","dcembre","decembre"]
    months_en = ["january","february","february","march","april","may","june","july","august","august","september","october","november","december","december"]
    for k in range(0,len(months_fr)):
        month_fr = months_fr[k]
        month_en = months_en[k]
        if month_fr in string:
            string = string.replace(month_fr,month_en)
    return string

def processLine(line,headers_types):
    if len(line) != len(headers_types):
        print(len(line))
        print(len(headers_types))
        print(line)
        print(headers_types)
        raise Exception("Len mismatch")
    line2 = []
    for k in range(0,len(line)):
        elt = line[k]
        type = headers_types[k]
        if elt == "":
            elt2 = "NULL"
        elif type["name"] == "NUMERIC":
            if isinstance(elt, basestring):
                if "," in elt:
                    try:
                        elt2 = float(elt.replace(",","."))
                    except:
                        print(elt)
                        raise Exception("Error parse float with ,")
                else:
                    try:
                        elt2 = float(elt)
                    except:
                        print(elt)
                        raise Exception("Error parse float")
            else:
                elt2 = elt
        elif type["name"] == "TIMESTAMP" or type["name"] == "INTERVAL" or type["name"] == "DATE":
            elt = translateDate(elt)
            format = type["format"]
            try:
                elt2 = datetime.strptime(elt, format)
            except Exception as e:
                print(elt)
                print(format)
                print(e)
                raise Exception("Error parsing datetime")
        elif type["name"] == "TEXT":
            #this str() caused unicode errors
            #elt = str(elt)
            elt2 = replaceSpecialChars(elt)
        else: #type TIME and all the rest
            #NOTE: for TIME type we don't use datetime.Strptime since it does not parse time of day, only datetime
            elt2 = elt
        line2.append(elt2)
    return line2

#NOTE: panda can read directly from excel file, and seems to be pretty good at recognizing types
def processExcelFile(excel_file, sheet_name, table, create_table):

    #we read data
    data = pd.read_excel(excel_file, sheet_name=sheet_name)
    headers = []
    for header in data.columns:
        headers.append(header)
    headers_types = []
    for type in data.dtypes:
        if type == "object":
            headers_types.append({"name": "TEXT"})
        if type == "float64":
            headers_types.append({"name": "NUMERIC"})
        if type == "int64":
            headers_types.append({"name": "NUMERIC"})

    #we create table in DB
    if create_table == True:
        command = "CREATE TABLE " + table + " (id BIGSERIAL PRIMARY KEY," + "\n"
        for k in range(0,len(headers)-1):
            header = replaceCharForColumns(headers[k])
            type = headers_types[k]
            command = command + header + " " + type["name"] + "," + "\n"
        header = replaceCharForColumns(headers[len(headers)-1])
        type = headers_types[len(headers)-1]
        command = command + header + " " + type["name"] + "" + "\n"
        command = command + ");"
        print(command)
        cur.execute(command)

    counter = 0
    for index, line in data.iterrows():
        print(counter)
        line2 = processLine(line,headers_types)
        print(line2)
        stri = "(DEFAULT,"
        for k in range(0,len(headers)-1):
            stri = stri + "%s,"
        stri = stri + "%s)"
        args_str = cur.mogrify(stri, line2)
        args_str = args_str.replace("'NULL'","NULL")
        args_str = args_str.replace("'NaN'","NULL")
        args_str = args_str.replace("'nan'","NULL")
        args_str = args_str.replace("NULL::float","NULL")
        try:
            cur.execute("INSERT INTO " + table + " VALUES " + args_str)
        except Exception as e:
            print(args_str)
            print(e)
            raise Exception("Error with DB insertion")
        counter = counter + 1


def drawCorr(df,name,method):
    corr = df.corr(method=method)
    fig = plt.figure()
    ax = fig.add_subplot(111)
    plt.subplots_adjust(top=0.6)
    plt.subplots_adjust(left=0.6)
    cax = ax.matshow(corr,cmap='coolwarm', vmin=-1, vmax=1)
    fig.colorbar(cax)
    ticks = np.arange(0,len(df.columns),1)
    ax.set_xticks(ticks)
    plt.xticks(rotation=90)
    ax.set_yticks(ticks)
    ax.set_xticklabels(df.columns)
    ax.set_yticklabels(df.columns)
    plt.savefig('./data/' + name + '.png')
