#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "Bauyrzhan Ospan"
__copyright__ = "Copyright 2018, KazPostBot"
__version__ = "1.0.1"
__maintainer__ = "Bauyrzhan Ospan"
__email__ = "bospan@cleverest.tech"
__status__ = "Development"


from gevent import monkey
monkey.patch_all()


from flask import Flask, render_template, request, Markup, jsonify
from flask_socketio import SocketIO, emit, join_room, leave_room, \
	close_room, rooms, disconnect
import time
import random
from random import sample
import datetime
import socket
import json
from pymongo import MongoClient
import pymongo
import requests
from requests import Request, Session
from threading import Lock
import logging
from flask_basicauth import BasicAuth


async_mode = None

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, async_mode=async_mode)
thread = None
thread_lock = Lock()
app.config['JSON_AS_ASCII'] = False

app.config['BASIC_AUTH_USERNAME'] = 'b2u'
app.config['BASIC_AUTH_PASSWORD'] = 'kzb2uRK'

basic_auth = BasicAuth(app)

client = MongoClient('mongodb://database:27017/')


logging.basicConfig(level=logging.WARNING)


def tubes_calc(dash, needs):

    objects = dash.distinct("object")
    new_tubes = {"total": {"percent":[], "values":[], "average": 0, "needed": 0}}

    needsis = needs.find()
    needs_total = 0
    for n in needsis:
        needs_total = needs_total + float(n["m1"])

    for obj in objects:

        new_data = dash.find({'type': 'm1', 'object':obj}, sort=[( '_id', pymongo.DESCENDING )])
        new_dates = []
        new_values = []
        values = []
        times = []
        percent = []
        need1 = needs.find_one({"object": obj})["m1"]



        for date in new_data:
            time = datetime.datetime.fromtimestamp(date["time"]).strftime("%d.%m.%y")
            if not new_dates:
                if date["data"]!="0":
                    new_dates.append(time)
                    new_values.append(date["data"])
                    times.append(date["time"])
                    # values.append([new_dates[-1], (int(new_values[-1]))])
            else:
                if new_dates[-1]!=time and date["data"]!="0":
                    new_dates.append(time)
                    new_values.append(date["data"])
                    times.append(date["time"])
                    # values.append([new_dates[-1], (int(new_values[-1])-int(new_values[-2]))])
        
        new_values = new_values[::-1]
        times = times[::-1]
        new_dates = new_dates[::-1]

        for i in range(len(new_values)):
            if i>0:
                values.append([ datetime.datetime.timestamp(datetime.datetime.strptime(new_dates[i], "%d.%m.%y"))*1000 , int(new_values[i]) - int(new_values[i-1])])
                percent.append([ datetime.datetime.timestamp(datetime.datetime.strptime(new_dates[i], "%d.%m.%y"))*1000 , round(100*float(int(new_values[i]) - int(new_values[i-1]))/float(need1))])
            else:
                values.append([ datetime.datetime.timestamp(datetime.datetime.strptime(new_dates[i], "%d.%m.%y"))*1000 , int(new_values[i])])
                percent.append([ datetime.datetime.timestamp(datetime.datetime.strptime(new_dates[i], "%d.%m.%y"))*1000 , round(100*float(int(new_values[i]))/float(need1))])
        
        period = datetime.datetime.fromtimestamp(times[-1]) - datetime.datetime(2020, 7, 28, 0, 0, 0)
        average = round(float(new_values[-1])/period.days)
        period2 = 15
        needed = round(float(need1)/period2)

        # logging.warning("Объект: " + str(obj) + ", скорость сейчас: " + str(average) + ", а надо: " + str(needed))
        # logging.warning(values)
        # logging.warning(average)
        # logging.warning(needed)

        new_tubes[obj] = {"percent": percent, "values": values, "average": average, "needed": needed}
        new_tubes["total"]["average"] = new_tubes["total"]["average"] + new_tubes[obj]["average"]
        new_tubes["total"]["needed"] = new_tubes["total"]["needed"] + new_tubes[obj]["needed"]
        
    last_day = new_data = datetime.datetime.strptime(datetime.datetime.fromtimestamp(dash.find_one({'type': 'm1', 'object':obj}, sort=[( '_id', pymongo.DESCENDING )])["time"]).strftime("%d.%m.%y"), "%d.%m.%y")
    all_days = (last_day - datetime.datetime(2020, 7, 28, 0, 0, 0)).days

    for i in range(all_days):
        today = datetime.datetime(2020, 7, 28, 0, 0, 0) + datetime.timedelta(days=i)
        total = 0
        perc_total = 0
        for obj in objects:
            for i in range(len(new_tubes[obj]["values"])):
                if new_tubes[obj]["values"][i][0] == datetime.datetime.timestamp(today)*1000:
                    total = total + new_tubes[obj]["values"][i][1]
                    perc_total = perc_total + new_tubes[obj]["values"][i][1]
            
            
        new_tubes["total"]["values"].append([datetime.datetime.timestamp(today)*1000, total])
        new_tubes["total"]["percent"].append([datetime.datetime.timestamp(today)*1000, round((100*float(perc_total)/needs_total))])
    
    # logging.warning(new_tubes["total"]["values"])
    logging.warning(new_tubes)
    return new_tubes

        
def calculate(dash, needs, statuses, data_now_db):

    objects = dash.distinct("object")
    types = dash.distinct("type")

    consoles1 = dash.find_one({"type": "p1"}, sort=[( '_id', pymongo.DESCENDING )])["data"]
    consoles3 = dash.find_one({"type": "p2"}, sort=[( '_id', pymongo.DESCENDING )])["data"]
    rsh = dash.find_one({"type": "p3"}, sort=[( '_id', pymongo.DESCENDING )])["data"]
    krb = dash.find_one({"type": "p4"}, sort=[( '_id', pymongo.DESCENDING )])["data"]
    comp_station = dash.find_one({"type": "p5"}, sort=[( '_id', pymongo.DESCENDING )])["data"]
    vac_station = dash.find_one({"type": "p6"}, sort=[( '_id', pymongo.DESCENDING )])["data"]
    oxy_station = dash.find_one({"type": "p7"}, sort=[( '_id', pymongo.DESCENDING )])["data"]
    
    prod_oxy = dash.find_one({"type": "a1"}, sort=[( '_id', pymongo.DESCENDING )])["data"]
    delv_oxy = dash.find_one({"type": "a2"}, sort=[( '_id', pymongo.DESCENDING )])["data"]
    prod_vac = dash.find_one({"type": "a3"}, sort=[( '_id', pymongo.DESCENDING )])["data"]
    delv_vac = dash.find_one({"type": "a4"}, sort=[( '_id', pymongo.DESCENDING )])["data"]
    prod_comp = dash.find_one({"type": "a5"}, sort=[( '_id', pymongo.DESCENDING )])["data"]
    delv_comp = dash.find_one({"type": "a6"}, sort=[( '_id', pymongo.DESCENDING )])["data"]
    no_oxy = dash.find_one({"type": "a7"}, sort=[( '_id', pymongo.DESCENDING )])["data"]
    sum_station_prod = float(prod_oxy) + float(prod_vac) + float(prod_comp)

    obj_data = {"total": {"tubes": 0, "krb": 0, "rsh": 0, "cons1": 0, "cons3": 0, "vac": 0, "comp": 0, "oxy": 0}}
    needed_data = {"total": {"tubes": 0, "krb": 0, "rsh": 0, "cons1": 0, "cons3": 0, "vac": 0, "comp": 0, "oxy": 0}}

    for obj in objects:
        obj_data[obj] = {}
        needed_data[obj] = {}

        obj_data[obj]["tubes"] = dash.find_one({"type": "m1", "object": str(obj)}, sort=[( '_id', pymongo.DESCENDING )])["data"]
        obj_data["total"]["tubes"] = obj_data["total"]["tubes"] + int(obj_data[obj]["tubes"])
        needed_data[obj]["tubes"] = needs.find_one({"object": obj})["m1"]
        needed_data["total"]["tubes"] = needed_data["total"]["tubes"] + needs.find_one({"object": obj})["m1"]

        obj_data[obj]["krb"] = dash.find_one({"type": "m2", "object": str(obj)}, sort=[( '_id', pymongo.DESCENDING )])["data"]
        obj_data["total"]["krb"] = obj_data["total"]["krb"] + int(obj_data[obj]["krb"])
        needed_data[obj]["krb"] = needs.find_one({"object": obj})["m2"]
        needed_data["total"]["krb"] = needed_data["total"]["krb"] + needs.find_one({"object": obj})["m2"]

        obj_data[obj]["rsh"] = dash.find_one({"type": "m3", "object": str(obj)}, sort=[( '_id', pymongo.DESCENDING )])["data"]
        obj_data["total"]["rsh"] = obj_data["total"]["rsh"] + int(obj_data[obj]["rsh"])
        needed_data[obj]["rsh"] = needs.find_one({"object": obj})["m3"]
        needed_data["total"]["rsh"] = needed_data["total"]["rsh"] + needs.find_one({"object": obj})["m3"]

        obj_data[obj]["cons1"] = dash.find_one({"type": "m4", "object": str(obj)}, sort=[( '_id', pymongo.DESCENDING )])["data"]
        obj_data["total"]["cons1"] = obj_data["total"]["cons1"] + int(obj_data[obj]["cons1"])
        needed_data[obj]["cons1"] = needs.find_one({"object": obj})["m4"]
        needed_data["total"]["cons1"] = needed_data["total"]["cons1"] + needs.find_one({"object": obj})["m4"]

        obj_data[obj]["cons3"] = dash.find_one({"type": "m5", "object": str(obj)}, sort=[( '_id', pymongo.DESCENDING )])["data"]
        obj_data["total"]["cons3"] = obj_data["total"]["cons3"] + int(obj_data[obj]["cons3"])
        needed_data[obj]["cons3"] = needs.find_one({"object": obj})["m5"]
        needed_data["total"]["cons3"] = needed_data["total"]["cons3"] + needs.find_one({"object": obj})["m5"]
        
        obj_data[obj]["vac"] = dash.find_one({"type": "m6", "object": str(obj)}, sort=[( '_id', pymongo.DESCENDING )])["data"]
        obj_data["total"]["vac"] = obj_data["total"]["vac"] + int(obj_data[obj]["vac"])
        needed_data[obj]["vac"] = needs.find_one({"object": obj})["m6"]
        needed_data["total"]["vac"] = needed_data["total"]["vac"] + needs.find_one({"object": obj})["m6"]

        obj_data[obj]["comp"] = dash.find_one({"type": "m7", "object": str(obj)}, sort=[( '_id', pymongo.DESCENDING )])["data"]
        obj_data["total"]["comp"] = obj_data["total"]["comp"] + int(obj_data[obj]["comp"])
        needed_data[obj]["comp"] = needs.find_one({"object": obj})["m7"]
        needed_data["total"]["comp"] = needed_data["total"]["comp"] + needs.find_one({"object": obj})["m7"]

        obj_data[obj]["oxy"] = dash.find_one({"type": "m8", "object": str(obj)}, sort=[( '_id', pymongo.DESCENDING )])["data"]
        obj_data["total"]["oxy"] = obj_data["total"]["oxy"] + int(obj_data[obj]["oxy"])
        needed_data[obj]["oxy"] = needs.find_one({"object": obj})["m8"]
        needed_data["total"]["oxy"] = needed_data["total"]["oxy"] + needs.find_one({"object": obj})["m8"]

    needed_total_station = float(needed_data["total"]["oxy"]) + float(needed_data["total"]["comp"]) + float(needed_data["total"]["vac"])
    data_now = {}

    data_now["Проложено труб"] = str(round(100/float(needed_data["total"]["tubes"])*float(obj_data["total"]["tubes"]), 1)) + "%"
    data_now["Произведено консолей"] = str( round( 100/( float(needed_data["total"]["cons1"]) + float(needed_data["total"]["cons3"])) * ( float(consoles1) + float(consoles3)) , 1 ) ) + "%"
    data_now["Установлено консолей"] = str( round( 100/( float(needed_data["total"]["cons1"]) + float(needed_data["total"]["cons3"])) * ( float(obj_data["total"]["cons1"]) + float(obj_data["total"]["cons3"])) , 1 ) ) + "%"
    data_now["Произведено деталей в общем"] = str( round( 100/needed_total_station*sum_station_prod , 1) ) + "%"
    
    data_now["консоль1"] = {"надо": needed_data["total"]["cons1"], "есть": consoles1}
    data_now["консоль3"] = {"надо": needed_data["total"]["cons3"], "есть": consoles3}
    data_now["крб"] = {"надо": needed_data["total"]["krb"], "есть": krb}
    data_now["рш"] = {"надо": needed_data["total"]["rsh"], "есть": rsh}
    data_now["комп"] = {"надо": needed_data["total"]["comp"], "есть": comp_station}
    data_now["вак"] = {"надо": needed_data["total"]["vac"], "есть": vac_station}
    data_now["кис"] = {"надо": needed_data["total"]["oxy"], "есть": oxy_station , "без": no_oxy}
    
    data_now["Произведено деталей"] = {"надо": needed_data["total"]["oxy"], "есть": prod_oxy, "без": no_oxy}
    data_now["Доставлено деталей"] = {"надо": needed_data["total"]["oxy"], "есть": delv_oxy}

    data_now["vac_Произведено деталей"] = {"надо": needed_data["total"]["vac"], "есть": prod_vac}
    data_now["vac_Доставлено деталей"] = {"надо": needed_data["total"]["vac"], "есть": delv_vac}
    
    data_now["comp_Произведено деталей"] = {"надо": needed_data["total"]["comp"], "есть": prod_comp}
    data_now["comp_Доставлено деталей"] = {"надо": needed_data["total"]["comp"], "есть": delv_comp}

    data_now["Объекты"] = {"Общее": {
                "Проложено труб": {
                    "надо": needed_data["total"]["tubes"],
                    "есть": obj_data["total"]["tubes"]
                },
                "Установлено консолей 1": {
                    "надо": needed_data["total"]["cons1"],
                    "есть": obj_data["total"]["cons1"]
                },
                "Установлено консолей 3": {
                    "надо": needed_data["total"]["cons3"],
                    "есть": obj_data["total"]["cons3"]
                },
                "КРБ": {
                    "надо": needed_data["total"]["krb"],
                    "есть": obj_data["total"]["krb"]
                },
                "РШ": {
                    "надо": needed_data["total"]["rsh"],
                    "есть": obj_data["total"]["rsh"]
                },
                "Ваакум": {
                    "надо": needed_data["total"]["vac"],
                    "есть": obj_data["total"]["vac"]
                },
                "Воздух": {
                    "надо": needed_data["total"]["comp"],
                    "есть": obj_data["total"]["comp"]
                },
                "Кислород": {
                    "надо": needed_data["total"]["oxy"],
                    "есть": obj_data["total"]["oxy"]
                }
            }
        }
    
    for obj in objects:
        data_now["Объекты"][obj] = {
            "Проложено труб": {
                "надо": needed_data[obj]["tubes"],
                "есть": obj_data[obj]["tubes"]
            },
            "Установлено консолей 1": {
                "надо": needed_data[obj]["cons1"],
                "есть": obj_data[obj]["cons1"]
            },
            "Установлено консолей 3": {
                "надо": needed_data[obj]["cons3"],
                "есть": obj_data[obj]["cons3"]
            },
            "КРБ": {
                "надо": needed_data[obj]["krb"],
                "есть": obj_data[obj]["krb"]
            },
            "РШ": {
                "надо": needed_data[obj]["rsh"],
                "есть": obj_data[obj]["rsh"]
            },
            "Ваакум": {
                "надо": needed_data[obj]["vac"],
                "есть": obj_data[obj]["vac"]
            },
            "Воздух": {
                "надо": needed_data[obj]["comp"],
                "есть": obj_data[obj]["comp"]
            },
            "Кислород": {
                "надо": needed_data[obj]["oxy"],
                "есть": obj_data[obj]["oxy"]
            }
        }
    
    data_now["date"] = datetime.datetime.now().strftime("%d.%m")

    new_t = tubes_calc(dash, needs)

    data_now["tubes_data"] = new_t

    data_now["statuses"] = {"Общее": {}}

    for ob in statuses.find():
        data_now["statuses"][ob["object"]] = {"status1": ob["status1"], "proc1": ob["proc1"], "status2": ob["status2"], "proc2": ob["proc2"]}

    data_now_db.insert_one(data_now)


def calc_table(dash, needs, statuses, data_now_db):

    tubes_date = datetime.datetime(2020, 8, 20)
    cons_date = datetime.datetime(2020, 8, 20)
    krb_date = datetime.datetime(2020, 8, 20)
    station_date = datetime.datetime(2020, 8, 27)
    today = datetime.datetime.now()

    data2send = data_now_db.find_one(sort=[( '_id', pymongo.DESCENDING )])

    objects = dash.distinct("object")

    tubes_done = [0]*len(list(data2send["Объекты"].keys()))
    cons_installed = [0]*len(list(data2send["Объекты"].keys()))
    krbrsh_installed = [0]*len(list(data2send["Объекты"].keys()))
    station_installed = [0]*len(list(data2send["Объекты"].keys()))

    details = [0, 0, 0, 0, 0, 0, 0, 0]
    production = [0, 0, 0, 0, 0, 0, 0, 0]
    installed = [0, 0, 0, 0, 0, 0, 0, 0]

    temp0 = '''
    <table class="w3-table w3-striped w3-white">
          <tr>
            <td>Работы</td>
    '''

    temp1 = '''
    <tr>
            <td>Проложено труб внутри</td>
    '''

    temp2 = '''
    <tr>
            <td>Установлено консолей</td>
    '''

    temp3 = '''
    <tr>
            <td>Установлено КРБ/РШ</td>
    '''

    temp4 = '''
    <tr>
            <td>Установлено станций</td>
    '''


    for i in range(len(objects)):

        temp0 = temp0 + "<td>" + str(objects[i]) + "</td>"

        tubes = data2send["Объекты"][objects[i]]["Проложено труб"]["есть"]
        tubes_need = data2send["Объекты"][objects[i]]["Проложено труб"]["надо"]
        tube_done2 = round(float(100)/float(tubes_need)*float(tubes))

        con1 = data2send["Объекты"][objects[i]]["Установлено консолей 1"]["есть"]
        con3 = data2send["Объекты"][objects[i]]["Установлено консолей 3"]["есть"]

        con1_n = data2send["Объекты"][objects[i]]["Установлено консолей 1"]["надо"]
        con3_n = data2send["Объекты"][objects[i]]["Установлено консолей 3"]["надо"]

        c_all = round(float(100)/(float(con1_n)+float(con3_n))*(float(con1)+float(con3)))

        krb_done = data2send["Объекты"][objects[i]]["КРБ"]["есть"]
        rsh_done = data2send["Объекты"][objects[i]]["РШ"]["есть"]

        krb_need = data2send["Объекты"][objects[i]]["КРБ"]["надо"]
        rsh_need = data2send["Объекты"][objects[i]]["РШ"]["надо"]

        krb_rsh = round(float(100)/(float(krb_need)+float(rsh_need))*(float(krb_done)+float(rsh_done)))

        s1_done = data2send["Объекты"][objects[i]]["Ваакум"]["есть"]
        s2_done = data2send["Объекты"][objects[i]]["Воздух"]["есть"]
        s3_done = data2send["Объекты"][objects[i]]["Кислород"]["есть"]

        s1_need = data2send["Объекты"][objects[i]]["Ваакум"]["надо"]
        s2_need = data2send["Объекты"][objects[i]]["Воздух"]["надо"]
        s3_need = data2send["Объекты"][objects[i]]["Кислород"]["надо"]

        s_done = float(s1_done)+float(s2_done)+float(s3_done)
        s_need = float(s1_need)+float(s2_need)+float(s3_need)

        s = round(float(100)/float(s_need)*float(s_done))

        tubes_done[i] = tube_done2

        temp1 = temp1 + "<td>" + str(tube_done2) + "%</td>"

        cons_installed[i] = c_all

        temp2 = temp2 + "<td>" + str(c_all) + "%</td>"

        krbrsh_installed[i] = krb_rsh

        temp3 = temp3 + "<td>" + str(krb_rsh) + "%</td>"

        station_installed[i] = s

        temp4 = temp4 + "<td>" + str(s) + "%</td>"

    tubes_done.append( (tubes_date - today).days )
    cons_installed.append( (cons_date - today).days )
    krbrsh_installed.append( (krb_date - today).days )
    station_installed.append( (station_date - today).days )

    temp0 = temp0 + "<td>Срок дни</td></tr>"
    temp1 = temp1 + "<td>" + str((tubes_date - today).days) + "</td></tr>"
    temp2 = temp2 + "<td>" + str((cons_date - today).days) + "</td></tr>"
    temp3 = temp3 + "<td>" + str((krb_date - today).days) + "</td></tr>"
    temp4 = temp4 + "<td>" + str((station_date - today).days) + "</td></tr></table>"

    ## Details and production
    details[0] = round(100/float(data2send["консоль1"]["надо"])*1000)
    details[1] = round(100/float(data2send["консоль3"]["надо"])*100)
    details[2] = round(100/float(data2send["крб"]["надо"])*float(data2send["крб"]["есть"]))
    details[3] = round(100/float(data2send["рш"]["надо"])*float(data2send["рш"]["есть"]))
    details[4] = round(100/float(data2send["кис"]["надо"])*float(data2send["Доставлено деталей"]["есть"]))
    details[5] = round(100/float(data2send["vac_Доставлено деталей"]["надо"])*float(data2send["vac_Доставлено деталей"]["есть"]))
    details[6] = round(100/float(data2send["comp_Доставлено деталей"]["надо"])*float(data2send["comp_Доставлено деталей"]["есть"]))

    production[0] = round(100/float(data2send["консоль1"]["надо"])*float(data2send["консоль1"]["есть"]))
    production[1] = round(100/float(data2send["консоль3"]["надо"])*float(data2send["консоль3"]["есть"]))
    production[2] = round(100/float(data2send["крб"]["надо"])*float(data2send["крб"]["есть"]))
    production[3] = round(100/float(data2send["рш"]["надо"])*float(data2send["рш"]["есть"]))
    production[4] = round(100/float(data2send["кис"]["надо"])*float(data2send["кис"]["есть"]))
    production[5] = round(100/float(data2send["вак"]["надо"])*float(data2send["вак"]["есть"]))
    production[6] = round(100/float(data2send["комп"]["надо"])*float(data2send["комп"]["есть"]))

    installed[0] = round(100/float(data2send["Объекты"]["Общее"]["Установлено консолей 1"]["надо"])*float(data2send["Объекты"]["Общее"]["Установлено консолей 1"]["есть"]))
    installed[1] = round(100/float(data2send["Объекты"]["Общее"]["Установлено консолей 3"]["надо"])*float(data2send["Объекты"]["Общее"]["Установлено консолей 3"]["есть"]))
    installed[2] = round(100/float(data2send["Объекты"]["Общее"]["КРБ"]["надо"])*float(data2send["Объекты"]["Общее"]["КРБ"]["есть"]))
    installed[3] = round(100/float(data2send["Объекты"]["Общее"]["РШ"]["надо"])*float(data2send["Объекты"]["Общее"]["РШ"]["есть"]))
    installed[4] = round(100/float(data2send["Объекты"]["Общее"]["Кислород"]["надо"])*float(data2send["Объекты"]["Общее"]["Кислород"]["есть"]))
    installed[5] = round(100/float(data2send["Объекты"]["Общее"]["Ваакум"]["надо"])*float(data2send["Объекты"]["Общее"]["Ваакум"]["есть"]))
    installed[6] = round(100/float(data2send["Объекты"]["Общее"]["Воздух"]["надо"])*float(data2send["Объекты"]["Общее"]["Воздух"]["есть"]))

    tempg = '''
    <table class="w3-table w3-striped w3-white">
          <tr>
            <td>Тип работ</td>
            <td>Консоль 1 газ</td>
            <td>Консоль 3 газ</td>
            <td>КРБ</td>
            <td>РШ</td>
            <td>Ст. О2</td>
            <td>Вак. ст.</td>
            <td>Ст. воз.</td>
          </tr>
          <tr>
            <td>Заготовки и детали</td>
            <td>
    '''
    tempg = tempg + str(details[0]) + "%</td><td>" + str(details[1]) + "%</td><td>" + str(details[2]) + "%</td><td>" + str(details[3]) + "%</td><td>" + str(details[4]) + "%</td><td>" + str(details[5]) + "%</td><td>" + str(details[6]) + "%</td></tr><tr><td>Произведено</td><td>"
    tempg = tempg + str(production[0]) + "%</td><td>" + str(production[1]) + "%</td><td>" + str(production[2]) + "%</td><td>" + str(production[3]) + "%</td><td>" + str(production[4]) + "%</td><td>" + str(production[5]) + "%</td><td>" + str(production[6]) + "%</td></tr><tr><td>Установлено</td><td>"
    tempg = tempg + str(installed[0]) + "%</td><td>" + str(installed[1]) + "%</td><td>" + str(installed[2]) + "%</td><td>" + str(installed[3]) + "%</td><td>" + str(installed[4]) + "%</td><td>" + str(installed[5]) + "%</td><td>" + str(installed[6]) + "%</td></tr></table>"

    table = Markup(temp0 + temp1 + temp2 + temp3 + temp4 + tempg)

    return table


# Main page
@app.route("/", methods=["GET", "POST"])
@app.route("/<city>", methods=["GET", "POST"])
@basic_auth.required
def index(city=""):

    if city == "":
        db = client.b2u
        users = db['users']
        problems = db['problems']
        msgs = db['messages']
        dash = db['dash']
        needs = db['needs']
        data_now_db = db['data_now']
        sklad = db["sklad"]
        statuses = db["statuses"]
    elif city == "2esh":
        db = client["2esh"]
        users = db['users']
        problems = db['problems']
        msgs = db['messages']
        dash = db['dash']
        needs = db['needs']
        data_now_db = db['data_now']
        sklad = db["sklad"]
        statuses = db["statuses"]

    calculate(dash, needs, statuses, data_now_db)
    table = calc_table(dash, needs, statuses, data_now_db)
    senddata = data_now_db.find_one(sort=[( '_id', pymongo.DESCENDING )])
    senddata["_id"] = 0
    senddata = Markup(str(senddata))
    return render_template(
        "index.html", **locals())


@app.route("/enter", methods=["GET", "POST"])
def enter():
    return render_template(
        "enter.html", **locals())


# Main flask app
if __name__ == "__main__":
    socketio.run(app, host='0.0.0.0', port=8080, debug=True)