from . import sub as rs
from pathlib import Path
import numpy as np
import pandas as pd
from scipy import interpolate
import csv
import matplotlib as mpl
mpl.use('TkAgg')
import matplotlib.pyplot as plt

def roleplayRun():
    tOpSch = 20
    startYear = 2021
    lastYear = 2100
    NShipFleet = 20
    Alpha = 1
    tbid = 2

    path = str(Path(__file__).parent)
    path = path.replace('roleplay','parameters')
    parameterFile1 = path+"\\variableAll3.csv"
    parameterFile2 = path+"\\eqLHV.csv"
    parameterFile3 = path+"\\CO2Eff.csv"
    parameterFile4 = path+"\\unitCostFuel.csv"
    parameterFile5 = path+"\\costShipBasic.csv"
    parameterFile6 = path+"\\initialFleetA.csv"
    parameterFile7 = path+"\\initialFleetB.csv"
    parameterFile8 = path+"\\initialFleetC.csv"

    variableAll, valueDict = rs.readinput(parameterFile1)

    # prepare fleets
    fleets = {'S': np.zeros(lastYear-startYear+1)}
    fleets['year'] = np.zeros(lastYear-startYear+1)
    fleets.setdefault('output',{})
    fleets['output']['g'] = np.zeros(lastYear-startYear+1)
    fleets['output']['gTilde'] = np.zeros(lastYear-startYear+1)
    initialFleets = rs.initialFleetFunc(parameterFile6)
    for i in range(len(initialFleets)):
        orderYear = initialFleets[i]['year'] - tbid
        iniT = startYear - initialFleets[i]['year']
        iniCAPcnt = initialFleets[i]['TEU']
        fleets = rs.orderShipFunc(fleets,'HFO','0','0','0',iniCAPcnt,tOpSch,tbid,iniT,orderYear,parameterFile2,parameterFile3,parameterFile5)

    # start ship operation
    for elapsedYear in range(lastYear-startYear+1):
        cerrentYear = startYear+elapsedYear
        # scrap old fleet
        #numFleet = len(fleets)-2
        #for currentFleet in range(1,numFleet):
        #    if fleets[currentFleet]['tOp'] == tOpSch:
        #        print('    Fleet',currentFleet,'was scrapped due to too old.')

        # order & operate fleet by GUI
        #fleets = rs.orderShipInputFunc(fleets,tOpSch,tbid,0,startYear+elapsedYear,parameterFile2,parameterFile3,parameterFile5)
        #fleets = rs.yearlyOperationInputFunc(fleets,Di,startYear,elapsedYear,NShipFleet,Alpha,tOpSch,valueDict,parameterFile4)
        #rs.outputGUIFunc(fleets,startYear,elapsedYear,tOpSch)

        # order & operate fleet by Scenario
        fleets = rs.orderShipFunc(fleets,'HFO','1','1','1',10000,tOpSch,tbid,0,cerrentYear,parameterFile2,parameterFile3,parameterFile5)
        fleets = rs.yearlyOperationFunc(fleets,startYear,elapsedYear,NShipFleet,Alpha,tOpSch,valueDict,parameterFile4)
        
    rs.outputFunc(fleets,startYear,elapsedYear,lastYear,tOpSch)