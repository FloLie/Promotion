import random as rd
import math

def createProcessTime(type, tnow, processRate = None, processSchedule = None):
    if type == "Stationary":
        processTime = rd.expovariate(processRate)
        return processTime
    if type == "Time Dependent":
        lastSwitch = processSchedule[-1][0]
        if tnow > lastSwitch:
            currentPosition = -1
        else:
            currentPosition = next(i for i,v in enumerate(processSchedule) if v[0] > tnow)-1
            
        processTime = rd.expovariate(processSchedule[currentPosition][1])

        if math.floor(tnow) < math.floor(tnow+processTime) and math.ceil(tnow) in [x[0] for x in processSchedule]:
            #print("It is: " + str(tnow) + " and inter is: " +str(interArrivalTime))
            processTime = math.ceil(tnow) - tnow + rd.expovariate(processSchedule[currentPosition + 1][1])


    return processTime
