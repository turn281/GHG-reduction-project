# -*- coding: utf-8 -*-
from flask import Flask, render_template, request, redirect, url_for, jsonify, make_response, session, copy_current_request_context
from flask_socketio import SocketIO, emit, join_room, leave_room, close_room, rooms, disconnect
from threading import Lock
import time
import json
import numpy as np
from roleplay import sub2 as rs
from pathlib import Path
import pandas as pd
from scipy import interpolate
import csv
import matplotlib as mpl
import matplotlib.pyplot as plt
import os
import sys
import roleplay.sub2 as rs

async_mode = None
thread = None
thread_lock = Lock()
app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, async_mode=async_mode)

# My Functions
def background_thread():
    count = 0

# My Classes
class MyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        else:
            return super(MyEncoder, self).default(obj)

# prepare path for parameter files
path = str(Path(__file__).parent)
if os.name == 'nt':
    path = path+"\\parameters\\"
elif os.name == 'posix':
    path = path+"/parameters/"
parameterFile1 = path+"variableAll.csv"
parameterFile2 = path+"eqLHVship.csv"
parameterFile3 = path+"CO2Eff.csv"
parameterFile4 = path+"unitCostFuel.csv"
parameterFile5 = path+"costShipBasic.csv"
parameterFile6 = path+"initialFleet1.csv"
parameterFile7 = path+"initialFleet2.csv"
parameterFile8 = path+"initialFleet3.csv"
#parameterFile9 = path+decisionListName1+".csv"
#parameterFile10 = path+decisionListName2+".csv"
#parameterFile11 = path+decisionListName3+".csv"
parameterFile12 = path+"eqLHVaux.csv"

valueDict, unitDict = rs.readinput(parameterFile1)
tOpSch = int(valueDict['tOpSch'])
startYear = int(valueDict['startYear'])
lastYear = int(valueDict['lastYear'])
NShipFleet = int(valueDict['NShipFleet'])
tbid = int(valueDict['tbid'])
regYear = np.linspace(valueDict['regStart'],valueDict['lastYear'],int((valueDict['lastYear']-valueDict['regStart'])//valueDict['regSpan']+1))
#regYear = np.linspace(2021,valueDict['lastYear'],int((valueDict['lastYear']-valueDict['regStart'])//valueDict['regSpan']+1))

# prepare fleets
initialFleets = [parameterFile6,parameterFile7,parameterFile8]
fleets = {'year': np.zeros(lastYear-startYear+1)}

# prepare regulator decision
nRegAct = 0
nRegDec = 0
regDec = rs.regPreFunc(len(regYear)+1)

NshipComp = 0
Nregulator = 0
Nuser = 0
userDict = {}
regulatorIDs = []

# Routing
@app.route('/')
def index():
    global Nuser
    Nuser += 1
    return render_template('userSelection.html', Nuser=Nuser)

@socketio.event
def connect_event(message):
    global thread
    with thread_lock:
        if thread is None:
            thread = socketio.start_background_task(background_thread)
    emit('my_response_connect', {'no': message['no']})

@socketio.event
def userSelection_event(message):
    emit('my_response_userSelection', {'type': message['type'], 'name': message['name'], 'no': message['no']}, broadcast=True)

@socketio.event
def userSelected_event(message):
    global fleets
    global userDict
    global NshipComp
    global Nregulator
    global tOpSch
    global startYear
    global regulatorIDs
    global regDec
    global nRegAct
    userID = request.sid
    userNo = int(message['no'])
    userType = message['type']
    userName = message['name']
    userDict.setdefault(userID,{})
    userDict[userID]['userNo'] = userNo
    userDict[userID]['userType'] = userType
    userDict[userID]['userName'] = userName
    userDict[userID]['elapsedYear'] = 0
    if userType == 'Regulator':
        regulatorIDs.append(userID)
        Nregulator += 1
        userDict[userID]['Nregulator'] = Nregulator
        userDict[userID]['NshipComp'] = 0
        emit('my_response_selected_regulator', {'type': userType, 'name': userName, 'no': userNo, 'elpsyear': userDict[userID]['elapsedYear']})
    elif userType == 'Shipping Company':
        NshipComp += 1
        userDict[userID]['NshipComp'] = NshipComp
        userDict[userID]['Nregulator'] = 0
        fleets = rs.fleetPreparationFunc(fleets,np.random.choice(initialFleets),NshipComp,startYear,lastYear,0,tOpSch,tbid,valueDict,NShipFleet,parameterFile2,parameterFile12,parameterFile3,parameterFile5)
        for keyFleet in range(1,len(fleets[NshipComp])):
            if fleets[NshipComp][keyFleet]['delivery'] <= startYear and fleets[NshipComp][keyFleet]['tOp'] < tOpSch:
                tOpTemp = fleets[NshipComp][keyFleet]['tOp']
                rEEDIreqCurrent = rs.rEEDIreqCurrentFunc(fleets[NshipComp][keyFleet]['wDWT'],regDec['rEEDIreq'][nRegAct])
                fleets[NshipComp][keyFleet]['EEDIref'][tOpTemp], fleets[NshipComp][keyFleet]['EEDIreq'][tOpTemp] = rs.EEDIreqFunc(valueDict['kEEDI1'],fleets[NshipComp][keyFleet]['wDWT'],valueDict['kEEDI2'],rEEDIreqCurrent)
                fleets[NshipComp][keyFleet]['MCRM'][tOpTemp], fleets[NshipComp][keyFleet]['PA'][tOpTemp], fleets[NshipComp][keyFleet]['EEDIatt'][tOpTemp], fleets[NshipComp][keyFleet]['vDsgnRed'][tOpTemp] = rs.EEDIattFunc(fleets[NshipComp][keyFleet]['wDWT'],valueDict['wMCR'],valueDict['kMCR1'],valueDict['kMCR2'],valueDict['kMCR3'],valueDict['kPAE1'],valueDict['kPAE2'],valueDict['rCCS'],valueDict['vDsgn'],valueDict['rWPS'],fleets[NshipComp][keyFleet]['Cco2ship'],valueDict['SfcM'],valueDict['SfcA'],valueDict['rSPS'],fleets[NshipComp][keyFleet]['Cco2aux'],fleets[NshipComp][keyFleet]['EEDIreq'][tOpTemp],fleets[NshipComp][keyFleet]['WPS'],fleets[NshipComp][keyFleet]['SPS'],fleets[NshipComp][keyFleet]['CCS'])
        emit('my_response_selected_shipComp', {'type': userType, 'name': userName, 'no': userNo, 'elpsyear': userDict[userID]['elapsedYear'], 'fleets': json.dumps(fleets,cls=MyEncoder), 'tOpSch': tOpSch, 'currentYear': userDict[userID]['elapsedYear']+startYear,  'regulatorIDs': json.dumps(regulatorIDs,cls=MyEncoder)})
    
#emit('redirect',{url_for()})

@socketio.event
def cbs_event(message):
    global fleets
    global userDict
    global Nregulator
    global tOpSch
    global startYear
    global regulatorIDs
    global regDec
    global nRegAct
    userID = request.sid
    userNo = userDict[userID]['userNo']
    userType = userDict[userID]['userType']
    userName = userDict[userID]['userName']
    NshipComp = userDict[userID]['NshipComp']
    for keyFleet in range(1,len(fleets[NshipComp])):
        if fleets[NshipComp][keyFleet]['delivery'] <= startYear and fleets[NshipComp][keyFleet]['tOp'] < tOpSch:
            fleets[NshipComp][keyFleet]['WPS'] = message[str(keyFleet)]['WPS']
            fleets[NshipComp][keyFleet]['SPS'] = message[str(keyFleet)]['SPS']
            fleets[NshipComp][keyFleet]['CCS'] = message[str(keyFleet)]['CCS']
            tOpTemp = fleets[NshipComp][keyFleet]['tOp']
            rEEDIreqCurrent = rs.rEEDIreqCurrentFunc(fleets[NshipComp][keyFleet]['wDWT'],regDec['rEEDIreq'][nRegAct])
            fleets[NshipComp][keyFleet]['EEDIref'][tOpTemp], fleets[NshipComp][keyFleet]['EEDIreq'][tOpTemp] = rs.EEDIreqFunc(valueDict['kEEDI1'],fleets[NshipComp][keyFleet]['wDWT'],valueDict['kEEDI2'],rEEDIreqCurrent)
            fleets[NshipComp][keyFleet]['MCRM'][tOpTemp], fleets[NshipComp][keyFleet]['PA'][tOpTemp], fleets[NshipComp][keyFleet]['EEDIatt'][tOpTemp], fleets[NshipComp][keyFleet]['vDsgnRed'][tOpTemp] = rs.EEDIattFunc(fleets[NshipComp][keyFleet]['wDWT'],valueDict['wMCR'],valueDict['kMCR1'],valueDict['kMCR2'],valueDict['kMCR3'],valueDict['kPAE1'],valueDict['kPAE2'],valueDict['rCCS'],valueDict['vDsgn'],valueDict['rWPS'],fleets[NshipComp][keyFleet]['Cco2ship'],valueDict['SfcM'],valueDict['SfcA'],valueDict['rSPS'],fleets[NshipComp][keyFleet]['Cco2aux'],fleets[NshipComp][keyFleet]['EEDIreq'][tOpTemp],fleets[NshipComp][keyFleet]['WPS'],fleets[NshipComp][keyFleet]['SPS'],fleets[NshipComp][keyFleet]['CCS'])
    emit('my_response_refurbish', {'type': userType, 'name': userName, 'no': userNo, 'elpsyear': userDict[userID]['elapsedYear'], 'fleets': json.dumps(fleets,cls=MyEncoder), 'tOpSch': tOpSch, 'currentYear': userDict[userID]['elapsedYear']+startYear,  'regulatorIDs': json.dumps(regulatorIDs,cls=MyEncoder)})

'''@socketio.event
def my_event(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my_response',
         {'data': message['data'], 'count': session['receive_count']})'''


@socketio.event
def my_broadcast_event(message):
    global NshipComp
    NshipComp += 1
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my_response',
         {'data': message['data'], 'count': session['receive_count'], 'nshipcomp': str(NshipComp)},
         broadcast=True)


@socketio.event
def join(message):
    join_room(message['room'])
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my_response',
         {'data': 'In rooms: ' + ', '.join(rooms()),
          'count': session['receive_count']})


@socketio.event
def leave(message):
    leave_room(message['room'])
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my_response',
         {'data': 'In rooms: ' + ', '.join(rooms()),
          'count': session['receive_count']})


@socketio.on('close_room')
def on_close_room(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my_response', {'data': 'Room ' + message['room'] + ' is closing.',
                         'count': session['receive_count']},
         to=message['room'])
    close_room(message['room'])

@socketio.event
def my_room_event(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my_response',
         {'data': message['data'], 'count': session['receive_count']},
         to=message['room'])

@socketio.event
def disconnect_request():
    @copy_current_request_context
    def can_disconnect():
        disconnect()

    session['receive_count'] = session.get('receive_count', 0) + 1
    # for this emit we use a callback function
    # when the callback function is invoked we know that the message has been
    # received and it is safe to disconnect
    emit('my_response',
         {'data': 'Disconnected!', 'count': session['receive_count']},
         callback=can_disconnect)

@socketio.event
def my_ping():
    emit('my_pong')

@socketio.on('disconnect')
def test_disconnect():
    print('Client disconnected', request.sid)

'''@app.route('/')
def test():
    title = "User Selection"
    return render_template('userSelection.html', title=title)'''

'''@app.route('/userSelection', methods=['POST', 'GET'])
def userSelection():
    title = "User Selection"
    name = 'hoge'
    global NshipComp
    print(NshipComp)
    return render_template('userSelection.html', name=name, title=title)'''

'''@app.route('/shipCompScrpRfrb', methods=['POST', 'GET'])
def shipCompScrpRfrb():
    title = "Ship Company's Scrap & Refurbish"
    name = 'hoge'
    global NshipComp
    print(NshipComp)
    return render_template('shipCompScrpRfrb.html', name=name, title=title)

@app.route('/userSelected', methods=['POST', 'GET'])
def userSelected():
    title = "User Selected"
    global NshipComp
    global Nregulator
    global fleets
    if request.method == 'POST':
        userType = request.form.get('radio')
        name = request.form.get('name')
        if userType == 'regulator':
            Nregulator += 1
            return render_template('regulator.html', name=name, title=title)
        elif userType == 'shipComp':
            NshipComp += 1
            fleets = rs.fleetPreparationFunc(fleets,np.random.choice(initialFleets),NshipComp,startYear,lastYear,0,tOpSch,tbid,valueDict,NShipFleet,parameterFile2,parameterFile12,parameterFile3,parameterFile5)
            return render_template('shipCompScrpRfrb.html', name=name, fleets=fleets, NshipComp=NshipComp, Nregulator=Nregulator)
    else:
        return redirect(url_for('user'))'''


if __name__ == '__main__':
    #socketio.run(app, host='0.0.0.0', port=5001, debug=True)
    socketio.run(app, host='0.0.0.0', debug=True)

#http://localhost:3000/