import pandas as pd
import random 
from gurobipy import *
import math
import copy
import time
import datetime
import socket
from itertools import combinations

machineName = socket.gethostname()
print(machineName)
print(datetime.datetime.now())

lambdaNL = 0.5
numDestins = 3 # fixed
tolError = 7 # limit of error of odds

for (numHubs,numAlternatives,numOrigins) in [(6,30,100),(24,30,100),(12,30,100),(18,30,100)]:

    grandAlternatives = pd.read_csv('pnr_list_corrected.csv')
    grandIndividuals = pd.read_csv('pnr_utility_corrected.csv')
        
    instance = 0
    
    for instance in range(10):
        
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
        
        bestDemand = 0.0
        tic = time.time() 
        machineArray = []
        lambdaArray = []
        toc = time.time() 
        timeArray = []
        demandArray = []
        selectedArray = {}
        for num in range(numHubs):
            selectedArray[num] = []
        
        for comb in combinations(list(subAlternatives['id']),numHubs):
            theSelected = list(comb)
        
        
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
                totalDemand += min(demand_j,capacity_j)
                #totalDemand += demand_j # unconstrained
                    
                
            if bestDemand < totalDemand:
                bestDemand = totalDemand
                bestSelected = copy.deepcopy(sorted(theSelected))
        
                print()
                toc = time.time()
                print('elapse time=',toc-tic)
                print('bestDemand=',bestDemand)
            
                machineArray += [machineName]
                lambdaArray += [lambdaNL]
                timeArray += [toc-tic]
                demandArray += [bestDemand]
        
                for num in range(numHubs):
                    selectedArray[num] += [bestSelected[num]]
        
                bestSolution = pd.DataFrame(list(zip(machineArray,lambdaArray,timeArray,demandArray)),columns =['Machine','Lambda','Time','Demand'])
                for num in range(numHubs):
                    bestSolution['selectedHub%s'%num] = selectedArray[num] 
        
                bestSolution.to_csv(r'bfs_NL_constrained_pnr_origin%s_I%s_J%s_p%s_inst%s_lambda%s.csv'%(numOrigins,numOrigins*numDestins,numAlternatives,numHubs,instance,int(lambdaNL * 10)), index = False)#Check
        
        machineArray += ['FINISH']
        lambdaArray += [lambdaNL]
        timeArray += [toc-tic]
        demandArray += [bestDemand]

        for num in range(numHubs):
            selectedArray[num] += [bestSelected[num]]

        bestSolution = pd.DataFrame(list(zip(machineArray,lambdaArray,timeArray,demandArray)),columns =['Machine','Lambda','Time','Demand'])
        for num in range(numHubs):
            bestSolution['selectedHub%s'%num] = selectedArray[num] 

        bestSolution.to_csv(r'bfs_NL_constrained_pnr_origin%s_I%s_J%s_p%s_inst%s_lambda%s.csv'%(numOrigins,numOrigins*numDestins,numAlternatives,numHubs,instance,int(lambdaNL * 10)), index = False)#Check
