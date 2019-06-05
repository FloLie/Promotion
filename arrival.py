import random as rd
import math

def createJob(type, tnow, tmax, arrivalRate = None, arrivalSchedule = None):
    jobList = []
    if type == "Stationary":
        while tnow < tmax:
            interArrivalTime = rd.expovariate(arrivalRate)
            jobList.append(tnow + interArrivalTime)
            tnow += interArrivalTime
    if type == "Time Dependent":
        lastSwitch = arrivalSchedule[-1][0]
        while tnow < tmax:
            if tnow > lastSwitch:
                currentPosition = -1
            else:
                currentPosition = next(i for i,v in enumerate(arrivalSchedule) if v[0] > tnow)-1
                
            interArrivalTime = rd.expovariate(arrivalSchedule[currentPosition][1])

            if math.floor(tnow) < math.floor(tnow+interArrivalTime) and math.ceil(tnow) in [x[0] for x in arrivalSchedule]:
                interArrivalTime = math.ceil(tnow) - tnow + rd.expovariate(arrivalSchedule[currentPosition+ 1][1])

            jobList.append(tnow + interArrivalTime)
            tnow += interArrivalTime
    
    return jobList
