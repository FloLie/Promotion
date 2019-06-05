import random as rd
import math
from simulation import sim
import matplotlib.pyplot as plt
import datetime
from time import time
from utility import RMSE,MAPE,get_optimal_process_rate,create_output,output_to_excel,get_total_cost,save_output_graph,get_expected_queue
import pandas as pd
import pickle
import itertools as it
import copy
import json

def SIPP(numberOfScenarios,arrivalRates,h,s,tmax,availableProcessRates,initQueue,arrivalRatesMicro=None):
    if isinstance(arrivalRatesMicro,type(None)):
        arrivalRatesMicro=arrivalRates
    results = []
    bestResult = {"TotalCost":math.inf,"Output":None}  

    SIPP = [[period[0],max(min(availableProcessRates),min(get_optimal_process_rate(period[1],h,s),max(availableProcessRates)))]for period in arrivalRates]
    SIPPround = [[period[0],int(round(period[1],0))]for period in SIPP]
    SIPPceil = [[period[0],int(math.ceil(period[1]))]for period in SIPP]
    SIPPfloor = [[period[0],int(math.floor(period[1]))]for period in SIPP]   
    allProcessRates = [SIPPround,SIPPceil,SIPPfloor]
    for processRates in allProcessRates:
        KPI, LQ,LS_tmax =  sim(numberOfScenarios,arrivalRatesMicro,processRates,tmax,"Time Dependent","Time Dependent",initQueue = initQueue,jobs=30)

        totalCost = get_total_cost(LQ,h,s,processRates,tmax,LS_tmax)
        #print(totalCost)
        output = create_output(numberOfScenarios,arrivalRatesMicro,processRates,tmax,h,s,LQ,LS_tmax)
        results.append(copy.deepcopy(output))
        if totalCost < bestResult["TotalCost"]:
            bestResult["TotalCost"] = output["totalCost"]
            bestResult["Output"] = copy.deepcopy(output)        
    return results,bestResult

#Algorithm Start
def simple_hill_climbing(numberOfScenarios,arrivalRates,h,s,tmax,availableProcessRates,initQueue,arrivalRatesMicro=None):
    if isinstance(arrivalRatesMicro,type(None)):
        arrivalRatesMicro=arrivalRates
    results = []
    resultDevelopment = []
    bestResult = {"TotalCost":math.inf,"Output":None}  
    maxProcessRate = availableProcessRates[-1]
    minProcessRate = availableProcessRates[0]
    
    abortCriterion = len(arrivalRates)
    abortCounter = 0 
    macroPeriod = 0
    
    tested = []

    SIPPresults,SIPPbest = SIPP(numberOfScenarios,arrivalRates,h,s,tmax,availableProcessRates,initQueue,arrivalRatesMicro)
    counter = 3
    tested.extend([i["processRates"] for i in SIPPresults])


    bestResult["TotalCost"] = SIPPbest["TotalCost"]
    bestResult["Output"] = copy.deepcopy(SIPPbest["Output"])
    processRates = SIPPbest["Output"]["processRates"]

    while abortCounter < abortCriterion:
        improvementInPeriod = False
        testHigher = True
        while testHigher == True and processRates[macroPeriod][1] < maxProcessRate:
            testProcessRates = copy.deepcopy(processRates)
            testProcessRates[macroPeriod][1] = availableProcessRates[availableProcessRates.index(testProcessRates[macroPeriod][1])+1]

            if testProcessRates not in tested:
                counter += 1
            
                KPI, LQ,LS_tmax =  sim(numberOfScenarios,arrivalRatesMicro,testProcessRates,tmax,"Time Dependent","Time Dependent",initQueue = initQueue,jobs=30)
                
                totalCost = get_total_cost(LQ,h,s,testProcessRates,tmax,LS_tmax)
                output = create_output(numberOfScenarios,arrivalRatesMicro,testProcessRates,tmax,h,s,LQ,LS_tmax)
                results.append(copy.deepcopy(output))
                tested.append(copy.deepcopy(testProcessRates))
                
            
                if totalCost < bestResult["TotalCost"]:
                    improvementInPeriod = True
                    processRates = copy.deepcopy(testProcessRates)
                    abortCounter = 0
                    bestResult["TotalCost"] = output["totalCost"]
                    bestResult["Output"] = copy.deepcopy(output)
                    bestResult["KPI"] = copy.deepcopy(KPI)
                    resultDevelopment.append((counter,totalCost))
                else:
                    testHigher = False
            else:
                    testHigher = False  

        if improvementInPeriod == False:
            testLower = True
            while testLower == True and processRates[macroPeriod][1] > minProcessRate:
                testProcessRates = copy.deepcopy(processRates)
                testProcessRates[macroPeriod][1] = availableProcessRates[availableProcessRates.index(testProcessRates[macroPeriod][1])-1]
                
                if testProcessRates not in tested:
                    counter +=1
                    KPI, LQ,LS_tmax =  sim(numberOfScenarios,arrivalRatesMicro,testProcessRates,tmax,"Time Dependent","Time Dependent",initQueue = initQueue,jobs=30)
                    totalCost = get_total_cost(LQ,h,s,testProcessRates,tmax,LS_tmax)
                    output = create_output(numberOfScenarios,arrivalRatesMicro,testProcessRates,tmax,h,s,LQ,LS_tmax)
                    results.append(copy.deepcopy(output))
                    tested.append(copy.deepcopy(testProcessRates))

                    if totalCost < bestResult["TotalCost"]:
                        improvementInPeriod = True
                        processRates = copy.deepcopy(testProcessRates)
                        abortCounter = 0
                        bestResult["TotalCost"] = totalCost
                        bestResult["Output"] = copy.deepcopy(output)
                        bestResult["KPI"] = copy.deepcopy(KPI)
                        resultDevelopment.append((counter,totalCost))
                    else:
                        testLower = False 
                else:
                    testLower = False
        if improvementInPeriod == False:
            abortCounter += 1
        macroPeriod = (macroPeriod+1)%len(arrivalRates)
    bestResult["counter"] = counter
    print("Total Cost: "+str(bestResult["TotalCost"]) + " after "+str(counter) +" evaluations")
    return results,bestResult,resultDevelopment


def independent_opt(numberOfScenarios,arrivalRates,h,s,tmax,availableProcessRates,initQueue,macroLength,arrivalRatesMicro=None):
    if isinstance(arrivalRatesMicro,type(None)):
        arrivalRatesMicro=arrivalRates
    results = []
    bestResult = {"TotalCost":math.inf,"Output":None}  

    maxProcessRate = availableProcessRates[-1]
    minProcessRate = availableProcessRates[0]
    
    macroPeriod = 1
    totalPeriods = len(arrivalRates)
    SIPPresults,SIPPbest = SIPP(numberOfScenarios,arrivalRates,h,s,tmax,availableProcessRates,initQueue,arrivalRatesMicro)

    completeArrivalRates = copy.deepcopy(arrivalRatesMicro)
    completeProcessRates = copy.deepcopy(SIPPbest["Output"]["processRates"])
    counter = 3
    processRates = completeProcessRates[:1]
    while macroPeriod < totalPeriods:
        processRates.append(completeProcessRates[macroPeriod])
        tmax = (macroPeriod+1)*macroLength
        KPI, LQ,LS_tmax =  sim(numberOfScenarios,arrivalRatesMicro,processRates,tmax,"Time Dependent","Time Dependent",initQueue = initQueue,jobs=30)
        totalCost = get_total_cost(LQ,h,s,processRates,tmax,LS_tmax)
        output = create_output(numberOfScenarios,arrivalRatesMicro,processRates,tmax,h,s,LQ,LS_tmax)
        bestResult["TotalCost"] = output["totalCost"]
        bestResult["Output"] = copy.deepcopy(output)

        improvementInPeriod = False
        testHigher = True
        while testHigher == True and processRates[macroPeriod][1] < maxProcessRate:

            testProcessRates = copy.deepcopy(processRates)
            testProcessRates[macroPeriod][1] = availableProcessRates[availableProcessRates.index(testProcessRates[macroPeriod][1])+1]
            counter += 1

            KPI, LQ,LS_tmax =  sim(numberOfScenarios,arrivalRatesMicro,testProcessRates,tmax,"Time Dependent","Time Dependent",initQueue = initQueue,jobs=30)
            totalCost = get_total_cost(LQ,h,s,testProcessRates,tmax,LS_tmax)

            output = create_output(numberOfScenarios,arrivalRatesMicro,testProcessRates,tmax,h,s,LQ,LS_tmax)
            results.append(copy.deepcopy(output))

            if totalCost < bestResult["TotalCost"]:
                improvementInPeriod = True
                processRates = copy.deepcopy(testProcessRates)
                bestResult["TotalCost"] = output["totalCost"]
                bestResult["Output"] = copy.deepcopy(output)
            else:
                testHigher = False

        if improvementInPeriod == False:
            testLower = True
            while testLower == True and processRates[macroPeriod][1] > minProcessRate:

                testProcessRates = copy.deepcopy(processRates)
                testProcessRates[macroPeriod][1] = availableProcessRates[availableProcessRates.index(testProcessRates[macroPeriod][1])-1]
                counter +=1

                KPI, LQ,LS_tmax =  sim(numberOfScenarios,arrivalRatesMicro,testProcessRates,tmax,"Time Dependent","Time Dependent",initQueue = initQueue,jobs=30)
                totalCost = get_total_cost(LQ,h,s,testProcessRates,tmax,LS_tmax)
                output = create_output(numberOfScenarios,arrivalRatesMicro,testProcessRates,tmax,h,s,LQ,LS_tmax)
                results.append(copy.deepcopy(output))

                if totalCost < bestResult["TotalCost"]:
                    improvementInPeriod = True
                    processRates = copy.deepcopy(testProcessRates)
                    bestResult["TotalCost"] = totalCost
                    bestResult["Output"] = copy.deepcopy(output)
                else:
                    testLower = False 
        macroPeriod = macroPeriod+1
    bestResult["counter"] = counter
    print("Total Cost: "+str(bestResult["TotalCost"]) + " after "+str(counter) +" evaluations")
    return results,bestResult


def steepest_ascent_hill_climbing(numberOfScenarios,arrivalRates,h,s,tmax,availableProcessRates,initQueue,macroLength,arrivalRatesMicro=None):
    if isinstance(arrivalRatesMicro,type(None)):
        arrivalRatesMicro=arrivalRates
    tested = []
    results = []
    resultDevelopment = []
    bestResult = {"TotalCost":math.inf,"Output":None}  
    #Counter 
    iterationCounter = 0
    evaluationCounter = 3

    maxProcessRate = availableProcessRates[-1]
    minProcessRate = availableProcessRates[0]
    totalPeriods = len(arrivalRates)

    SIPPresults,SIPPbest = SIPP(numberOfScenarios,arrivalRates,h,s,tmax,availableProcessRates,initQueue,arrivalRatesMicro)
    
    bestResult["TotalCost"] = SIPPbest["TotalCost"]
    bestResult["Output"] = copy.deepcopy(SIPPbest)
    processRates = copy.deepcopy(SIPPbest["Output"]["processRates"])

    improvement = True
    resetMacroPeriods = False
    
    macroPeriods = [i for i in range(0,totalPeriods)]
    nextMacroPeriods = []
    
    while improvement:  
        improvementInIteration = False
        iterationResults = []
        for macroPeriod in macroPeriods:
            improvementInPeriod = False
            if processRates[macroPeriod][1] < maxProcessRate:

                testProcessRates = copy.deepcopy(processRates)
                testProcessRates[macroPeriod][1] = availableProcessRates[availableProcessRates.index(testProcessRates[macroPeriod][1])+1]

                if testProcessRates not in tested:
                    KPI, LQ, LS_tmax =  sim(numberOfScenarios,arrivalRatesMicro,testProcessRates,tmax,"Time Dependent","Time Dependent",initQueue = initQueue,jobs=30)
                    totalCost = get_total_cost(LQ,h,s,testProcessRates,tmax,LS_tmax)
                    output = create_output(numberOfScenarios,arrivalRatesMicro,testProcessRates,tmax,h,s,LQ,LS_tmax)

                    iterationResults.append(copy.deepcopy(output))
                    tested.append(copy.deepcopy(testProcessRates))

                    if totalCost < bestResult["TotalCost"]:
                        improvementInPeriod = True
                        iterationResults[-1]["macroPeriod"] = macroPeriod
                        nextMacroPeriods.append(macroPeriod)
                        resetMacroPeriods = False

                    evaluationCounter += 1

            if processRates[macroPeriod][1] > minProcessRate and not improvementInPeriod:

                testProcessRates = copy.deepcopy(processRates)
                testProcessRates[macroPeriod][1] = availableProcessRates[availableProcessRates.index(testProcessRates[macroPeriod][1])-1]

                if testProcessRates not in tested:
                    KPI, LQ,LS_tmax =  sim(numberOfScenarios,arrivalRatesMicro,testProcessRates,tmax,"Time Dependent","Time Dependent",initQueue = initQueue,jobs=30)
                    totalCost = get_total_cost(LQ,h,s,testProcessRates,tmax,LS_tmax)    
                    output = create_output(numberOfScenarios,arrivalRatesMicro,testProcessRates,tmax,h,s,LQ,LS_tmax)

                    iterationResults.append(copy.deepcopy(output))
                    tested.append(copy.deepcopy(testProcessRates))

                    if totalCost < bestResult["TotalCost"]:
                        improvementInPeriod = True
                        iterationResults[-1]["macroPeriod"] = macroPeriod
                        nextMacroPeriods.append(macroPeriod)
                        resetMacroPeriods = False

                    evaluationCounter += 1
            if improvementInPeriod:
                improvementInIteration = True

        bestInIteration = (None,math.inf)  

        if improvementInIteration: 
            for result in iterationResults:
                if result["totalCost"]<bestResult["TotalCost"]:
                    period = result["macroPeriod"]
                    processRates[period][1] = result["processRates"][period][1]
                    improvement = True
                    if result["totalCost"]<bestInIteration[1]:
                        bestInIteration = (result,result["totalCost"])

            if bestInIteration[0]["processRates"] != processRates:
                KPI, LQ,LS_tmax =  sim(numberOfScenarios,arrivalRatesMicro,processRates,tmax,"Time Dependent","Time Dependent",initQueue = initQueue,jobs=30)
                totalCost = get_total_cost(LQ,h,s,processRates,tmax,LS_tmax)    
                output = create_output(numberOfScenarios,arrivalRatesMicro,processRates,tmax,h,s,LQ,LS_tmax)
                evaluationCounter += 1
                tested.append(copy.deepcopy(processRates))

                if totalCost < bestInIteration[1]:
                    bestResult["TotalCost"] = totalCost
                    bestResult["Output"] = copy.deepcopy(output)
            else:
                processRates = bestInIteration[0]["processRates"]
                bestResult["TotalCost"] = bestInIteration[1]
                bestResult["Output"] =bestInIteration[0]


        if not improvementInIteration  and not resetMacroPeriods:
            resetMacroPeriods = True
            nextMacroPeriods = [i for i in range(0,totalPeriods)]

        if resetMacroPeriods and len(nextMacroPeriods) == 0:
            improvement = False

        
        macroPeriods = copy.deepcopy(nextMacroPeriods)
        nextMacroPeriods = []

        iterationCounter += 1
        results.extend(iterationResults)
        resultDevelopment.append((evaluationCounter,bestResult["TotalCost"]))
    print("Total Cost: "+str(bestResult["TotalCost"]) + " after "+str(evaluationCounter) +" evaluations")
    bestResult["counter"] = evaluationCounter
    return results,bestResult,resultDevelopment