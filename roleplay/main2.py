from . import sub2 as rs
from pathlib import Path
import numpy as np
import pandas as pd
from scipy import interpolate
import csv
import matplotlib as mpl
#mpl.use('TkAgg')
import matplotlib.pyplot as plt
import os
import sys

#def roleplayRun(decisionListName1,decisionListName2,decisionListName3):
def roleplayRun():
    tOpSch = 20
    startYear = 2021
    regYear = [2025,2030,2035,2040,2045]
    lastYear = 2022
    NShipFleet = 6
    tbid = 2

    path = str(Path(__file__).parent)

    if os.name == 'nt':
        path = path.replace('roleplay','parameters') + '\\'
    elif os.name == 'posix':
        path = path.replace('roleplay','parameters') + '/'

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

    # prepare fleets
    fleets = {'year': np.zeros(lastYear-startYear+1)}
    fleets = rs.fleetPreparationFunc(fleets,parameterFile6,1,startYear,lastYear,0,tOpSch,tbid,valueDict,NShipFleet,parameterFile2,parameterFile12,parameterFile3,parameterFile5)
    fleets = rs.fleetPreparationFunc(fleets,parameterFile7,2,startYear,lastYear,0,tOpSch,tbid,valueDict,NShipFleet,parameterFile2,parameterFile12,parameterFile3,parameterFile5)
    fleets = rs.fleetPreparationFunc(fleets,parameterFile8,3,startYear,lastYear,0,tOpSch,tbid,valueDict,NShipFleet,parameterFile2,parameterFile12,parameterFile3,parameterFile5)

    # prepare regulator decision
    regDec = rs.regPreFunc(len(regYear)+1)
    
    # prepare dicisionList dictionary
    #decisionList = {}
    #decisionList.setdefault(1,rs.decisionListFunc(parameterFile9))
    #decisionList.setdefault(2,rs.decisionListFunc(parameterFile10))
    #decisionList.setdefault(3,rs.decisionListFunc(parameterFile11))

    # start ship operation
    nRegAct = 0
    nRegDec = 0
    for elapsedYear in range(lastYear-startYear+1):
        currentYear = startYear+elapsedYear
        fleets['year'][elapsedYear] = currentYear

        #'''
        # requlator's decision phase
        if currentYear == regYear[nRegDec]:
            nRegDec += 1
            regDec = rs.regDecFunc(regDec,nRegDec,currentYear)

        if nRegAct < len(regYear)-1:
            if currentYear == regYear[nRegAct+1]:
                nRegAct += 1

        # scrap & refurbish phase (also decide additional shipping fee per container)
        dcostTemp = np.zeros(3)
        dcostCntSum = 0
        playOrder = np.array([1,2,3])
        for numCompany in playOrder:
            fleets, dcostCntTemp = rs.scrapRefurbishFunc(fleets,numCompany,elapsedYear,currentYear,valueDict,tOpSch,regDec,nRegAct)
            dcostTemp[numCompany-1] = dcostCntTemp
            dcostCntSum += dcostCntTemp - valueDict["dcostCntMin"]

        # demand calculation
        Dtotal = rs.demandScenarioFunc(currentYear,valueDict["kDem1"],valueDict["kDem2"],valueDict["kDem3"],valueDict["kDem4"])
        Dasg = Dtotal * (dcostTemp - valueDict["dcostCntMin"]) / dcostCntSum
        playOrder = rs.playOrderFunc(dcostTemp,playOrder)
        
        # order & yearly operation phase
        overDi = 0
        for numCompany in playOrder:
            Di = Dasg[numCompany-1]
            fleets = rs.orderPhaseFunc(fleets,numCompany,valueDict,elapsedYear,tOpSch,tbid,currentYear,regDec,NShipFleet,parameterFile2,parameterFile12,parameterFile3,parameterFile5)
            fleets, overDi = rs.yearlyOperationPhaseFunc(fleets,numCompany,Di,overDi,startYear,elapsedYear,NShipFleet,tOpSch,valueDict,parameterFile4)
        #'''

        rs.outputGuiFunc(fleets,startYear,elapsedYear,lastYear,tOpSch,unitDict)
    
    rs.outputCsvFunc(fleets,elapsedYear)

    #rs.outputEachCompanyFunc(fleets,1,startYear,elapsedYear,lastYear,tOpSch,decisionListName1)
    #rs.outputEachCompanyFunc(fleets,2,startYear,elapsedYear,lastYear,tOpSch,decisionListName2)
    #rs.outputEachCompanyFunc(fleets,3,startYear,elapsedYear,lastYear,tOpSch,decisionListName3)
    #decisionListNameList = [decisionListName1, decisionListName2, decisionListName3]
    #rs.outputAllCompanyFunc(fleets,startYear,elapsedYear,lastYear,tOpSch,unitDict,decisionListNameList)

