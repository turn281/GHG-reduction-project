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

def roleplayRun(decisionListName1,decisionListName2,decisionListName3):
    tOpSch = 20
    startYear = 2020
    lastYear = 2050
    NShipFleet = 6
    Alpha = 1
    tbid = 2

    path = str(Path(__file__).parent)

    if os.name == 'nt':
        path = path.replace('roleplay','parameters') + '\\'
    elif os.name == 'posix':
        path = path.replace('roleplay','parameters') + '/'

    parameterFile1 = path+"variableAll.csv"
    parameterFile2 = path+"eqLHV.csv"
    parameterFile3 = path+"CO2Eff.csv"
    parameterFile4 = path+"unitCostFuel.csv"
    parameterFile5 = path+"costShipBasic.csv"
    parameterFile6 = path+"initialFleet1.csv"
    parameterFile7 = path+"initialFleet2.csv"
    parameterFile8 = path+"initialFleet3.csv"
    parameterFile9 = path+decisionListName1+".csv"
    parameterFile10 = path+decisionListName2+".csv"
    parameterFile11 = path+decisionListName3+".csv"

    variableAll, valueDict, unitDict = rs.readinput(parameterFile1)

    # prepare fleets
    fleets = {'year': np.zeros(lastYear-startYear+1)}
    fleets = rs.fleetPreparationFunc(fleets,parameterFile6,1,startYear,lastYear,tOpSch,tbid,parameterFile2,parameterFile3,parameterFile5)
    fleets = rs.fleetPreparationFunc(fleets,parameterFile7,2,startYear,lastYear,tOpSch,tbid,parameterFile2,parameterFile3,parameterFile5)
    fleets = rs.fleetPreparationFunc(fleets,parameterFile8,3,startYear,lastYear,tOpSch,tbid,parameterFile2,parameterFile3,parameterFile5)
    
    # prepare dicisionList dictionary
    decisionList = {}
    decisionList.setdefault(1,rs.decisionListFunc(parameterFile9))
    decisionList.setdefault(2,rs.decisionListFunc(parameterFile10))
    decisionList.setdefault(3,rs.decisionListFunc(parameterFile11))

    # start ship operation
    playOrder = np.array([1,2,3])
    for elapsedYear in range(lastYear-startYear+1):
        currentYear = startYear+elapsedYear
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
        scoreTemp = []
        overDi = 0
        dcostCntSum = 0
        Dtotal = rs.demandScenarioFunc(currentYear,valueDict["kDem1"],valueDict["kDem2"],valueDict["kDem3"],valueDict["kDem4"])
        for numCompany in playOrder:
            if decisionList[numCompany][currentYear]['Fee'] >= valueDict["dcostCntMin"] and decisionList[numCompany][currentYear]['Fee'] <= valueDict["dcostCntMax"]:
                dcostCntSum += decisionList[numCompany][currentYear]['Fee'] - valueDict["dcostCntMin"]
            else:
                print('ERROR: dcostCnt should be more equal than {0} and less equal than {1}, but now {2}. '.format(valueDict["dcostCntMin"], valueDict["dcostCntMax"], decisionList[numCompany][currentYear]['Fee']))
                sys.exit()

        for numCompany in playOrder:
            if decisionList[numCompany][currentYear]['Order']:
                if decisionList[numCompany][currentYear]['CAP'] >= valueDict["CAPcntMin"] and decisionList[numCompany][currentYear]['CAP'] <= valueDict["CAPcntMax"]:
                    fleets = rs.orderShipFunc(fleets,numCompany,decisionList[numCompany][currentYear]['fuelType'],decisionList[numCompany][currentYear]['WPS'],decisionList[numCompany][currentYear]['SPS'],decisionList[numCompany][currentYear]['CCS'],decisionList[numCompany][currentYear]['CAP'],tOpSch,tbid,0,currentYear,parameterFile2,parameterFile3,parameterFile5)
                else:
                    print('ERROR: CAPcnt should be more equal than {0} and less equal than {1}, but now {2}. '.format(valueDict["CAPcntMin"], valueDict["CAPcntMax"], decisionList[numCompany][currentYear]['CAP']))
                    sys.exit()
            Di = Dtotal * (decisionList[numCompany][currentYear]['Fee'] - valueDict["dcostCntMin"]) / dcostCntSum
            if decisionList[numCompany][currentYear]['Speed'] >= valueDict["vMin"]:
                fleets = rs.yearlyOperationFunc(fleets,numCompany,Di,startYear,elapsedYear,NShipFleet,Alpha,tOpSch,decisionList[numCompany][currentYear]['Speed'],valueDict,parameterFile4)
            else:
                print('ERROR: CAPcnt should be more equal than {0} , but now {1}. '.format(valueDict["vMin"], decisionList[numCompany][currentYear]['Speed']))
                sys.exit()
            scoreTemp.append(decisionList[numCompany][currentYear]['Fee'])
        
        playOrder = np.argsort(np.array(scoreTemp))[::-1] + 1
        
    #rs.outputEachCompanyFunc(fleets,1,startYear,elapsedYear,lastYear,tOpSch,decisionListName1)
    #rs.outputEachCompanyFunc(fleets,2,startYear,elapsedYear,lastYear,tOpSch,decisionListName2)
    #rs.outputEachCompanyFunc(fleets,3,startYear,elapsedYear,lastYear,tOpSch,decisionListName3)
    decisionListNameList = [decisionListName1, decisionListName2, decisionListName3]
    rs.outputAllCompanyFunc(fleets,startYear,elapsedYear,lastYear,tOpSch,unitDict,decisionListNameList)

