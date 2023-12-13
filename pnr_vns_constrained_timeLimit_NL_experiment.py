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

for instance in [0]:
    for multiple in [4]:
        for (numHubsB,numAlternativesB,numOriginsB) in [(15,30,100)]:
            for lambdaNL in [0.5,0.25,0.75]:
                for rep in range(1):
        
                    numHubs = numHubsB * multiple
                    numAlternatives = numAlternativesB * multiple
                    numOrigins = numOriginsB * multiple
                
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
                    
                    nonSelected = copy.deepcopy(jToProcess)
                    
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
                                        
                    
                    # record trial = 0
                    bestDemand = totalDemand
                    bestSelected = copy.deepcopy(sorted(theSelected))
                    bestNonSelected = copy.deepcopy(sorted(nonSelected))
                    
                    
                    machineArray = [machineName]
                    toc = time.time()
                    timeArray = [toc-tic]
                    demandArray = [bestDemand]
                    lambdaArray = [lambdaNL]
                    
                    selectedArray = {}
                    for num in range(numHubs):
                        selectedArray[num] = [bestSelected[num]]
                    
                    bestSolution = pd.DataFrame(list(zip(machineArray,lambdaArray,timeArray,demandArray)),columns =['Machine','Lambda','Time','Demand'])
                    for num in range(numHubs):
                        bestSolution['selectedHub%s'%num] = selectedArray[num] 
                    
                    bestSolution.to_csv(r'vns_constrained_pnr_origin%s_I%s_J%s_p%s_inst%s_rep%s_lambda%s.csv'%(numOrigins,numOrigins*numDestins,numAlternatives,numHubs,instance,rep,int(lambdaNL * 10)), index = False)#Check
                    
                    
                    improve = True
                    while improve == True:
                        improve = False
                        for selected in bestSelected:
                            if improve == True:
                                break
                            
                            for notSelected in bestNonSelected:
                                theSelected = copy.deepcopy(bestSelected)
                                theSelected.remove(selected)
                                theSelected.append(notSelected)
                                nonSelected = copy.deepcopy(bestNonSelected)
                                nonSelected.remove(notSelected)
                                nonSelected.append(selected)
                    
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
                                    improve = True
                                    bestDemand = totalDemand
                                    bestSelected = copy.deepcopy(sorted(theSelected))
                                    bestNonSelected = copy.deepcopy(sorted(nonSelected))
                                    print()
                                    toc = time.time()
                                    print('elapse time=',toc - tic)
                                    print('best solution=',bestDemand)
                    
                                    machineArray += [machineName]
                                    timeArray += [toc-tic]
                                    demandArray += [bestDemand]
                                    lambdaArray += [lambdaNL]
                                    
                                    for num in range(numHubs):
                                        selectedArray[num] += [bestSelected[num]]
                                    
                                    bestSolution = pd.DataFrame(list(zip(machineArray,lambdaArray,timeArray,demandArray)),columns =['Machine','Lambda','Time','Demand'])
                                    for num in range(numHubs):
                                        bestSolution['selectedHub%s'%num] = selectedArray[num] 
                                    
                                    bestSolution.to_csv(r'vns_constrained_pnr_origin%s_I%s_J%s_p%s_inst%s_rep%s_lambda%s.csv'%(numOrigins,numOrigins*numDestins,numAlternatives,numHubs,instance,rep,int(lambdaNL * 10)), index = False)#Check
                    
                                    break
                                                
            
                    machineArray += ['FINISH']
                    timeArray += [toc-tic]
                    demandArray += [bestDemand]
                    lambdaArray += [lambdaNL]
                    
                    for num in range(numHubs):
                        selectedArray[num] += [bestSelected[num]]
                    
                    bestSolution = pd.DataFrame(list(zip(machineArray,lambdaArray,timeArray,demandArray)),columns =['Machine','Lambda','Time','Demand'])
                    for num in range(numHubs):
                        bestSolution['selectedHub%s'%num] = selectedArray[num] 
                    
                    bestSolution.to_csv(r'vns_constrained_pnr_origin%s_I%s_J%s_p%s_inst%s_rep%s_lambda%s.csv'%(numOrigins,numOrigins*numDestins,numAlternatives,numHubs,instance,rep,int(lambdaNL * 10)), index = False)#Check
                                
                                
                    
                    
                    
                    
