import numpy as np
import pandas as pd
from scipy import interpolate
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, NavigationToolbar2Tk)
from matplotlib.backend_bases import key_press_handler
from matplotlib.figure import Figure
from matplotlib.font_manager import FontProperties
from matplotlib.ticker import ScalarFormatter
from flask import Flask, render_template, request
from tkinter import *
from tkinter import ttk
import sys
import os
import shutil
import random
from matplotlib.ticker import MaxNLocator
from pathlib import Path

def readinput(filename):
    csv_input = pd.read_csv(filepath_or_buffer=filename, encoding="utf_8", sep=",")
    #print("variableAll")
    #display(csv_input[0:24])
    #print("\n")
    symbol = csv_input['Symbol']
    value = csv_input['Value']
    unit = csv_input['Unit']
    valueDict = {}
    unitDict = {}
    for i, j, k in zip(symbol, value, unit):
        valueDict[i] = float(j)
        unitDict[i] = str(k)
    return valueDict, unitDict

def CeqLHVFunc(filename,fuelName):
    csv_input = pd.read_csv(filepath_or_buffer=filename, encoding="utf_8", sep=",")
    #print("CeqLHV")
    #display(csv_input)
    #print("\n")
    fuelType = csv_input['Fuel type']
    CeqLHV = csv_input['CeqLHV']
    fuelDict = {}
    for i, j in zip(fuelType, CeqLHV):
        fuelDict[i] = float(j)
    return fuelDict[fuelName]

def Cco2Func(filename,fuelName):
    csv_input = pd.read_csv(filepath_or_buffer=filename, encoding="utf_8", sep=",")
    #print("Cco2")
    #display(csv_input)
    #print("\n")
    fuelType = csv_input['Fuel type']
    Cco2 = csv_input['Cco2']
    Cco2Dict = {}
    for i, j in zip(fuelType, Cco2):
        Cco2Dict[i] = float(j)
    return Cco2Dict[fuelName]

def initialFleetFunc(filename):
    csv_input = pd.read_csv(filepath_or_buffer=filename, encoding="utf_8", sep=",")
    year = csv_input['Year']
    TEU = csv_input['TEU']
    iniFleetDict = {}
    k = 0
    for i, j in zip(year, TEU):
        iniFleetDict.setdefault(k,{})
        iniFleetDict[k]['year'] = int(i)
        iniFleetDict[k]['TEU'] = float(j)
        k += 1
    return iniFleetDict

def decisionListFunc(filename):
    csv_input = pd.read_csv(filepath_or_buffer=filename, encoding="utf_8", sep=",").fillna(0)
    Year = csv_input['Year']
    Order = csv_input['Order']
    fuelType = csv_input['Fuel type']
    WPS = csv_input['WPS']
    SPS = csv_input['SPS']
    CCS = csv_input['CCS']
    CAP = csv_input['CAP']
    Speed = csv_input['Speed']
    Fee = csv_input['Fee']
    valueDict = {}
    for i, j, k, l, m, n, o, p, q in zip(Year, Order, fuelType, WPS, SPS, CCS, CAP, Speed, Fee):
        valueDict.setdefault(int(i),{})
        valueDict[int(i)]['Order'] = int(j)
        valueDict[int(i)]['fuelType'] = k
        valueDict[int(i)]['WPS'] = int(l)
        valueDict[int(i)]['SPS'] = int(m)
        valueDict[int(i)]['CCS'] = int(n)
        valueDict[int(i)]['CAP'] = float(o)
        valueDict[int(i)]['Speed'] = float(p)
        valueDict[int(i)]['Fee'] = float(q)
    return valueDict

def fleetPreparationFunc(fleetAll,initialFleetFile,numCompany,startYear,lastYear,elapsedYear,tOpSch,tbid,valueDict,NShipFleet,parameterFile2,parameterFile12,parameterFile3,parameterFile5):
    fleetAll.setdefault(numCompany,{})
    fleetAll[numCompany].setdefault('total',{})
    compTotal = fleetAll[numCompany]['total']
    compTotal['sale'] = np.zeros(lastYear-startYear+1)
    compTotal['g'] = np.zeros(lastYear-startYear+1)
    compTotal['gTilde'] = np.zeros(lastYear-startYear+1)
    compTotal['costTilde'] = np.zeros(lastYear-startYear+1)
    compTotal['saleTilde'] = np.zeros(lastYear-startYear+1)
    compTotal['cta'] = np.zeros(lastYear-startYear+1)
    compTotal['overDi'] = np.zeros(lastYear-startYear+1)
    compTotal['costShipBasicHFO'] = np.zeros(lastYear-startYear+1)
    compTotal['costShip'] = np.zeros(lastYear-startYear+1)
    compTotal['costFuel'] = np.zeros(lastYear-startYear+1)
    compTotal['costAdd'] = np.zeros(lastYear-startYear+1)
    compTotal['costAll'] = np.zeros(lastYear-startYear+1)
    compTotal['maxCta'] = np.zeros(lastYear-startYear+1)
    compTotal['rocc'] = np.zeros(lastYear-startYear+1)
    compTotal['costRfrb'] = np.zeros(lastYear-startYear+1)
    compTotal['dcostCnt'] = np.zeros(lastYear-startYear+1)
    compTotal['dcostEco'] = np.zeros(lastYear-startYear+1)
    compTotal['nTransCnt'] = np.zeros(lastYear-startYear+1)

    initialFleets = initialFleetFunc(initialFleetFile)

    for i in range(len(initialFleets)):
        orderYear = initialFleets[i]['year'] - tbid
        iniT = startYear - initialFleets[i]['year']
        if iniT < 0:
            orderYear = initialFleets[i]['year']
            iniT = 0
        iniCAPcnt = initialFleets[i]['TEU']
        fleetAll = orderShipFunc(fleetAll,numCompany,'HFO',0,0,0,iniCAPcnt,tOpSch,tbid,iniT,orderYear,elapsedYear,valueDict,NShipFleet,parameterFile2,parameterFile12,parameterFile3,parameterFile5)
    return fleetAll

def unitCostFuelFunc(filename,fuelName,year):
    csv_input = pd.read_csv(filepath_or_buffer=filename, encoding="utf_8", sep=",")
    #print("unitCostFuel")
    #display(csv_input)
    #print("\n")
    measureYear = np.array(csv_input['Year'],dtype='float64')
    measureHFO = np.array(csv_input['HFO'],dtype='float64')
    measure = np.array(csv_input[fuelName],dtype='float64')
    fittedHFO = interpolate.interp1d(measureYear, measureHFO)
    fitted = interpolate.interp1d(measureYear, measure)
    if year >= 2020:
        interp = fitted(year)
        interpHFO = fittedHFO(year)
    else:
        interp = measure[0]
        interpHFO = measureHFO[0]
    return interp, interpHFO

def rShipBasicFunc(filename,fuelName,CAPcnt):
    csv_input = pd.read_csv(filepath_or_buffer=filename, encoding="utf_8", sep=",")
    #print("CeqLHV")
    #display(csv_input)
    #print("\n")
    fuelType = csv_input['Fuel type']
    rShipBasic = csv_input['rShipBasic']
    fuelDict = {}
    for i, j in zip(fuelType, rShipBasic):
        fuelDict[i] = float(j)
    return fuelDict[fuelName]

def wDWTFunc(kDWT1,CAPcnt,kDWT2):
    wDWT = kDWT1*CAPcnt+kDWT2
    return wDWT

def wFLDFunc(kFLD1,wDWT,kFLD2):
    wFLD = kFLD1*wDWT+kFLD2
    return wFLD

def dFunc(Dyear,Hday,v,Rrun):
    d = Dyear*Hday*v*Rrun
    return d

def fShipFunc(kShip1,kShip2,wDWT,wFLD,rocc,CNM2km,v,d,rWPS,windPr,CeqLHV):
    fShipORG = (kShip1/1000)*(wFLD-(1-kShip2*rocc)*wDWT)*(wFLD**(-1/3))*((CNM2km*v)**2)*CNM2km*d
    if windPr:
        fShip = CeqLHV*fShipORG*(1-rWPS)
    else:
        fShip = CeqLHV*fShipORG
    return fShipORG, fShip

def fAuxFunc(Dyear,Hday,Rrun,kAux1,kAux2,wDWT,rSPS,solar,CeqLHV):
    fAuxORG = Dyear*Hday*Rrun*(kAux1+kAux2*wDWT)/1000
    if solar:
        fAux = CeqLHV*fAuxORG*(1-rSPS)
    else:
        fAux = CeqLHV*fAuxORG
    return fAuxORG, fAux

def gFunc(Cco2ship,fShip,Cco2aux,fAux,rCCS,CCS):
    gORG = Cco2ship*fShip+Cco2aux*fAux
    if CCS:
        g = gORG*(1-rCCS)
    else:
        g = gORG
    return gORG, g

def maxCtaFunc(CAPcnt,d):
    maxCta = CAPcnt*d
    return maxCta

def ctaFunc(CAPcnt,rocc,d):
    cta = CAPcnt*rocc*d
    return cta

def costFuelFunc(unitCostFuelHFO, unitCostFuel, fShipORG, fAuxORG, fShip, fAux):
    costFuelORG = unitCostFuelHFO*(fShipORG+fAuxORG)
    costFuel = unitCostFuel*(fShip+fAux)
    dcostFuel = costFuel - costFuelORG
    return costFuelORG, costFuel, dcostFuel

def costShipFunc(kShipBasic1, CAPcnt, kShipBasic2, rShipBasic, dcostWPS, dcostSPS, dcostCCS, flagWPS, flagSPS, flagCCS):
    costShipBasicHFO = kShipBasic1 * CAPcnt + kShipBasic2
    costShipBasic = rShipBasic * costShipBasicHFO
    cAdditionalEquipment = 1
    if flagWPS:
        cAdditionalEquipment += dcostWPS
    elif flagSPS:
        cAdditionalEquipment += dcostSPS
    elif flagCCS:
        cAdditionalEquipment += dcostCCS
    costShipAdd = cAdditionalEquipment * costShipBasicHFO
    costShipAll = costShipBasic + costShipAdd
    return costShipBasicHFO, costShipBasic, costShipAdd, costShipAll

def additionalShippingFeeFunc(tOp, tOpSch, dcostFuelAll, costShipAll, costShipBasicHFO):
    if tOp <= tOpSch:
        dcostShipping = dcostFuelAll + (costShipAll-costShipBasicHFO)/tOpSch
    else:
        dcostShipping = dcostFuelAll
    return dcostShipping

def demandScenarioFunc(year,kDem1,kDem2,kDem3,kDem4):
    Di = (kDem1*year**2 + kDem2*year + kDem3)*1000000000/kDem4
    return Di

def playOrderFunc(cost,playOrder):
    unique, counts = np.unique(cost, return_counts=True)
    if np.amax(counts) == 1:
        playOrderNew = playOrder[np.argsort(cost)]
    elif np.amax(counts) == 2:
        minCost = np.amin(cost)
        maxCost = np.amax(cost)
        if minCost == unique[counts == 1]:
            playOrderNew = np.zeros(3)
            playOrderNew[0] = playOrder[cost == minCost]
            playOrderNew[1:3] = np.random.permutation(playOrder[cost!=minCost])
        else:
            playOrderNew = np.zeros(3)
            playOrderNew[2] = playOrder[cost == maxCost]
            playOrderNew[0:2] = np.random.permutation(playOrder[cost!=maxCost])
    else:
        playOrderNew = np.random.permutation(playOrder)
    return playOrderNew

def rEEDIreqCurrentFunc(wDWT,rEEDIreq):
    if wDWT >= 200000:
        rEEDIreqCurrent = rEEDIreq[0]
    elif wDWT >= 120000:
        rEEDIreqCurrent = rEEDIreq[1]
    else:
        rEEDIreqCurrent = rEEDIreq[2]
    return rEEDIreqCurrent

def EEDIreqFunc(kEEDI1,wDWT,kEEDI2,rEEDIreq):
    EEDIref = kEEDI1*wDWT**kEEDI2
    EEDIreq = (1-rEEDIreq/100)*EEDIref
    return EEDIref, EEDIreq

def EEDIattFunc(wDWT,wMCR,kMCR1,kMCR2,kMCR3,kPAE1,kPAE2,rCCS,vDsgn,rWPS,Cco2ship,SfcM,SfcA,rSPS,Cco2aux,EEDIreq,flagWPS,flagSPS,flagCCS):
    if wDWT < wMCR:
        MCRM = kMCR1*wDWT + kMCR2
    else:
        MCRM = kMCR3
    PA = kPAE1*MCRM+kPAE2

    def _EEDIcalc(vDsgnRed):
        if flagWPS:
            rWPStemp = rWPS
        else:
            rWPStemp = 0
        if flagSPS:
            rSPStemp = rSPS
        else:
            rSPStemp = 0
        if flagCCS:
            rCCStemp = rCCS
        else:
            rCCStemp = 0
        return ((1-rCCStemp)/(0.7*wDWT*vDsgnRed))*((1-rWPStemp)*Cco2ship*0.75*MCRM*SfcM*(vDsgnRed/vDsgn)**3 + (1-rSPStemp)*Cco2aux*PA*SfcA)

    vDsgnRed = vDsgn
    EEDIatt = _EEDIcalc(vDsgnRed)
    while EEDIatt > EEDIreq:
        vDsgnRed -= 1
        EEDIatt = _EEDIcalc(vDsgnRed)

    return MCRM, PA, EEDIatt, vDsgnRed

def regPreFunc(nDec):
    regDec = {}
    regDec['rEEDIreq'] = np.zeros((nDec,3))
    regDec['Subsidy'] = np.zeros(nDec)
    regDec['Ctax'] = np.zeros(nDec)
    regDec['rEEDIreq'][0,0] = 50
    regDec['rEEDIreq'][0,1] = 45
    regDec['rEEDIreq'][0,2] = 35
    #regDec['Subsidy'][0] = 
    #regDec['Ctax'][0] = 
    return regDec

def regDecFunc(regDec,nReg,currentYear):
    
    def _regDecGui1(regDec,nReg,currentYear):

        def _buttonCommand(regDec,nReg,root):
            regDec['rEEDIreq'][nReg,0] = float(v1.get()) / 100
            regDec['rEEDIreq'][nReg,1] = float(v2.get()) / 100
            regDec['rEEDIreq'][nReg,2] = float(v3.get()) / 100
            root.quit()
            root.destroy()

        root = Tk()
        root.title('Regulator : Reduction Rate for EEXI / EEDI in '+str(currentYear))
        width = 500
        height = 300
        placeX = root.winfo_screenwidth()/2 - width/2
        placeY = root.winfo_screenheight()/2 - height/2
        widgetSize = str(width)+'x'+str(height)+'+'+str(int(placeX))+'+'+str(int(placeY))
        root.geometry(widgetSize)

        # Frame
        frame = ttk.Frame(root, padding=20)
        frame.pack()

        # Checkbutton
        v1 = StringVar()
        v1.set('50')
        cb1 = ttk.Entry(frame, textvariable=v1)
        label1 = ttk.Label(frame, text='wDWT <= 200,000', padding=(5, 2))
        label11 = ttk.Label(frame, text='>= 0 [%]', padding=(5, 2))


        # Checkbutton
        v2 = StringVar()
        v2.set('45') # 初期化
        cb2 = ttk.Entry(frame, textvariable=v2)
        label2 = ttk.Label(frame, text='120,000 <= wDWT < 200,000', padding=(5, 2))
        label22 = ttk.Label(frame, text='>= 0 [%]', padding=(5, 2))

        # Checkbutton
        v3 = StringVar()
        v3.set('30') # 初期化
        cb3 = ttk.Entry(frame, textvariable=v3)
        label3 = ttk.Label(frame, text='wDWT < 120,000', padding=(5, 2))
        label33 = ttk.Label(frame, text='>= 0 [%]', padding=(5, 2))

        # Button
        button = ttk.Button(frame, text='Next', command=lambda: _buttonCommand(regDec,nReg,root))

        # Layout
        label11.grid(row=0, column=2)
        cb1.grid(row=0, column=1)
        label1.grid(row=0, column=0)
        label22.grid(row=1, column=2)
        cb2.grid(row=1, column=1)
        label2.grid(row=1, column=0)
        label33.grid(row=2, column=2)
        cb3.grid(row=2, column=1)
        label3.grid(row=2, column=0)
        button.grid(row=3, column=0, columnspan=2)

        root.deiconify()
        root.mainloop()

        return regDec

    def _regDecGui2(regDec,nReg,currentYear):

        def _buttonCommand(regDec,nReg,root):
            def inner():
                regDec['Subsidy'][nReg] = float(v1.get()) / 100
                regDec['Ctax'][nReg] = float(v2.get()) / 100
                root.quit()
                root.destroy()
                return regDec
            return inner

        root = Tk()
        root.title('Regulator : Subsidy & Ctax in'+str(currentYear))
        width = 500
        height = 300
        placeX = root.winfo_screenwidth()/2 - width/2
        placeY = root.winfo_screenheight()/2 - height/2
        widgetSize = str(width)+'x'+str(height)+'+'+str(int(placeX))+'+'+str(int(placeY))
        root.geometry(widgetSize)

        # Frame
        frame = ttk.Frame(root, padding=20)
        frame.pack()

        # Checkbutton
        v1 = StringVar()
        v1.set('50')
        cb1 = ttk.Entry(frame, textvariable=v1)
        label1 = ttk.Label(frame, text='Rsubs', padding=(5, 2))
        label11 = ttk.Label(frame, text='>= 0 [%]', padding=(5, 2))


        # Checkbutton
        v2 = StringVar()
        v2.set('45') # 初期化
        cb2 = ttk.Entry(frame, textvariable=v2)
        label2 = ttk.Label(frame, text='Rtax', padding=(5, 2))
        label22 = ttk.Label(frame, text='>= 0 [%]', padding=(5, 2))

        # Button
        button = ttk.Button(frame, text='Next', command=_buttonCommand(regDec,nReg,root))

        # Layout
        label11.grid(row=0, column=2)
        cb1.grid(row=0, column=1)
        label1.grid(row=0, column=0)
        label22.grid(row=1, column=2)
        cb2.grid(row=1, column=1)
        label2.grid(row=1, column=0)
        button.grid(row=2, column=0, columnspan=2)

        root.deiconify()
        root.mainloop()

        return regDec

    regDec = _regDecGui1(regDec,nReg,currentYear)
    regDec = _regDecGui2(regDec,nReg,currentYear)

    return regDec
    
def scrapRefurbishFunc(fleetAll,numCompany,elapsedYear,currentYear,valueDict,tOpSch,rEEDIreq):
    
    def _fleetListGui(fleetAll,numCompany):
        def _buttonCommand(root):
            root.quit()
            root.destroy()
        
        def _selectTree(event):
            for item in tree.selection():
                itemText = tree.item(item,"values")
                #print(itemText) #itemText[0]等で項目指定できる

        fleetNum = []
        fuelType = []
        CAP = []
        WPS = []
        SPS = []
        CCS = []
        vDsgnRed = []
        EEXIreq = []
        EEXIatt = []
        for keyFleet in fleetAll[numCompany].keys():
            if type(keyFleet) is int:
                compFleet = fleetAll[numCompany][keyFleet]
                tOpTemp = compFleet['tOp']
                if compFleet['delivery'] <= currentYear and compFleet['tOp'] < tOpSch:
                    rEEDIreqCurrent = rEEDIreqCurrentFunc(compFleet['wDWT'],rEEDIreq)
                    compFleet['EEDIref'][tOpTemp], compFleet['EEDIreq'][tOpTemp] = EEDIreqFunc(valueDict['kEEDI1'],compFleet['wDWT'],valueDict['kEEDI2'],rEEDIreqCurrent)
                    compFleet['MCRM'][tOpTemp], compFleet['PA'][tOpTemp], compFleet['EEDIatt'][tOpTemp], compFleet['vDsgnRed'][tOpTemp] = EEDIattFunc(compFleet['wDWT'],valueDict['wMCR'],valueDict['kMCR1'],valueDict['kMCR2'],valueDict['kMCR3'],valueDict['kPAE1'],valueDict['kPAE2'],valueDict['rCCS'],valueDict['vDsgn'],valueDict['rWPS'],compFleet['Cco2ship'],valueDict['SfcM'],valueDict['SfcA'],valueDict['rSPS'],compFleet['Cco2aux'],compFleet['EEDIreq'][tOpTemp],compFleet['WPS'],compFleet['SPS'],compFleet['CCS'])
                    fleetNum.append(keyFleet)
                    if compFleet['fuelName'] == 'HFO':
                        fuelType.append('HFO/Diesel')
                    else:
                        fuelType.append(compFleet['fuelName'])
                    CAP.append(compFleet['CAPcnt'])
                    if compFleet['WPS']:
                        WPS.append('Yes')
                    else:
                        WPS.append('No')
                    if compFleet['SPS']:
                        SPS.append('Yes')
                    else:
                        SPS.append('No')
                    if compFleet['CCS']:
                        CCS.append('Yes')
                    else:
                        CCS.append('No')
                    vDsgnRed.append(compFleet['vDsgnRed'][tOpTemp])
                    EEXIreq.append('{:.3g}'.format(compFleet['EEDIreq'][tOpTemp]))
                    EEXIatt.append('{:.3g}'.format(compFleet['EEDIatt'][tOpTemp]))


        fleetList = pd.DataFrame({'fleetNum': fleetNum,
                                  'fuelType': fuelType, 
                                  'CAP': CAP,
                                  'WPS': WPS,
                                  'SPS': SPS,
                                  'CCS': CCS,
                                  'vDsgnRed': vDsgnRed,
                                  'EEXIreq': EEXIreq,
                                  'EEXIatt': EEXIatt,})

        root = Tk()
        root.title('Company '+str(numCompany)+' : Alive Fleet List in '+str(currentYear))
        width = 1000
        height = 300
        placeX = root.winfo_screenwidth()/2 - width/2
        placeY = root.winfo_screenheight()/2 - height/2
        widgetSize = str(width)+'x'+str(height)+'+'+str(int(placeX))+'+'+str(int(placeY))
        root.geometry(widgetSize)

        tree = ttk.Treeview(root)
        tree["column"] = (1, 2, 3, 4, 5, 6, 7, 8, 9)
        tree["show"] = "headings"
        tree.heading(1, text="No.")
        tree.heading(2, text="Fuel type")
        tree.heading(3, text="CAP [TEU]")
        tree.heading(4, text="WPS")
        tree.heading(5, text="SPS")
        tree.heading(6, text="CCS")
        tree.heading(7, text="vMax [kt]")
        tree.heading(8, text="EEXIreq [g/(ton*NM)]")
        tree.heading(9, text="EEXIatt [g/(ton*NM)]")
        tree.column(1, width=40)
        tree.column(2, width=100)
        tree.column(3, width=100)
        tree.column(4, width=50)
        tree.column(5, width=50)
        tree.column(6, width=50)
        tree.column(7, width=80)
        tree.column(8, width=130)
        tree.column(9, width=130)


        for row in fleetList.itertuples():
            tree.insert("", "end", values=(row.fleetNum, row.fuelType, row.CAP, row.WPS, row.SPS,row.CCS, row.vDsgnRed, row.EEXIreq, row.EEXIatt))

        tree.bind("<<TreeviewSelect>>", _selectTree)
        tree.pack()
        


        # Frame
        frame = ttk.Frame(root, padding=20)
        frame.pack()
        # Button
        button = ttk.Button(frame, text='Next', command=lambda: _buttonCommand(root))

        # Layout
        button.grid(row=0, column=0, columnspan=2)

        root.deiconify()
        root.mainloop()

        return
    
    def _scrapOrRefurbishGui(compFleet,numFleet,tOpSch,valueDict):
        def _buttonCommandScrap(compFleet,root):
            compFleet['tOp'] = tOpSch
            root.quit()
            root.destroy()
        
        def _buttonCommandNext(root):
            root.quit()
            root.destroy()

        def _buttonCommandCheck(compFleet,valueDict,rEEDIreq,v,labelS,label14,label15,label16,Sys,button):
            tOpTemp = compFleet['tOp']
            compFleet[Sys] = int(v.get())
            compFleet['EEDIref'][tOpTemp], compFleet['EEDIreq'][tOpTemp] = EEDIreqFunc(valueDict['kEEDI1'],compFleet['wDWT'],valueDict['kEEDI2'],rEEDIreq)
            compFleet['MCRM'][tOpTemp], compFleet['PA'][tOpTemp], compFleet['EEDIatt'][tOpTemp], compFleet['vDsgnRed'][tOpTemp] = EEDIattFunc(compFleet['wDWT'],valueDict['wMCR'],valueDict['kMCR1'],valueDict['kMCR2'],valueDict['kMCR3'],valueDict['kPAE1'],valueDict['kPAE2'],valueDict['rCCS'],valueDict['vDsgn'],valueDict['rWPS'],compFleet['Cco2ship'],valueDict['SfcM'],valueDict['SfcA'],valueDict['rSPS'],compFleet['Cco2aux'],compFleet['EEDIreq'][tOpTemp],compFleet['WPS'],compFleet['SPS'],compFleet['CCS'])
                
            if compFleet[Sys]:
                labelS['text'] = 'Yes'
            else:
                labelS['text'] = 'No'
            label14['text'] = str(compFleet['vDsgnRed'][tOpTemp])
            label15['text'] = str('{:.3g}'.format(compFleet['EEDIreq'][tOpTemp]))
            label16['text'] = str('{:.3g}'.format(compFleet['EEDIatt'][tOpTemp]))
            if valueDict['vMin'] < compFleet['vDsgnRed'][tOpTemp]:
                button['state'] = 'normal'

        root = Tk()
        root.title('Company '+str(numCompany)+' : Scrap or Refurbish  in '+str(currentYear))
        width = 800
        height = 200
        placeX = root.winfo_screenwidth()/2 - width/2
        placeY = root.winfo_screenheight()/2 - height/2
        widgetSize = str(width)+'x'+str(height)+'+'+str(int(placeX))+'+'+str(int(placeY))
        root.geometry(widgetSize)

        # Frame
        frame = ttk.Frame(root, padding=20)
        frame.pack()

        # Label
        label0 = ttk.Label(frame, text='No.', padding=(5, 2))
        label00 = ttk.Label(frame, text=str(numFleet), padding=(5, 2))
        label1 = ttk.Label(frame, text='Fuel type', padding=(5, 2))
        label2 = ttk.Label(frame, text='CAP [TEU]', padding=(5, 2))
        label3 = ttk.Label(frame, text='WPS', padding=(5, 2))
        label4 = ttk.Label(frame, text='SPS', padding=(5, 2))
        label5 = ttk.Label(frame, text='CCS', padding=(5, 2))
        label6 = ttk.Label(frame, text='vMax [kt]', padding=(5, 2))
        label7 = ttk.Label(frame, text='EEXIreq [g/(ton*NM)]', padding=(5, 2))
        label8 = ttk.Label(frame, text='EEXIatt [g/(ton*NM)]', padding=(5, 2))
        if compFleet['fuelName'] == 'HFO':
            label9 = ttk.Label(frame, text='HFO/Diesel', padding=(5, 2))
        else:
            label9 = ttk.Label(frame, text=compFleet['fuelName'], padding=(5, 2))
        label10 = ttk.Label(frame, text=compFleet['CAPcnt'], padding=(5, 2))
        if compFleet['WPS']:
            label11 = ttk.Label(frame, text='Yes', padding=(5, 2))
        else:
            label11 = ttk.Label(frame, text='No', padding=(5, 2))
        if compFleet['SPS']:
            label12 = ttk.Label(frame, text='Yes', padding=(5, 2))
        else:
            label12 = ttk.Label(frame, text='No', padding=(5, 2))
        if compFleet['CCS']:
            label13 = ttk.Label(frame, text='Yes', padding=(5, 2))
        else:
            label13 = ttk.Label(frame, text='No', padding=(5, 2))
        tOpTemp = compFleet['tOp']
        label14 = ttk.Label(frame, text=compFleet['vDsgnRed'][tOpTemp], padding=(5, 2))
        label15 = ttk.Label(frame, text='{:.3g}'.format(compFleet['EEDIreq'][tOpTemp]), padding=(5, 2))
        label16 = ttk.Label(frame, text='{:.3g}'.format(compFleet['EEDIatt'][tOpTemp]), padding=(5, 2))

        rEEDIreqCurrent = rEEDIreqCurrentFunc(compFleet['wDWT'],rEEDIreq)

        # Button
        button1 = ttk.Button(frame, text='Scrap', command=lambda: _buttonCommandScrap(compFleet,root))
        if valueDict['vMin'] > compFleet['vDsgnRed'][tOpTemp]:
            button2 = ttk.Button(frame, text='Next', state='disabled', command=lambda: _buttonCommandNext(root))
        else:
            button2 = ttk.Button(frame, text='Next', command=lambda: _buttonCommandNext(root))

        # Checkbutton
        v1 = StringVar()
        if compFleet['WPS']:
            v1.set('1')
            cb1 = ttk.Checkbutton(frame, padding=(10), text='WPS', state='disable', command=lambda: _buttonCommandCheck(compFleet,valueDict,rEEDIreqCurrent,v1,label11,label14,label15,label16,'WPS',button2),variable=v1)
        else:
            v1.set('0')
            cb1 = ttk.Checkbutton(frame, padding=(10), text='WPS', command=lambda: _buttonCommandCheck(compFleet,valueDict,rEEDIreqCurrent,v1,label11,label14,label15,label16,'WPS',button2),variable=v1)

        # Checkbutton
        v2 = StringVar()
        if compFleet['SPS']:
            v2.set('1')
            cb2 = ttk.Checkbutton(frame, padding=(10), text='SPS', state='disable', command=lambda: _buttonCommandCheck(compFleet,valueDict,rEEDIreqCurrent,v2,label12,label14,label15,label16,'SPS',button2), variable=v2)
        else:
            v2.set('0')
            cb2 = ttk.Checkbutton(frame, padding=(10), text='SPS', command=lambda: _buttonCommandCheck(compFleet,valueDict,rEEDIreqCurrent,v2,label12,label14,label15,label16,'SPS',button2), variable=v2)

        # Checkbutton
        v3 = StringVar()
        if compFleet['CCS']:
            v3.set('1')
            cb3 = ttk.Checkbutton(frame, padding=(10), text='CCS', state='disable', command=lambda: _buttonCommandCheck(compFleet,valueDict,rEEDIreqCurrent,v3,label13,label14,label15,label16,'CCS',button2), variable=v3)
        else:
            v3.set('0')
            cb3 = ttk.Checkbutton(frame, padding=(10), text='CCS', command=lambda: _buttonCommandCheck(compFleet,valueDict,rEEDIreqCurrent,v3,label13,label14,label15,label16,'CCS',button2), variable=v3)

        # Layout
        label0.grid(row=0, column=0)
        label00.grid(row=1, column=0)
        label1.grid(row=0, column=1)
        label2.grid(row=0, column=2)
        label3.grid(row=0, column=3)
        label4.grid(row=0, column=4)
        label5.grid(row=0, column=5)
        label6.grid(row=0, column=6)
        label7.grid(row=0, column=7)
        label8.grid(row=0, column=8)
        label9.grid(row=1, column=1)
        label10.grid(row=1, column=2)
        label11.grid(row=1, column=3)
        label12.grid(row=1, column=4)
        label13.grid(row=1, column=5)
        label14.grid(row=1, column=6)
        label15.grid(row=1, column=7)
        label16.grid(row=1, column=8)
        cb1.grid(row=2, column=3)
        cb2.grid(row=2, column=4)
        cb3.grid(row=2, column=5)
        button1.grid(row=2, column=7)
        button2.grid(row=2, column=8)

        root.deiconify()
        root.mainloop()

        return compFleet

    def _dcostCntGui(fleetAll,numCompany,elapsedYear):
        def _buttonCommand(fleetAll,numCompany,elapsedYear,root,v):
            fleetAll[numCompany]['total']['dcostCnt'][elapsedYear] = v.get()
            root.destroy()
            root.quit()

        root = Tk()
        root.title('Company '+str(numCompany)+' : Additional Shipping Fee Per Container in '+str(currentYear))
        width = 500
        height = 200
        placeX = root.winfo_screenwidth()/2 - width/2
        placeY = root.winfo_screenheight()/2 - height/2
        widgetSize = str(width)+'x'+str(height)+'+'+str(int(placeX))+'+'+str(int(placeY))
        root.geometry(widgetSize)

        # Frame
        frame = ttk.Frame(root, padding=20)
        frame.pack()

        v1 = StringVar()
        v1.set('0')
        cb1 = ttk.Entry(frame, textvariable=v1)
        label1 = ttk.Label(frame, text='dcontCnt (-1000 <= dcostCnt <= 1000)', padding=(5, 2))
        label2 = ttk.Label(frame, text='Nominal shipping cost: 1500 $/container', padding=(5, 2))
        label3 = ttk.Label(frame, text='$', padding=(5, 2))

        button = ttk.Button(frame, text='Complete', command=lambda: _buttonCommand(fleetAll,numCompany,elapsedYear,root,v1))

        label1.grid(row=1, column=0)
        label2.grid(row=0, column=0)
        label3.grid(row=1, column=2)
        cb1.grid(row=1, column=1)
        button.grid(row=2, column=1)

        root.deiconify()
        root.mainloop()

        return fleetAll

    # calculate EEDI
    NumFleet = len(fleetAll[numCompany])
    for i in range(1,NumFleet):
        compFleet = fleetAll[numCompany][i]
        tOpTemp = compFleet['tOp']
        if compFleet['delivery'] <= currentYear and compFleet['tOp'] < tOpSch:
            rEEDIreqCurrent = rEEDIreqCurrentFunc(compFleet['wDWT'],rEEDIreq)
            compFleet['EEDIref'][tOpTemp], compFleet['EEDIreq'][tOpTemp] = EEDIreqFunc(valueDict['kEEDI1'],compFleet['wDWT'],valueDict['kEEDI2'],rEEDIreqCurrent)
            compFleet['MCRM'][tOpTemp], compFleet['PA'][tOpTemp], compFleet['EEDIatt'][tOpTemp], compFleet['vDsgnRed'][tOpTemp] = EEDIattFunc(compFleet['wDWT'],valueDict['wMCR'],valueDict['kMCR1'],valueDict['kMCR2'],valueDict['kMCR3'],valueDict['kPAE1'],valueDict['kPAE2'],valueDict['rCCS'],valueDict['vDsgn'],valueDict['rWPS'],compFleet['Cco2ship'],valueDict['SfcM'],valueDict['SfcA'],valueDict['rSPS'],compFleet['Cco2aux'],compFleet['EEDIreq'][tOpTemp],compFleet['WPS'],compFleet['SPS'],compFleet['CCS'])
            fleetAll[numCompany][i] = compFleet

    # show fleet list
    _fleetListGui(fleetAll,numCompany)
    
    # decide to scrap or refurbish currently alive fleet
    for i in range(1,NumFleet):
        compFleet = fleetAll[numCompany][i]
        tOpTemp = compFleet['tOp']
        if compFleet['delivery'] <= currentYear and compFleet['tOp'] < tOpSch:
            compFleet = _scrapOrRefurbishGui(compFleet,i,tOpSch,valueDict)
            cAdditionalEquipment = 1
            if compFleet['WPS']:
                cAdditionalEquipment += valueDict['dcostWPS']
            elif compFleet['SPS']:
                cAdditionalEquipment += valueDict['dcostSPS']
            elif compFleet['CCS']:
                cAdditionalEquipment += valueDict['dcostCCS']
            compFleet['costRfrb'][tOpTemp] = cAdditionalEquipment * compFleet['costShipBasicHFO']
            fleetAll[numCompany][i] = compFleet

    # decide additional shipping fee per container
    _dcostCntGui(fleetAll,numCompany,elapsedYear)

    #if decisionList[numCompany][currentYear]['Fee'] >= valueDict["dcostCntMin"] and decisionList[numCompany][currentYear]['Fee'] <= valueDict["dcostCntMax"]:
            #    dcostCntSum += decisionList[numCompany][currentYear]['Fee'] - valueDict["dcostCntMin"]
            #else:
            #    print('ERROR: dcostCnt should be more equal than {0} and less equal than {1}, but now {2}. '.format(valueDict["dcostCntMin"], valueDict["dcostCntMax"], decisionList[numCompany][currentYear]['Fee']))
            #    sys.exit()

    return fleetAll, fleetAll[numCompany]['total']['dcostCnt'][elapsedYear]

def orderShipFunc(fleetAll,numCompany,fuelName,WPS,SPS,CCS,CAPcnt,tOpSch,tbid,iniT,currentYear,elapsedYear,valueDict,NShipFleet,parameterFile2,parameterFile12,parameterFile3,parameterFile5):
    NumFleet = len(fleetAll[numCompany])
    fleetAll[numCompany].setdefault(NumFleet,{})
    compFleet = fleetAll[numCompany][NumFleet]
    compTotal = fleetAll[numCompany]['total']

                #if decisionList[numCompany][currentYear]['CAP'] >= valueDict["CAPcntMin"] and decisionList[numCompany][currentYear]['CAP'] <= valueDict["CAPcntMax"]:
                #    fleets = rs.orderShipFunc(fleets,numCompany,decisionList[numCompany][currentYear]['fuelType'],decisionList[numCompany][currentYear]['WPS'],decisionList[numCompany][currentYear]['SPS'],decisionList[numCompany][currentYear]['CCS'],decisionList[numCompany][currentYear]['CAP'],tOpSch,tbid,0,currentYear,parameterFile2,parameterFile12,parameterFile3,parameterFile5)
                #else:
                #    print('ERROR: CAPcnt should be more equal than {0} and less equal than {1}, but now {2}. '.format(valueDict["CAPcntMin"], valueDict["CAPcntMax"], decisionList[numCompany][currentYear]['CAP']))
                #    sys.exit()

    compFleet['fuelName'] = fuelName
    compFleet['WPS'] = WPS
    compFleet['SPS'] = SPS
    compFleet['CCS'] = CCS
    compFleet['CAPcnt'] = float(CAPcnt)
    compFleet['wDWT'] = wDWTFunc(valueDict["kDWT1"],compFleet['CAPcnt'],valueDict["kDWT2"])
    compFleet['wFLD'] = wFLDFunc(valueDict["kFLD1"],compFleet['wDWT'],valueDict["kFLD2"])
    compFleet['CeqLHVship'] = CeqLHVFunc(parameterFile2,compFleet['fuelName'])
    compFleet['CeqLHVaux'] = CeqLHVFunc(parameterFile12,compFleet['fuelName'])
    compFleet['Cco2ship'] = Cco2Func(parameterFile3,compFleet['fuelName'])
    if fuelName == 'HFO':
        compFleet['Cco2aux'] = Cco2Func(parameterFile3,'Diesel')
    else:
        compFleet['Cco2aux'] = Cco2Func(parameterFile3,compFleet['fuelName'])
    compFleet['rShipBasic'] = rShipBasicFunc(parameterFile5,compFleet['fuelName'],compFleet['CAPcnt'])
    compFleet['delivery'] = currentYear+tbid
    compFleet['tOp'] = iniT
    compFleet['costShipBasicHFO'], compFleet['costShipBasic'], compFleet['costShipAdd'], compFleet['costShip'] = costShipFunc(valueDict["kShipBasic1"], compFleet["CAPcnt"], valueDict["kShipBasic2"], compFleet['rShipBasic'], valueDict["dcostWPS"], valueDict["dcostSPS"], valueDict["dcostCCS"], compFleet['WPS'], compFleet['SPS'], compFleet['CCS'])
    if iniT == 0:
        compTotal['costShip'][elapsedYear] += NShipFleet * compFleet['costShip']
        compTotal['costShipBasicHFO'][elapsedYear] += NShipFleet * compFleet['costShipBasicHFO']
    compFleet['v'] = np.zeros(tOpSch)
    #compFleet['v'][:] = 1
    compFleet['d'] = np.zeros(tOpSch)
    compFleet['fShipORG'] = np.zeros(tOpSch)
    compFleet['fAuxORG'] = np.zeros(tOpSch)
    compFleet['gORG'] = np.zeros(tOpSch)
    compFleet['costFuelORG'] = np.zeros(tOpSch)
    compFleet['costFuel'] = np.zeros(tOpSch)
    compFleet['dcostFuel'] = np.zeros(tOpSch)
    compFleet['fShip'] = np.zeros(tOpSch)
    compFleet['fAux'] = np.zeros(tOpSch)
    compFleet['g'] = np.zeros(tOpSch)
    compFleet['cta'] = np.zeros(tOpSch)
    compFleet['dcostShipping'] = np.zeros(tOpSch)
    compFleet['gTilde'] = np.zeros(tOpSch)
    compFleet['costRfrb'] = np.zeros(tOpSch)
    compFleet['EEDIref'] = np.zeros(tOpSch)
    compFleet['EEDIreq'] = np.zeros(tOpSch)
    compFleet['EEDIatt'] = np.zeros(tOpSch)
    compFleet['vDsgnRed'] = np.zeros(tOpSch)
    compFleet['MCRM'] = np.zeros(tOpSch)
    compFleet['PA'] = np.zeros(tOpSch)
    fleetAll[numCompany][NumFleet] = compFleet
    fleetAll[numCompany]['total'] = compTotal
    return fleetAll

def orderPhaseFunc(fleetAll,numCompany,valueDict,elapsedYear,tOpSch,tbid,currentYear,rEEDIreq,NShipFleet,parameterFile2,parameterFile12,parameterFile3,parameterFile5):

    def _orderShipGui(fleetAll,numCompany,valueDict,elapsedYear,tOpSch,tbid,currentYear,rEEDIreq,NShipFleet,parameterFile2,parameterFile12,parameterFile3,parameterFile5):
        def _buttonCommandAnother(fleetAll,numCompany,tOpSch,tbid,currentYear,elapsedYear,NShipFleet,parameterFile2,parameterFile12,parameterFile3,parameterFile5):
            if v1.get() == 'HFO/Diesel':
                fuelName = 'HFO'
            else:
                fuelName = v1.get()
            fleetAll = orderShipFunc(fleetAll,numCompany,fuelName,int(v3.get()),int(v4.get()),int(v5.get()),float(v2.get()),tOpSch,tbid,0,currentYear,elapsedYear,valueDict,NShipFleet,parameterFile2,parameterFile12,parameterFile3,parameterFile5)
            cb1.delete(0,"end")
            cb1.insert(0, '8000')
            v3.set('0')
            v4.set('0')
            v5.set('0')
            cb2.var = v3
            cb3.var = v4
            cb4.var = v5
            label6['text'] = 'None'
            label7['text'] = 'None'
            label8['text'] = 'None'
            button1['state'] = 'disabled'
            button2['state'] = 'disabled'

        def _buttonCommandComplete(root,fleetAll,numCompany,tOpSch,tbid,currentYear,elapsedYear,NShipFleet,parameterFile2,parameterFile12,parameterFile3,parameterFile5):
            if v1.get() == 'HFO/Diesel':
                fuelName = 'HFO'
            else:
                fuelName = v1.get()
            fleetAll = orderShipFunc(fleetAll,numCompany,fuelName,int(v3.get()),int(v4.get()),int(v5.get()),float(v2.get()),tOpSch,tbid,0,currentYear,elapsedYear,valueDict,NShipFleet,parameterFile2,parameterFile12,parameterFile3,parameterFile5)
            root.quit()
            root.destroy()

        def _buttonCommandCheck(valueDict,parameterFile3,rEEDIreq):
            fuelType = v1.get()
            CAP = float(v2.get())
            WPS = int(v3.get())
            SPS = int(v4.get())
            CCS = int(v5.get())
            wDWT = wDWTFunc(valueDict['kDWT1'],CAP,valueDict['kDWT2'])
            rEEDIreqCurrent = rEEDIreqCurrentFunc(wDWT,rEEDIreq)
            if fuelType == 'HFO/Diesel':
                Cco2ship = Cco2Func(parameterFile3,'HFO')
                Cco2aux = Cco2Func(parameterFile3,'Diesel')
            else:
                Cco2ship = Cco2Func(parameterFile3,fuelType)
                Cco2aux = Cco2Func(parameterFile3,fuelType)
            _, EEDIreq = EEDIreqFunc(valueDict['kEEDI1'],wDWT,valueDict['kEEDI2'],rEEDIreqCurrent)
            _, _, EEDIatt, vDsgnRed = EEDIattFunc(wDWT,valueDict['wMCR'],valueDict['kMCR1'],valueDict['kMCR2'],valueDict['kMCR3'],valueDict['kPAE1'],valueDict['kPAE2'],valueDict['rCCS'],valueDict['vDsgn'],valueDict['rWPS'],Cco2ship,valueDict['SfcM'],valueDict['SfcA'],valueDict['rSPS'],Cco2aux,EEDIreq,WPS,SPS,CCS)
            label6['text'] = str(vDsgnRed)
            label7['text'] = str('{:.3g}'.format(EEDIreq))
            label8['text'] = str('{:.3g}'.format(EEDIatt))
            if valueDict['vMin'] < vDsgnRed:
                button1['state'] = 'normal'
                button2['state'] = 'normal'
        
        def _buttonCommandNoOrder(root):
            root.quit()
            root.destroy()

        root = Tk()
        root.title('Company '+str(numCompany)+' : Order Ship in '+str(currentYear))
        width = 1000
        height = 300
        placeX = root.winfo_screenwidth()/2 - width/2
        placeY = root.winfo_screenheight()/2 - height/2
        widgetSize = str(width)+'x'+str(height)+'+'+str(int(placeX))+'+'+str(int(placeY))
        root.geometry(widgetSize)

        # Frame
        frame = ttk.Frame(root, padding=20)
        frame.pack()

        # Label
        label1 = ttk.Label(frame, text='Fuel type', padding=(5, 2))
        label2 = ttk.Label(frame, text='CAP (8000<=) [TEU]', padding=(5, 2))
        label3 = ttk.Label(frame, text='vMax [kt]', padding=(5, 2))
        label4 = ttk.Label(frame, text='EEDIreq [g/(ton*NM)]', padding=(5, 2))
        label5 = ttk.Label(frame, text='EEDIatt [g/(ton*NM)]', padding=(5, 2))
        label6 = ttk.Label(frame, text='None', padding=(5, 2))
        label7 = ttk.Label(frame, text='None', padding=(5, 2))
        label8 = ttk.Label(frame, text='None', padding=(5, 2))
        label9 = ttk.Label(frame, text='WPS', padding=(5, 2))
        label10 = ttk.Label(frame, text='SPS', padding=(5, 2))
        label11 = ttk.Label(frame, text='CCS', padding=(5, 2))

        # List box
        fuelTypeList = ['HFO/Diesel','LNG','NH3','H2']
        v1 = StringVar()
        lb = ttk.Combobox(frame,textvariable=v1,values=fuelTypeList)
        lb.set(fuelTypeList[0])

        # Entry
        v2 = StringVar()
        v2.set('8000')
        cb1 = ttk.Entry(frame, textvariable=v2)

        # Checkbutton
        v3 = StringVar()
        v3.set('0') # 初期化
        cb2 = ttk.Checkbutton(frame, padding=(10), text='WPS', variable=v3)

        # Checkbutton
        v4 = StringVar()
        v4.set('0') # 初期化
        cb3 = ttk.Checkbutton(frame, padding=(10), text='SPS', variable=v4)

        # Checkbutton
        v5 = StringVar()
        v5.set('0') # 初期化
        cb4 = ttk.Checkbutton(frame, padding=(10), text='CCS', variable=v5)

        # Button
        button1 = ttk.Button(frame, text='Another fleet', state='disabled', command=lambda: _buttonCommandAnother(fleetAll,numCompany,tOpSch,tbid,currentYear,elapsedYear,NShipFleet,parameterFile2,parameterFile12,parameterFile3,parameterFile5))
        button2 = ttk.Button(frame, text='Complete', state='disabled', command=lambda: _buttonCommandComplete(root,fleetAll,numCompany,tOpSch,tbid,currentYear,elapsedYear,NShipFleet,parameterFile2,parameterFile12,parameterFile3,parameterFile5))
        button3 = ttk.Button(frame, text='EEDI check', command=lambda: _buttonCommandCheck(valueDict,parameterFile3,rEEDIreq))
        button4 = ttk.Button(frame, text='No order', command=lambda: _buttonCommandNoOrder(root))

        # Layout
        label1.grid(row=0, column=0)
        label2.grid(row=0, column=1)
        label3.grid(row=2, column=1)
        label4.grid(row=2, column=2)
        label5.grid(row=2, column=3)
        label6.grid(row=3, column=1)
        label7.grid(row=3, column=2)
        label8.grid(row=3, column=3)
        label9.grid(row=0, column=2)
        label10.grid(row=0, column=3)
        label11.grid(row=0, column=4)
        cb1.grid(row=1, column=1)
        cb2.grid(row=1, column=2)
        cb3.grid(row=1, column=3)
        cb4.grid(row=1, column=4)
        lb.grid(row=1, column=0)
        button1.grid(row=4, column=2)
        button2.grid(row=4, column=4)
        button3.grid(row=4, column=1)
        button4.grid(row=4, column=0)

        root.deiconify()
        root.mainloop()

        return fleetAll

    fleetAll = _orderShipGui(fleetAll,numCompany,valueDict,elapsedYear,tOpSch,tbid,currentYear,rEEDIreq,NShipFleet,parameterFile2,parameterFile12,parameterFile3,parameterFile5)

    return fleetAll

def yearlyOperationFunc(fleetAll,numCompany,pureDi,overDi,startYear,elapsedYear,NShipFleet,tOpSch,v,valueDict,parameterFile4,nextIf):
    NumFleet = len(fleetAll[numCompany])
    compTotal = fleetAll[numCompany]['total']

    #if decisionList[numCompany][currentYear]['Speed'] >= valueDict["vMin"]:
            #    fleets = rs.yearlyOperationFunc(fleets,numCompany,Di,startYear,elapsedYear,NShipFleet,Alpha,tOpSch,decisionList[numCompany][currentYear]['Speed'],valueDict,parameterFile4)
            #else:
            #    print('ERROR: CAPcnt should be more equal than {0} , but now {1}. '.format(valueDict["vMin"], decisionList[numCompany][currentYear]['Speed']))
            #    sys.exit()
    #print('ERROR: rocc should be 0.0 < rocc but now',Di/maxCta,'.')

    j = 0
    maxCta = 0
    currentYear = startYear+elapsedYear
    for i in range(1,NumFleet):
        compFleet = fleetAll[numCompany][i]
        if compFleet['delivery'] <= currentYear and compFleet['tOp'] < tOpSch:
            tOpTemp = compFleet['tOp']
            compFleet['v'][tOpTemp] = float(v[j].get()) # input for each fleet
            compFleet['d'][tOpTemp] = dFunc(valueDict["Dyear"],valueDict["Hday"],compFleet['v'][tOpTemp],valueDict["Rrun"])
            maxCta += NShipFleet * maxCtaFunc(compFleet['CAPcnt'],compFleet['d'][tOpTemp])
            fleetAll[numCompany][i] = compFleet
            j += 1
    
    compTotal['maxCta'][elapsedYear] = maxCta
    Di = overDi + pureDi

    if Di <= valueDict["rDMax"]*maxCta and Di / maxCta > 0.0:
        compTotal['rocc'][elapsedYear] = Di / maxCta
    elif Di > valueDict["rDMax"]*maxCta:
        compTotal['rocc'][elapsedYear] = valueDict["rDMax"]
        overDi = Di - valueDict["rDMax"]*maxCta
        compTotal['overDi'][elapsedYear] = overDi
        
    compTotal['costRfrb'][elapsedYear] = 0
    compTotal['g'][elapsedYear] = 0
    compTotal['cta'][elapsedYear] = 0
    compTotal['costFuel'][elapsedYear] = 0
    for i in range(1,NumFleet):
        compFleet = fleetAll[numCompany][i]
        if compFleet['delivery'] <= currentYear and compFleet['tOp'] < tOpSch:
            tOpTemp = compFleet['tOp']
            unitCostFuel, unitCostFuelHFO = unitCostFuelFunc(parameterFile4,compFleet['fuelName'],currentYear)
            compFleet['cta'][tOpTemp] = ctaFunc(compFleet['CAPcnt'],compTotal['rocc'][elapsedYear],compFleet['d'][tOpTemp])
            compFleet['fShipORG'][tOpTemp], compFleet['fShip'][tOpTemp] = fShipFunc(valueDict["kShip1"],valueDict["kShip2"],compFleet['wDWT'],compFleet['wFLD'],compTotal['rocc'][elapsedYear],valueDict["CNM2km"],compFleet['v'][tOpTemp],compFleet['d'][tOpTemp],valueDict["rWPS"],compFleet['WPS'],compFleet['CeqLHVship'])
            compFleet['fAuxORG'][tOpTemp], compFleet['fAux'][tOpTemp] = fAuxFunc(valueDict["Dyear"],valueDict["Hday"],valueDict["Rrun"],valueDict["kAux1"],valueDict["kAux2"],compFleet['wDWT'],valueDict["rSPS"],compFleet['SPS'],compFleet['CeqLHVaux'])
            compFleet['gORG'][tOpTemp], compFleet['g'][tOpTemp] = gFunc(compFleet['Cco2ship'],compFleet['fShip'][tOpTemp],compFleet['Cco2aux'],compFleet['fAux'][tOpTemp],valueDict["rCCS"],compFleet['CCS'])     
            compFleet['costFuelORG'][tOpTemp], compFleet['costFuel'][tOpTemp], compFleet['dcostFuel'][tOpTemp] = costFuelFunc(unitCostFuelHFO, unitCostFuel, compFleet['fShipORG'][tOpTemp], compFleet['fAuxORG'][tOpTemp], compFleet['fShip'][tOpTemp], compFleet['fAux'][tOpTemp])
            compFleet['dcostShipping'][tOpTemp] = additionalShippingFeeFunc(tOpTemp, tOpSch, compFleet['dcostFuel'][tOpTemp], compFleet['costShip'], compFleet['costShipBasicHFO'])
            compFleet['gTilde'][tOpTemp] = compFleet['g'][tOpTemp] / compFleet['cta'][tOpTemp]
            compTotal['costRfrb'][elapsedYear] += NShipFleet * compFleet['costRfrb'][tOpTemp]
            compTotal['g'][elapsedYear] += NShipFleet * compFleet['g'][tOpTemp]
            compTotal['cta'][elapsedYear] += NShipFleet * compFleet['cta'][tOpTemp]
            compTotal['costFuel'][elapsedYear] += NShipFleet * compFleet['costFuel'][tOpTemp]
            if nextIf:
                compFleet['tOp'] += 1
            fleetAll[numCompany][i] = compFleet

    compTotal['costAll'][elapsedYear] = compTotal['costFuel'][elapsedYear] + compTotal['costShip'][elapsedYear]/tOpSch + compTotal['costRfrb'][elapsedYear]
    compTotal['dcostEco'][elapsedYear] = compTotal['costFuel'][elapsedYear] + (compTotal['costShip'][elapsedYear]-compTotal['costShipBasicHFO'][elapsedYear])/tOpSch + compTotal['costRfrb'][elapsedYear]
    compTotal['nTransCnt'][elapsedYear] = compTotal['cta'][elapsedYear] / valueDict['dJPNA']
    compTotal['sale'][elapsedYear] = compTotal['nTransCnt'][elapsedYear] * (compTotal['dcostCnt'][elapsedYear] + valueDict['costCntNom'])

    compTotal['gTilde'][elapsedYear] = compTotal['g'][elapsedYear] / compTotal['cta'][elapsedYear]
    compTotal['costTilde'][elapsedYear] = compTotal['costAll'][elapsedYear] / compTotal['cta'][elapsedYear]
    compTotal['saleTilde'][elapsedYear] = compTotal['sale'][elapsedYear] / compTotal['cta'][elapsedYear]

    fleetAll[numCompany]['total'] = compTotal
    return fleetAll, overDi

def yearlyOperationPhaseFunc(fleetAll,numCompany,pureDi,overDi,startYear,elapsedYear,NShipFleet,tOpSch,valueDict,parameterFile4):
    def _surviceSpeedGui(fleetAll,numCompany,pureDi,overDi,startYear,elapsedYear,NShipFleet,tOpSch,valueDict,parameterFile4):
        
        def _buttonCommandNext(root,fleetAll,numCompany,pureDi,overDi,startYear,elapsedYear,NShipFleet,tOpSch,v13,valueDict,parameterFile4):
            fleetAll, overDi = yearlyOperationFunc(fleetAll,numCompany,pureDi,overDi,startYear,elapsedYear,NShipFleet,tOpSch,v13,valueDict,parameterFile4,True)
            root.quit()
            root.destroy()

        def _buttonCommandCalc(fleetAll,numCompany,pureDi,overDi,startYear,elapsedYear,NShipFleet,tOpSch,valueDict,parameterFile4):
            fleetAll, _ = yearlyOperationFunc(fleetAll,numCompany,pureDi,overDi,startYear,elapsedYear,NShipFleet,tOpSch,v13,valueDict,parameterFile4,False)
            compTotal = fleetAll[numCompany]['total']
            labelRes4['text'] = str('{:.3g}'.format(compTotal['cta'][elapsedYear]))
            labelRes6['text'] = str('{:.3g}'.format(compTotal['rocc'][elapsedYear]))
            labelRes8['text'] = str('{:.3g}'.format(compTotal['costFuel'][elapsedYear]))
            labelRes10['text'] = str('{:.3g}'.format(compTotal['g'][elapsedYear]))
            button2['state'] = 'normal'
            NumFleet = len(fleetAll[numCompany])
            j = 0
            for i in range(1,NumFleet):
                compFleet = fleetAll[numCompany][i]
                if compFleet['delivery'] <= currentYear and compFleet['tOp'] < tOpSch:
                    tOpTemp = compFleet['tOp']
                    if float(v13[j].get()) < 12 or float(v13[j].get()) > compFleet['vDsgnRed'][tOpTemp]:
                        button2['state'] = 'disabled'
                    j += 1

        root = Tk()
        root.title('Company '+str(numCompany)+' : Service Speed in '+str(startYear+elapsedYear))
        width = 800
        height = 500
        placeX = root.winfo_screenwidth()/2 - width/2
        placeY = root.winfo_screenheight()/2 - height/2
        widgetSize = str(width)+'x'+str(height)+'+'+str(int(placeX))+'+'+str(int(placeY))
        root.geometry(widgetSize)

        # Frame
        frame = ttk.Frame(root, padding=20)
        frame.pack()

        # Label
        labelRes1 = ttk.Label(frame, text='Assigned demand [TEU*NM]:', padding=(5, 2))
        labelRes2 = ttk.Label(frame, text=str('{:.3g}'.format(pureDi+overDi)), padding=(5, 2))
        labelRes3 = ttk.Label(frame, text='Cargo trasnsport amount [TEU*NM]:', padding=(5, 2))
        labelRes4 = ttk.Label(frame, text='None', padding=(5, 2))
        labelRes5 = ttk.Label(frame, text='Occupancy rate [%]:', padding=(5, 2))
        labelRes6 = ttk.Label(frame, text='None', padding=(5, 2))
        labelRes7 = ttk.Label(frame, text='Fuel cost [$]:', padding=(5, 2))
        labelRes8 = ttk.Label(frame, text='None', padding=(5, 2))
        labelRes9 = ttk.Label(frame, text='CO2 [ton]:', padding=(5, 2))
        labelRes10 = ttk.Label(frame, text='None', padding=(5, 2))
        label0 = ttk.Label(frame, text='No.', padding=(5, 2))
        label1 = ttk.Label(frame, text='Fuel type', padding=(5, 2))
        label2 = ttk.Label(frame, text='CAP [TEU]', padding=(5, 2))
        label3 = ttk.Label(frame, text='WPS', padding=(5, 2))
        label4 = ttk.Label(frame, text='SPS', padding=(5, 2))
        label5 = ttk.Label(frame, text='CCS', padding=(5, 2))
        label6 = ttk.Label(frame, text='vSer (12<=) [kt]', padding=(5, 2))
        label7 = ttk.Label(frame, text='vMax [kt]', padding=(5, 2))
        label00 = []
        label8 = []
        label9 = []
        label10 = []
        label11 = []
        label12 = []
        label13 = []
        label14 = []
        v13 = []
        currentYear = startYear+elapsedYear
        NumFleet = len(fleetAll[numCompany])
        for i in range(1,NumFleet):
            compFleet = fleetAll[numCompany][i]
            if compFleet['delivery'] <= currentYear and compFleet['tOp'] < tOpSch:
                label00.append(ttk.Label(frame, text=str(i), padding=(5, 2)))
                tOpTemp = compFleet['tOp']
                if compFleet['fuelName'] == 'HFO':
                    label8.append(ttk.Label(frame, text='HFO/Diesel', padding=(5, 2)))
                else:
                    label8.append(ttk.Label(frame, text=compFleet['fuelName'], padding=(5, 2)))
                label9.append(ttk.Label(frame, text=str(compFleet['CAPcnt']), padding=(5, 2)))
                if compFleet['WPS']:
                    label10.append(ttk.Label(frame, text='Yes', padding=(5, 2)))
                else:
                    label10.append(ttk.Label(frame, text='No', padding=(5, 2)))
                if compFleet['SPS']:
                    label11.append(ttk.Label(frame, text='Yes', padding=(5, 2)))
                else:
                    label11.append(ttk.Label(frame, text='No', padding=(5, 2)))
                if compFleet['CCS']:
                    label12.append(ttk.Label(frame, text='Yes', padding=(5, 2)))
                else:
                    label12.append(ttk.Label(frame, text='No', padding=(5, 2)))
                tOpTemp = compFleet['tOp']
                v13.append(StringVar())
                if compFleet['v'][tOpTemp-1] == 0:
                    v13[-1].set(str(compFleet['vDsgnRed'][tOpTemp]))
                else:
                    v13[-1].set(str(compFleet['v'][tOpTemp-1]))
                label13.append(ttk.Entry(frame, textvariable=v13[-1]))
                label14.append(ttk.Label(frame, text=str(compFleet['vDsgnRed'][tOpTemp]), padding=(5, 2)))

        # Button
        button1 = ttk.Button(frame, text='Calculate', command=lambda: _buttonCommandCalc(fleetAll,numCompany,pureDi,overDi,startYear,elapsedYear,NShipFleet,tOpSch,valueDict,parameterFile4))
        button2 = ttk.Button(frame, text='Next', state='disabled', command=lambda: _buttonCommandNext(root,fleetAll,numCompany,pureDi,overDi,startYear,elapsedYear,NShipFleet,tOpSch,v13,valueDict,parameterFile4))

        # Layout
        labelRes1.grid(row=0, column=1)
        labelRes2.grid(row=0, column=2)
        labelRes3.grid(row=0, column=4)
        labelRes4.grid(row=0, column=5)
        labelRes5.grid(row=1, column=1)
        labelRes6.grid(row=1, column=2)
        labelRes7.grid(row=1, column=4)
        labelRes8.grid(row=1, column=5)
        labelRes9.grid(row=2, column=1)
        labelRes10.grid(row=2, column=2)
        label0.grid(row=3, column=0)
        label1.grid(row=3, column=1)
        label2.grid(row=3, column=2)
        label3.grid(row=3, column=3)
        label4.grid(row=3, column=4)
        label5.grid(row=3, column=5)
        label6.grid(row=3, column=6)
        label7.grid(row=3, column=7)
        for i, j in enumerate(label8):
            label00[i].grid(row=i+4, column=0)
            label8[i].grid(row=i+4, column=1)
            label9[i].grid(row=i+4, column=2)
            label10[i].grid(row=i+4, column=3)
            label11[i].grid(row=i+4, column=4)
            label12[i].grid(row=i+4, column=5)
            label13[i].grid(row=i+4, column=6)
            label14[i].grid(row=i+4, column=7)
        button1.grid(row=i+5, column=6)
        button2.grid(row=i+5, column=7)

        root.deiconify()
        root.mainloop()

        return fleetAll

    fleetAll = _surviceSpeedGui(fleetAll,numCompany,pureDi,overDi,startYear,elapsedYear,NShipFleet,tOpSch,valueDict,parameterFile4)

    return fleetAll, overDi

def outputGuiFunc(fleetAll,startYear,elapsedYear,lastYear,tOpSch,unitDict):
    def _eachFrame(frame,fig,keyi,keyList,root):
        '''
        def _on_key_press(event):
            #print("you pressed {}".format(event.key))
            key_press_handler(event, canvas, toolbar)
        '''

        def _buttonCommandNext(root,fig):
            for keyi in keyList:
                fig[keyi].clf()
                plt.close(fig[keyi])
            root.quit()     # stops mainloop
            root.destroy()  # this is necessary on Windows to prevent
            
        def _buttonCommandShow(frameShow):
            frameShow.tkraise()

        frameEach = frame[keyi]
        frameEach.grid(row=0, column=0, sticky="nsew")

        # Canvas
        canvas = FigureCanvasTkAgg(fig[keyi], master=frameEach)
        canvas.draw()
        canvas.get_tk_widget().place(relx=0.03, rely=0.1)

        '''
        toolbar = NavigationToolbar2Tk(canvas, root)
        toolbar.update()
        canvas.get_tk_widget().grid(row=1, column=0)
        canvas.mpl_connect("key_press_event", _on_key_press)
        '''

        # Button
        button1 = Button(master=frameEach, text="Next Year", command=lambda: _buttonCommandNext(root,fig))
        button1.place(relx=0.22, rely=0.9)
        button2 = Button(master=frameEach, text="Show", command=lambda: _buttonCommandShow(frame[v.get()]))
        button2.place(relx=0.59, rely=0.9)

        # List box
        v = StringVar()
        lb = ttk.Combobox(frameEach,textvariable=v,values=keyList)
        lb.set(keyi)
        lb.place(relx=0.66, rely=0.9)

    # Tkinter Class
    root = Tk()
    root.title('Result in '+str(startYear+elapsedYear))
    root.geometry('800x600+300+200')
    width = 800
    height = 600
    placeX = root.winfo_screenwidth()/2 - width/2
    placeY = root.winfo_screenheight()/2 - height/2
    widgetSize = str(width)+'x'+str(height)+'+'+str(int(placeX))+'+'+str(int(placeY))
    root.geometry(widgetSize)

    fig = {}
    frame = {}
    keyList = list(fleetAll[1]['total'].keys())
    for keyi in keyList:
        fig[keyi] = outputAllCompany2Func(fleetAll,startYear,elapsedYear,keyi,unitDict)
        frame[keyi] = ttk.Frame(root, height=height, width=width)
    
    for keyi in keyList:
        _eachFrame(frame,fig,keyi,keyList,root)

    frame[keyList[0]].tkraise()

    # root
    mainloop()

def outputEachCompanyFunc(fleetAll,numCompany,startYear,elapsedYear,lastYear,tOpSch,decisionListName):
    fig, ax = plt.subplots(2, 2, figsize=(10.0, 10.0))
    plt.subplots_adjust(wspace=0.4, hspace=0.6)
    compTotal = fleetAll[numCompany]['total']

    SPlot = compTotal['S'][:elapsedYear+1]
    ax[0,0].plot(fleetAll['year'][:elapsedYear+1],compTotal['S'][:elapsedYear+1])
    ax[0,0].set_title(r"$ ( \Delta C_{shipping} - \alpha g) \ / \ cta$")
    ax[0,0].set_xlabel('Year')
    ax[0,0].yaxis.set_major_formatter(ScalarFormatter(useMathText=True))
    ax[0,0].ticklabel_format(style="sci",  axis="y",scilimits=(0,0))
    #ax[0].set_ylabel('Year')

    gTildePlot = compTotal['gTilde'][:elapsedYear+1]*1000000
    ax[1,0].plot(fleetAll['year'][:elapsedYear+1],compTotal['gTilde'][:elapsedYear+1]*1000000)
    ax[1,0].set_title("g / cta")
    ax[1,0].set_xlabel('Year')
    ax[1,0].set_ylabel('g / (TEU $\cdot$ NM)')
    #ax[1,0].yaxis.set_major_formatter(ScalarFormatter(useMathText=True))
    ax[1,0].ticklabel_format(style="sci",  axis="y",scilimits=(0,0))

    gPlot = compTotal['g'][:elapsedYear+1]/1000000
    ax[0,1].plot(fleetAll['year'][:elapsedYear+1],compTotal['g'][:elapsedYear+1]/1000000)
    ax[0,1].set_title("g")
    ax[0,1].set_xlabel('Year')
    ax[0,1].set_ylabel('Millions ton')
    ax[0,1].yaxis.set_major_formatter(ScalarFormatter(useMathText=True))
    ax[0,1].ticklabel_format(style="sci",  axis="y",scilimits=(0,0))

    dcostShippingTildePlot = compTotal['dcostShippingTilde'][:elapsedYear+1]
    ax[1,1].plot(fleetAll['year'][:elapsedYear+1],compTotal['dcostShippingTilde'][:elapsedYear+1])
    ax[1,1].set_title("$\Delta C_{shipping} \ / \ cta$")
    ax[1,1].set_xlabel('Year')
    ax[1,1].set_ylabel('\$ / (TEU $\cdot$ NM)')
    ax[1,1].yaxis.set_major_formatter(ScalarFormatter(useMathText=True))
    ax[1,1].ticklabel_format(style="sci",  axis="y",scilimits=(0,0))
                #if i == 1:
                #    ax2.bar(fleetAll['year'][:elapsedYear+1], simu)
                #else:
                #    ax2.bar(fleetAll['year'][:elapsedYear+1], simu, bottom=simuSum)
    
    #fig.tight_layout()
    
    if os.name == 'nt':
        plt.show()
    elif os.name == 'posix':
        plt.savefig("Company"+str(numCompany)+decisionListName+".jpg")
        np.savetxt("Company"+str(numCompany)+decisionListName+'_S.csv',SPlot)
        np.savetxt("Company"+str(numCompany)+decisionListName+'_gTilde.csv',gTildePlot)
        np.savetxt("Company"+str(numCompany)+decisionListName+'_g.csv',gPlot)
        np.savetxt("Company"+str(numCompany)+decisionListName+'_dcostShippingTilde.csv',dcostShippingTildePlot)

def outputAllCompanyFunc(fleetAll,startYear,elapsedYear,lastYear,tOpSch,unitDict):
        
    currentYear = startYear+elapsedYear
    if elapsedYear > 0:
        year = fleetAll['year'][:elapsedYear+1]
        
        fig, axes = plt.subplots(3, 6, figsize=(16.0, 9.0))
        plt.subplots_adjust(wspace=0.4, hspace=0.6)

        for numCompany in range(1,4):
            for ax, keyi in zip(fig.axes, fleetAll[numCompany]['total'].keys()):
                ax.plot(year,fleetAll[numCompany]['total'][keyi][:elapsedYear+1],label="Company"+str(numCompany))
                ax.set_title(keyi)
                ax.set_xlabel('Year')
                ax.legend()
                #ax.ticklabel_format(style="sci",  axis="y",scilimits=(0,0))
                ax.set_ylabel(unitDict[keyi])
                ax.title.set_size(10)
                ax.xaxis.label.set_size(10)
                #ax.get_xaxis().get_major_formatter().set_useOffset(False)
                #ax.get_xaxis().set_major_locator(MaxNLocator(integer=True))
                ax.set_xticks(year)
                ax.yaxis.label.set_size(10)
    else:
        fig, axes = plt.subplots(3, 6, figsize=(16.0, 9.0))
        plt.subplots_adjust(wspace=0.4, hspace=0.6)

        for numCompany in range(1,4):
            for ax, keyi in zip(fig.axes, fleetAll[numCompany]['total'].keys()):
                ax.scatter(startYear,fleetAll[numCompany]['total'][keyi][0],label="Company"+str(numCompany))
                ax.set_title(keyi)
                ax.set_xlabel('Year')
                ax.legend()
                #ax.ticklabel_format(style="sci",  axis="y",scilimits=(0,0))
                ax.set_ylabel(unitDict[keyi])
                ax.title.set_size(10)
                ax.xaxis.label.set_size(10)
                #ax.set_xticks(np.array([startYear-1,startYear,startYear+1]))
                ax.set_xticks(np.array([startYear]))
                ax.yaxis.label.set_size(10)

    
    '''
    if os.name == 'nt':
        plt.show()
    elif os.name == 'posix':
        plt.savefig("TotalValues.jpg")
        for j, listName in enumerate(decisionListNameList,1):
            valueName = []
            outputList = []
            for i, keyi in enumerate(fleetAll[j]['total'].keys(),1):
                valueName.append(keyi)
                outputList.append(fleetAll[j]['total'][keyi][:elapsedYear+1])
                    
            outputData = np.stack(outputList,1)
            outputDf = pd.DataFrame(data=outputData, index=year, columns=valueName, dtype='float')
            outputDf.to_csv("Company"+str(j)+'_'+listName+'.csv')
    '''

    '''
    figDict = {}
    for j, listName in enumerate(decisionListNameList,1):
        for keyFleet in fleetAll[j].keys():
            valueName = []
            outputList = []
            if type(keyFleet) is int:
                for keyValue in fleetAll[j][keyFleet].keys():
                    if type(fleetAll[j][keyFleet][keyValue]) is np.ndarray:
                        valueName.append(keyValue)
                        #if keyFleet == 1 and j == 1:
                        #    fig, ax = plt.subplots(1, 1, figsize=(12.0, 8.0))
                        #    figDict.setdefault(keyValue,ax)

                        plotArr = np.zeros(lastYear-startYear+1)
                        if fleetAll[j][keyFleet]['delivery'] >= startYear:
                            plotArr[fleetAll[j][keyFleet]['delivery']-startYear:fleetAll[j][keyFleet]['delivery']-startYear+fleetAll[j][keyFleet]['tOp']] = fleetAll[j][keyFleet][keyValue][:fleetAll[j][keyFleet]['tOp']]
                        else:
                            plotArr[:tOpSch-startYear+fleetAll[j][keyFleet]['delivery']] = fleetAll[j][keyFleet][keyValue][startYear-fleetAll[j][keyFleet]['delivery']:fleetAll[j][keyFleet]['tOp']]
                        
                        outputList.append(plotArr)

                        #figDict[keyValue].plot(year,plotArr,label="Fleet"+str(keyFleet))
                        #figDict[keyValue].set_title(keyValue)
                        #figDict[keyValue].set_xlabel('Year')
                        #figDict[keyValue].legend()
                        #figDict[keyValue].ticklabel_format(style="sci",  axis="y",scilimits=(0,0))
                        #figDict[keyValue].set_ylabel(unitDict[keyValue])

                        #if j == len(decisionListNameList) and keyFleet == len(list(fleetAll[j].keys()))-1 and os.name == 'nt':
                        #    plt.show()
                        #elif j == len(decisionListNameList) and keyFleet == len(list(fleetAll[j].keys()))-1 and os.name == 'posix':
                        #    plt.savefig(str(keyValue)+".jpg")

                if os.name == 'posix':
                    outputData = np.stack(outputList,1)
                    outputDf = pd.DataFrame(data=outputData, index=year, columns=valueName, dtype='float')
                    outputDf.to_csv("Company"+str(j)+'_'+listName+'_'+'Fleet'+str(keyFleet)+'.csv')
    '''

    return fig

def outputAllCompany2Func(fleetAll,startYear,elapsedYear,keyi,unitDict):
        
    currentYear = startYear+elapsedYear
    fig, ax = plt.subplots(1, 1, figsize=(7.5, 4.5))
    #plt.subplots_adjust(wspace=0.4, hspace=0.6)
    if elapsedYear > 0:
        year = fleetAll['year'][:elapsedYear+1]
        for numCompany in range(1,4):
            ax.plot(year,fleetAll[numCompany]['total'][keyi][:elapsedYear+1],label="Company"+str(numCompany))
            ax.set_title(keyi)
            ax.set_xlabel('Year')
            ax.legend()
            ax.ticklabel_format(style="sci",  axis="y",scilimits=(0,0))
            ax.set_ylabel(unitDict[keyi])
            #ax.title.set_size(10)
            #ax.xaxis.label.set_size(10)
            #ax.get_xaxis().get_major_formatter().set_useOffset(False)
            #ax.get_xaxis().set_major_locator(MaxNLocator(integer=True))
            ax.set_xticks(np.array([2020,2025,2030,2035,2040,2045,2050]))
            #ax.yaxis.label.set_size(10)
    else:
        for numCompany in range(1,4):
            ax.scatter(startYear,fleetAll[numCompany]['total'][keyi][0],label="Company"+str(numCompany))
            ax.set_title(keyi)
            ax.set_xlabel('Year')
            ax.legend()
            ax.ticklabel_format(style="sci",  axis="y",scilimits=(0,0))
            ax.set_ylabel(unitDict[keyi])
            #ax.title.set_size(10)
            #ax.xaxis.label.set_size(10)
            #ax.set_xticks(np.array([startYear-1,startYear,startYear+1]))
            ax.set_xticks(np.array([startYear]))
            #ax.yaxis.label.set_size(10)
    return fig

def outputCsvFunc(fleetAll,startYear,elapsedYear,lastYear,tOpSch):
    resPath = Path(__file__).parent
    resPath /= '../results'
    shutil.rmtree(resPath)
    os.mkdir(resPath)
    year = fleetAll['year'][:elapsedYear+1]
    tOps = np.arange(tOpSch)
    for numCompany in range(1,4):
        valueName = []
        outputList = []
        for keyi in fleetAll[numCompany]['total'].keys():
            valueName.append(keyi)
            outputList.append(fleetAll[numCompany]['total'][keyi][:elapsedYear+1])
                    
        outputData1 = np.stack(outputList,1)
        outputDf1 = pd.DataFrame(data=outputData1, index=year, columns=valueName, dtype='float')
        outputDf1.to_csv(str(resPath)+"\Company"+str(numCompany)+'.csv')

        for keyFleet in fleetAll[numCompany].keys():
            valueName = []
            outputList = []
            if type(keyFleet) is int:
                compFleet = fleetAll[numCompany][keyFleet]
                for keyValue in compFleet.keys():
                    if type(compFleet[keyValue]) is np.ndarray:
                        valueName.append(keyValue)
                        '''
                        plotArr = np.zeros(lastYear-startYear+1)
                        if compFleet['delivery'] >= startYear:
                            plotArr[compFleet['delivery']-startYear:compFleet['delivery']-startYear+compFleet['tOp']] = compFleet[keyValue][:compFleet['tOp']]
                        else:
                            plotArr[:tOpSch-startYear+compFleet['delivery']] = compFleet[keyValue][(startYear-compFleet['delivery']):compFleet['tOp']]
                        '''
                        outputList.append(compFleet[keyValue])
                
                outputData2 = np.stack(outputList,1)
                outputDf2 = pd.DataFrame(data=outputData2, index=tOps, columns=valueName, dtype='float')
                outputDf2.to_csv(str(resPath)+"\Company"+str(numCompany)+'_'+'Fleet'+str(keyFleet)+'.csv')

