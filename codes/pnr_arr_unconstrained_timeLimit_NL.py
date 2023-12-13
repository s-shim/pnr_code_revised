import pandas as pd
import random 
from gurobipy import *
import math
import copy
import time
import datetime
import socket

machineName = socket.gethostname()
print(machineName)
print(datetime.datetime.now())

#trialLimit = 100000
timeLimit = 60


# =============================================================================
# (numHubs,numAlternatives,numOrigins,numInstances) = (15,30,100,10)
# instance = 0
# 
# grandAlternatives = pd.read_csv('pnr_list_csv.csv')
# grandIndividuals = pd.read_csv('pnr_utility.csv')
# numDestins = 3 # fixed
# tolError = 7 # limit of error of odds
# 
# subAlternatives = pd.read_csv('pnr_list_csv.csv')
# subIndividuals = pd.read_csv('pnr_utility.csv')
# 
# numHubs = int(len(subAlternatives['id']) / 2)
# numAlternatives = len(subAlternatives['id'])
# numOrigins = len(subIndividuals['TAZ'])
# =============================================================================

lambdaNL = 0.5

(numAlternatives,numOrigins,numInstances) = (30,100,10)
numHubs = int(numAlternatives / 2 + 0.0001)

instance = 0

grandAlternatives = pd.read_csv('pnr_list_corrected.csv')
grandIndividuals = pd.read_csv('pnr_utility_corrected.csv')
numDestins = 3 # fixed
tolError = 7 # limit of error of odds

subAlternatives = pd.read_csv('./data/pnr_J%s_inst%s.csv'%(numAlternatives,instance))
subIndividuals = pd.read_csv('./data/origin%s_I%s_inst%s.csv'%(numOrigins, numOrigins * numDestins, instance))


util = {}
for taz in subIndividuals['TAZ']:
    for destin in range(numDestins):
        j = 0 # j = 0 : car
        [utility] = grandIndividuals.loc[grandIndividuals['TAZ']==taz,'U_car_CBD%s'%(destin)]
        util[taz,destin,j] = float(utility) 

for taz in subIndividuals['TAZ']:
    for destin in range(numDestins):
        for j in subAlternatives['id']:
            [utility] = grandIndividuals.loc[grandIndividuals['TAZ']==taz,'U_pnr_corr_%s_CBD_%s'%(j,destin)]
            util[taz,destin,j] = float(utility) 

            
Flow = {}
for taz in subIndividuals['TAZ']:
    for destin in range(numDestins):
        [flow_i] = grandIndividuals.loc[grandIndividuals['TAZ']==taz,'car_to_CBD%s'%(destin)]
        Flow[taz,destin] = flow_i

halfY = {}
for j in subAlternatives['id']:
    halfY[j] = 0.5
    
tic = time.time()
# seed -> perturb     
seedY = copy.deepcopy(halfY)
ptbY = {}
for j in subAlternatives['id']:
    ptbY[j] = seedY[j] * random.random()


# theSelected = ROUND(ptb)
theSelected = []
jToProcess = copy.deepcopy(list(subAlternatives['id']))
while len(theSelected) < numHubs:
    largest = 0.0    
    largestJ = -1
    for j in jToProcess:
        if largest < ptbY[j]:
            largest = ptbY[j]
            largestJ = j
    jToProcess.remove(largestJ)
    theSelected += [largestJ]


# demand(theSelected)
totalPW_PNR_NL = {}
for taz in subIndividuals['TAZ']:
    for destin in range(numDestins):
        totalPW_PNR_NL[taz,destin] = 0.0
        for j in theSelected:
            totalPW_PNR_NL[taz,destin] += math.exp(util[taz,destin,j]/lambdaNL)

gamma = {}
for taz in subIndividuals['TAZ']:
    for destin in range(numDestins):
        gamma[taz,destin] = 0.0 # compute gamma_i
        for j in theSelected:
            gamma[taz,destin] += math.exp(util[taz,destin,j]/lambdaNL)
        gamma[taz,destin] = math.log(gamma[taz,destin])
        
totalDemand = 0.0
for j in theSelected:
    demand_j = 0.0
    for taz in subIndividuals['TAZ']:
        for destin in range(numDestins):
            demand_j += Flow[taz,destin] * (math.exp(lambdaNL * gamma[taz,destin]) / (math.exp(util[taz,destin,0]) + math.exp(lambdaNL * gamma[taz,destin]))) * (math.exp(util[taz,destin,j]/lambdaNL) / totalPW_PNR_NL[taz,destin])
    [capacity_j] = grandAlternatives.loc[grandAlternatives['id']==j,'capacity']
    #totalDemand += min(demand_j,capacity_j)
    totalDemand += demand_j # unconstrained


# record trial = 0
bestDemand = totalDemand
bestSelected = copy.deepcopy(sorted(theSelected))
trial = 0
nLocal = 0
reset = False
print()
print('trial=',trial)
toc = time.time()
print('elapse time=',toc-tic)
print('bestDemand=',bestDemand)

machineArray = [machineName]
lambdaArray = [lambdaNL]
trialArray = [trial]
timeArray = [toc-tic]
demandArray = [bestDemand]

selectedArray = {}
for num in range(numHubs):
    selectedArray[num] = [bestSelected[num]]

bestSolution = pd.DataFrame(list(zip(machineArray,trialArray,timeArray,demandArray)),columns =['Machine','Trial','Time','Demand'])
for num in range(numHubs):
    bestSolution['selectedHub%s'%num] = selectedArray[num] 

bestSolution.to_csv(r'arr_unconstrained_pnr_origin%s_I%s_J%s_p%s_inst%s.csv'%(numOrigins,numOrigins*numDestins,numAlternatives,numHubs,instance), index = False)#Check

toc = time.time()
elapseTime = toc - tic
while elapseTime < timeLimit:
    
    trial += 1

    # compute RMSD
    RMSD = 0.0
    for j in subAlternatives['id']:
        RMSD += (seedY[j] - 0.5) ** 2
    RMSD = math.sqrt(RMSD / len(subAlternatives['id']))

    # seed -> perturb     
    ptbY = {}
    for j in subAlternatives['id']:
        ptbY[j] = seedY[j] * random.random()
    
    # theSelected = ROUND(ptb)
    theSelected = []
    jToProcess = copy.deepcopy(list(subAlternatives['id']))
    while len(theSelected) < numHubs:
        largest = 0.0    
        largestJ = -1
        for j in jToProcess:
            if largest < ptbY[j]:
                largest = ptbY[j]
                largestJ = j
        jToProcess.remove(largestJ)
        theSelected += [largestJ]
        
        
    # check theSelected = bestSelected
    same = True
    for j in bestSelected:
        if j not in theSelected:
            same = False
            break
        
    if same == True:
        nLocal += 1
        
        # compute reset probability
        ## pR = probability of reset
        pR = min(1,nLocal/20) * RMSD
        if pR > random.random():
            reset = True
            seedY = copy.deepcopy(halfY)
            nLocal = 0
            
    else:
        nLocal = 0
        reset = False
        
        # demand(theSelected)
        totalPW_PNR_NL = {}
        for taz in subIndividuals['TAZ']:
            for destin in range(numDestins):
                totalPW_PNR_NL[taz,destin] = 0.0
                for j in theSelected:
                    totalPW_PNR_NL[taz,destin] += math.exp(util[taz,destin,j]/lambdaNL)
        
        gamma = {}
        for taz in subIndividuals['TAZ']:
            for destin in range(numDestins):
                gamma[taz,destin] = 0.0 # compute gamma_i
                for j in theSelected:
                    gamma[taz,destin] += math.exp(util[taz,destin,j]/lambdaNL)
                gamma[taz,destin] = math.log(gamma[taz,destin])
                
        totalDemand = 0.0
        for j in theSelected:
            demand_j = 0.0
            for taz in subIndividuals['TAZ']:
                for destin in range(numDestins):
                    demand_j += Flow[taz,destin] * (math.exp(lambdaNL * gamma[taz,destin]) / (math.exp(util[taz,destin,0]) + math.exp(lambdaNL * gamma[taz,destin]))) * (math.exp(util[taz,destin,j]/lambdaNL) / totalPW_PNR_NL[taz,destin])
            [capacity_j] = grandAlternatives.loc[grandAlternatives['id']==j,'capacity']
            #totalDemand += min(demand_j,capacity_j)
            totalDemand += demand_j # unconstrained
            
            
        if bestDemand < totalDemand:
            bestDemand = totalDemand
            bestSelected = copy.deepcopy(sorted(theSelected))            
            print()
            print('trial=',trial)
            toc=time.time()
            print('elapse time=',toc-tic)
            print('bestDemand=',bestDemand)

            machineArray += [machineName]
            lambdaArray += [lambdaNL]
            trialArray += [trial]
            timeArray += [toc-tic]
            demandArray += [bestDemand]
            
            for num in range(numHubs):
                selectedArray[num] += [bestSelected[num]]
            
            bestSolution = pd.DataFrame(list(zip(machineArray,lambdaArray,trialArray,timeArray,demandArray)),columns =['Machine','Lambda','Trial','Time','Demand'])
            for num in range(numHubs):
                bestSolution['selectedHub%s'%num] = selectedArray[num] 
            
            bestSolution.to_csv(r'arr_unconstrainedNL_pnr_origin%s_I%s_J%s_p%s_inst%s_lambda(%s).csv'%(numOrigins,numOrigins*numDestins,numAlternatives,numHubs,instance,lambdaNL), index = False)#Check
        
    if reset == False:
        alpha = 1 / (1 + math.exp(4 * RMSD))
        for j in subAlternatives['id']:
            seedY[j] = (1 - alpha) * seedY[j]
        for j in bestSelected:
            seedY[j] += alpha 
        
    toc = time.time()
    elapseTime = toc - tic




