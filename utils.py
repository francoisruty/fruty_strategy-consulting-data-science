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

def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False

def replaceSpecialChars(string):
    try:
        #sometimes string is a numeric, I dunno why. We can't use str all the time since it crashes with special chars
        if is_number(string):
            string = str(string)
        return filter(lambda x: x in printable, string)
    except:
        print(type(string))
        print(string)
        raise ValueError("Error with replaceSpecialChars")

def replaceCharForColumns(string):
    string = string.replace("-","_")
    string = string.replace("/","_")
    string = string.replace(" ","_")
    string = string.replace("(","_")
    string = string.replace(")","_")
    return string


def processLine(line, headers_types):
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
        elif pd.isna(elt): #for NaT and NaN
            elt2 = "NULL"
        elif type == "float64" or type == "int64":
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
        elif type == "datetime64[ns]":
            elt2 = elt
        elif type == "object":
            elt2 = replaceSpecialChars(elt)
        else:
            elt2 = elt
        line2.append(elt2)
    return line2

#NOTE: panda can read directly from excel file, and seems to be pretty good at recognizing types
def processExcelFile(excel_file, sheet_name, table, create_table, offset):

    #we read data
    print("Reading Excel data...")
    data = pd.read_excel(excel_file, sheet_name=sheet_name, encoding='utf-8')
    print("Finished reading excel data.")
    headers = []
    for header in data.columns:
        headers.append(header)
    print("Detected headers types:")
    print(data.dtypes)

    print("headers:")
    print(headers)

    #we force all columns to contain only theoretical column dtype
    print("Forcing columns types...")
    for k in range(0,len(headers)):
        header = headers[k]
        type = data.dtypes[k]
        if type == "float64" or type == "int64":
            data[header] = pd.to_numeric(data[header], errors='coerce')
        if type == "datetime64[ns]":
            data[header] = pd.to_datetime(data[header], errors='coerce')
        if type == "object":
            data = data.astype({header:unicode})


    #we create table in DB
    if create_table == True:
        command = "CREATE TABLE " + table + " (id BIGSERIAL PRIMARY KEY," + "\n"
        for k in range(0,len(headers)-1):
            header = replaceCharForColumns(headers[k])
            if data.dtypes[k] == "float64" or data.dtypes[k] == "int64":
                type = "NUMERIC"
            elif data.dtypes[k] == "object":
                type = "TEXT"
            elif data.dtypes[k] == "datetime64[ns]":
                type = "TIMESTAMP"
            else:
                type = "TEXT"
            command = command + header + " " + type + "," + "\n"
        header = replaceCharForColumns(headers[len(headers)-1])
        if data.dtypes[len(headers)-1] == "float64" or data.dtypes[len(headers)-1] == "int64":
            type = "NUMERIC"
        elif data.dtypes[len(headers)-1] == "object":
            type = "TEXT"
        elif data.dtypes[len(headers)-1] == "datetime64[ns]":
            type = "TIMESTAMP"
        else:
            type = "TEXT"
        command = command + header + " " + type + "" + "\n"
        command = command + ");"
        print(command)
        cur.execute(command)

    counter = 0
    for index, line in data.iterrows():
        counter = counter + 1
        if (counter < offset):
            continue
        line2 = processLine(line, data.dtypes)
        #print(line2)
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
