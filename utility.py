import numpy as np
from sklearn.metrics import mean_squared_error
from math import sqrt,inf
from scipy.optimize import fsolve
import pandas as pd
import datetime
import matplotlib.pyplot as plt
import copy
import numpy as np


def MAPE(y_true, y_pred): 
    y_true, y_pred = np.array(y_true), np.array(y_pred)
    return np.mean(np.abs((y_true - y_pred) / y_true)) * 100


def  RMSE(expected,predictions):
    mse = mean_squared_error(expected, predictions)
    rmse = sqrt(mse)
    return rmse

def objective_function (x,l,h,s):
    objectiveValue = h*l/(x-l)+s*x**2
    return objectiveValue

def first_derivertive (x,l,h,s):
    return 2*s*x-(h*l)/(x-l)**2

def second_derivertive (h,s,l,x):
    sec = (h*l/s)**(1/3) + l
    return sec

def get_optimal_process_rate (l,h,s):
    roots = fsolve(first_derivertive, l + 0.01,args=(l,h,s),full_output = False)
    return roots[0]

def get_utilization(l,x):
    utilization = l/x
    return utilization

def get_expected_queue(l,h,s,availableProcessRates):
    processRate = min(get_optimal_process_rate(l,h,s),max(availableProcessRates))
    if processRate <= l:
        l=availableProcessRates[-2]
    utilization = get_utilization(l,processRate)
    E_LQ = int(round(utilization**2/(1-utilization),0))
    return E_LQ

def get_total_cost(LQ,h,s,processRates,tmax,LS_tmax):
    holdingCost = sum([period * h for period in LQ])
    serviceCost = sum([(processRates[i+1][0]-processRates[i][0]) * s *processRates[i][1]**2 for i in range(len(processRates)-1)] + 
    [ (tmax-processRates[-1][0])* s * processRates[-1][1]**2])
    endOfHorizonCost = LS_tmax/processRates[-1][1]*(h/2*LS_tmax+s*processRates[-1][1]**2)
    totalCost = holdingCost+serviceCost+endOfHorizonCost
    return totalCost

def evaluate_run_detail(LQ,h,s,processRates,tmax,LS_tmax):
    holdingCostPerPeriod = [period * h for period in LQ]
    serviceCostPerPeriod = [next(processRates[index-1][1]**2*s for index,value in enumerate(processRates) if value[0] > tnow) if tnow<processRates[-1][0] else processRates[-1][1]**2*s for tnow in range(len(LQ)) ]
    totalCostPerPeriod = [holdingCostPerPeriod[i]+serviceCostPerPeriod[i] for i in range(tmax)]
    #print(sum(holdingCostPerPeriod))
    #print(sum(serviceCostPerPeriod))
    totalCost = get_total_cost(LQ,h,s,processRates,tmax,LS_tmax)
    return holdingCostPerPeriod,serviceCostPerPeriod,totalCostPerPeriod,totalCost

def get_arrival_rate_per_Period(arrivalRates,tmax):
    arrivalRatePerPeriod = [next(arrivalRates[index-1][1] for index,value in enumerate(arrivalRates) if value[0] > tnow) if tnow<arrivalRates[-1][0] else arrivalRates[-1][1] for tnow in range(tmax) ]
    return arrivalRatePerPeriod

def get_process_rate_per_Period(processRates,tmax):
    processRatePerPeriod = [next(processRates[index-1][1] for index,value in enumerate(processRates) if value[0] > tnow) if tnow<processRates[-1][0] else processRates[-1][1] for tnow in range(tmax) ]
    return processRatePerPeriod

def create_output(numberOfScenarios,arrivalRates,processRates,tmax,h,s,LQ,LS_tmax):
    
    holdingCostPerPeriod,serviceCostPerPeriod,totalCostPerPeriod,totalCost = evaluate_run_detail(LQ,h,s,processRates,tmax,LS_tmax)
    output = {
            "numberOfScenarios":numberOfScenarios, 
            "holdingCost":h, 
            "serviceCost":s, 
            "arrivalRate":copy.deepcopy(arrivalRates), 
            "processRates":copy.deepcopy(processRates), 
            "totalCost":totalCost, 
            "TimeSeries":{ 
                    "LQ":LQ, 
                    "serviceCost":serviceCostPerPeriod, 
                    "holdingCost":holdingCostPerPeriod, 
                    "totalCost":totalCostPerPeriod, 
                    "arrivalRate":get_arrival_rate_per_Period(arrivalRates,tmax), 
                    "processRate":get_process_rate_per_Period(processRates,tmax) 
                        } 
            }
    return output

def output_to_excel(projectName,output,bestResult,runtime=0):
    #+str(datetime.datetime.now().strftime("%Y_%m_%d_%H-%M"))
    fileName = projectName + " " +str(datetime.datetime.now().strftime("%Y_%m_%d_%H-%M")) + ".xlsx"
    writer = pd.ExcelWriter("Results/" + fileName)

    dfOverview = pd.DataFrame([
                    runtime,
                    output[0]["numberOfScenarios"],
                    runtime/output[0]["numberOfScenarios"],
                    bestResult["Output"]["processRates"],
                    bestResult["Output"]["totalCost"],
                    ],
                    index=["Runtime","Number of Scenarios","Time per Scenario","Process Rates","Total Cost"])
    dfOverview.to_excel(writer,'Overview')

    KPIs = ["numberOfScenarios","holdingCost","serviceCost","arrivalRate","processRates","totalCost"]
    dfKPIOutput = pd.DataFrame([[entry[KPI] for KPI in KPIs] for entry in output],columns=KPIs)
    dfKPIOutput.to_excel(writer,'KPIs')

    TimeSeries = list(output[0]["TimeSeries"].keys())
    for TimeSerie in TimeSeries:
        dfTimeSerie = pd.DataFrame([entry["TimeSeries"][TimeSerie] for entry in output]) 
        dfTimeSerie.to_excel(writer,TimeSerie)
    writer.save()




def save_output_graph(projectName,output,show = False):
    myFig = plt.figure(figsize=(12,8))
    costPlot = myFig.add_subplot(221)
    paraPlot = myFig.add_subplot(222)
    lqPlot = myFig.add_subplot(212)

    costPlot.plot(output["TimeSeries"]["serviceCost"],label="Production Cost")
    costPlot.plot(output["TimeSeries"]["holdingCost"],label="Holding Cost")
    costPlot.plot(output["TimeSeries"]["totalCost"],label="Total Cost")
    costPlot.legend(frameon=False)

    paraPlot.plot(output["TimeSeries"]["arrivalRate"],label="Arrival Rate")
    paraPlot.plot(output["TimeSeries"]["processRate"],label="Process Rate")
    util = [output["TimeSeries"]["arrivalRate"][i] /output["TimeSeries"]["processRate"][i] for i in range(len(output["TimeSeries"]["processRate"]))]
    paraPlotTwin = paraPlot.twinx()
    
    paraPlotTwin.plot(util,label="Utilization",color = "green")
    paraPlot.legend(loc='upper right',frameon=False)
    paraPlotTwin.legend(loc=(0.653,0.74),frameon=False)
    paraPlotTwin.set_ylabel('Utilization')
    paraPlotTwin.set_ylim([0,max(1,max(util))])

    lqPlot.plot(output["TimeSeries"]["LQ"],label="Length of Queue")
    lqPlot.legend(frameon=False)
    fileName = projectName + " " +str(datetime.datetime.now().strftime("%Y_%m_%d_%H-%M")) + ".png"
    myFig.savefig("Results/" +fileName, dpi=myFig.dpi)
    if show == True:
        plt.show()

