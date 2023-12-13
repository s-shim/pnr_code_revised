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
#timeLimit = 60

lambdaNL = 0.25

(numHubs,numAlternatives,numOrigins,instance) = (60,120,400,0)

instance = 0

grandAlternatives = pd.read_csv('pnr_list_corrected.csv')
grandIndividuals = pd.read_csv('pnr_utility_corrected.csv')
numDestins = 3 # fixed

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

theSelected = []
bestSolution = pd.read_csv('opt_constrained_pnr_origin400_I1200_J120_p60_inst0.csv')
for varName in bestSolution['varName']:
    if varName[0] == 'Y':
        [varVal] = bestSolution.loc[bestSolution['varName']==varName,'varVal']
        if float(varVal) > 1 - 0.0004:
            selected = int(varName[2:-1])
            theSelected += [selected]

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

print('lambdaNL=',lambdaNL)            
print('totalDemand=',totalDemand)        


