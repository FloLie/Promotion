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
from heuristics import SIPP,independent_opt,simple_hill_climbing,steepest_ascent_hill_climbing

if __name__ == '__main__':
    rd.seed (42)
    numberOfScenarios = 2000

    arrivalType = "Time Dependent"
    processType = "Time Dependent"    
    h  = 120
    s = 5
    macroLength = 3

    arrivalProcess = [6,6,6,16,14,3,3,3,16,15,14,1,7,7]
    arrivalRates = [[i*macroLength,arrivalProcess[i]] for i in range(len(arrivalProcess))]

    tmax = len(arrivalProcess)*macroLength
    availableProcessRates = [1 + i for i in range(15)]
    initQueue = 0

    start_timer = time()
    SIPP_result,SIPP_best_result = SIPP(numberOfScenarios,arrivalRates,h,s,tmax,availableProcessRates,initQueue)
    print("-----SIPP-----")
    print("Total Cost: "+str(SIPP_best_result["TotalCost"]) + " after "+str(3) +" evaluations")
    print([i[1] for i in SIPP_best_result["Output"]["processRates"]])
    print(time()-start_timer)

    start_timer = time()
    print("-----SHC-----")
    SHC_result,SHC_best_result,SHC_result_developement =simple_hill_climbing(numberOfScenarios,arrivalRates,h,s,tmax,availableProcessRates,initQueue)
    print([i[1] for i in SHC_best_result["Output"]["processRates"]])
    print(time()-start_timer)

    start_timer = time()
    print("-----IND-----")
    independent_result,independent_best_result = independent_opt(numberOfScenarios,arrivalRates,h,s,tmax,availableProcessRates,initQueue,macroLength)
    print([i[1] for i in independent_best_result["Output"]["processRates"]])
    print(time()-start_timer)
    
    start_timer = time()
    print("-----SAHC-----")
    SAHC_result,SAHC_best_result,SAHC_result_developement =  steepest_ascent_hill_climbing(numberOfScenarios,arrivalRates,h,s,tmax,availableProcessRates,initQueue,macroLength)
    print([i[1] for i in SAHC_best_result["Output"]["processRates"]])
    print(time()-start_timer)

    print("_________________________________")
    save_output_graph("SHC Best Result",SHC_best_result["Output"],True)

