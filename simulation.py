import random as rd
import math
from arrival import createJob
from process import createProcessTime
import copy
import concurrent.futures as cf
from itertools import repeat, chain 

def simProcess(seeds,arrivalRates,processRates,tmax, arrivalType,processType,initQueue = 0):

    KPIall = []
    numberOfScenarios = len(seeds)

    #Simulaton

    for scenario in range(numberOfScenarios):
        #set Seed for scenario
        rd.seed(seeds[scenario])
        #Simulation Log
        systemLog = []
        #Scenario Output
        KPIs = dict()
        KPIs["LQ"] = [0 for i in range(tmax)]
        KPIs["Seed"] = seeds[scenario]

        tnow = 0
        arrivals = [0 for i in range(initQueue)] + createJob(type = arrivalType, arrivalRate = arrivalRates, arrivalSchedule = arrivalRates, tnow = tnow,tmax = tmax)

        for index, interArrivalTime in enumerate(arrivals):
            
            if index == 0:
                arrivalTime = interArrivalTime
                tnow = arrivalTime
                processStart = interArrivalTime
                processEnd = processStart + createProcessTime(processType, tnow, processRate = processRates, processSchedule = processRates)
                systemLog.append ( [arrivalTime,processStart,processEnd] )
            else:
                arrivalTime = interArrivalTime
                tnow = arrivalTime
                processStart = max(arrivalTime,systemLog[index-1][2])
                processEnd = processStart + createProcessTime(processType, processStart, processRate = processRates, processSchedule = processRates)
                systemLog.append( [arrivalTime,processStart,processEnd])
        
            enqueuePeriod = math.ceil(arrivalTime)
            dequeuePeriod = math.ceil(processEnd) 
            
            for currentPeriod in range(enqueuePeriod , dequeuePeriod + 1):
                if currentPeriod > tmax:
                    break
                elif enqueuePeriod == dequeuePeriod == currentPeriod:
                    KPIs["LQ"][currentPeriod - 1] += (processEnd - arrivalTime)
                    
                elif enqueuePeriod < currentPeriod and dequeuePeriod == currentPeriod:
                    KPIs["LQ"][currentPeriod - 1] += (processEnd - (currentPeriod - 1))
                    
                elif enqueuePeriod == currentPeriod and dequeuePeriod > currentPeriod:
                    KPIs["LQ"][currentPeriod - 1] += (currentPeriod - arrivalTime)
                    
                else:
                    KPIs["LQ"][currentPeriod - 1] += 1
        LS_tmax = len([i for i in systemLog if i[0]<tmax and i[2]>tmax])  
        KPIs["LS_tmax"] = LS_tmax
        KPIall.append(copy.deepcopy(KPIs))

    return KPIall,None



def sim(numberOfScenarios,arrivalRates,processRates,tmax,arrivalType,processType,initQueue = 0,workers = 6,jobs = 30):
    rd.seed (42)
    #chunksize = numberOfScenarios // 20
    chunksize = [numberOfScenarios//jobs for i in range(jobs)]
    chunksize[-1] += numberOfScenarios-sum(chunksize)
    workers = 6
    #2. Parallelization
    with cf.ProcessPoolExecutor(max_workers=workers) as executor:
        # 2.1. Discretise workload and submit to worker pool
        seeds = [[rd.randint(1000000,10000000) for i in range(chunk)] for chunk in chunksize]
        futures = executor.map(simProcess, seeds, repeat(arrivalRates), repeat(processRates),repeat(tmax),repeat(arrivalType),repeat(processType),repeat(initQueue))

    KPIall = list(futures)
    temp = [i[0] for i in KPIall]
    KPIall = []
    for i in temp:

        KPIall += i
    averageLQ = [0 for i in range(tmax)]
    for i in range(numberOfScenarios):
        for j in range(tmax):
            averageLQ[j] += KPIall[i]["LQ"][j]
    averageLQ = [x / numberOfScenarios for x in averageLQ]
    LS_tmax = sum([i["LS_tmax"] for i in KPIall])/numberOfScenarios
    return KPIall,averageLQ,LS_tmax