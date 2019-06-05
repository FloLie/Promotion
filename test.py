import numpy as np
import pandas as pd
import scipy as sc
import matplotlib.pyplot as plt
import random as rd
import time
from simulation import simProcess


rd.seed (42)

arrivalType = "Time Dependent"
processType = "Time Dependent"    
macroLength = 80

#arrivalProcess = [6,6,6,16,14,3,3,3,16,15,14,1,7,7]
arrivalProcess = [12,12]
processProcess = [12.6,12.6]
arrivalRates = [[i*macroLength,arrivalProcess[i]] for i in range(len(arrivalProcess))]
processRates = [[i*macroLength,processProcess[i]] for i in range(len(processProcess))]

tmax = len(arrivalProcess)*macroLength
numberOfScenarios = 10000
start = time.time()
KPI, LQ,LS_tmax =  sim(numberOfScenarios,arrivalRates,processRates,tmax,"Time Dependent","Time Dependent",jobs=30)
print(time.time()-start)
plt.plot(LQ)