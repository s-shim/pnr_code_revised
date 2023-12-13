import socket
import pandas as pd
import random 
from gurobipy import *
import math
import datetime
import time

machineName = socket.gethostname()

#(numHubs,numAlternatives,numOrigins,numInstances) = (15,30,100,10)
numInstances = 10
numDestins = 3 # fixed
tolError = 7 # limit of error of odds

grandAlternatives = pd.read_csv('pnr_list_corrected.csv')
grandIndividuals = pd.read_csv('pnr_utility_corrected.csv')

for (numAlternatives,numOrigins) in [(30,100),(60,200),(90,300),(120,400)]:
    numHubs = numAlternatives / 2 

    machineArray = []
    originArray = []
    iArray = []
    jArray = []
    pArray = []
    instanceArray = []
    ilpObjArray = []
    accurateArray = []    
    constrainedArray = []
    underArray = []
    overArray = []
    runArray = []
    

    for instance in range(numInstances):
        
        subAlternatives = pd.read_csv('./data/pnr_J%s_inst%s.csv'%(numAlternatives,instance))
        subIndividuals = pd.read_csv('./data/origin%s_I%s_inst%s.csv'%(numOrigins, numOrigins * numDestins, instance))
        
        pw = {} # preference weight
        for taz in subIndividuals['TAZ']:
            for destin in range(numDestins):
                j = 0 # j = 0 : car
                [utility] = grandIndividuals.loc[grandIndividuals['TAZ']==taz,'U_car_CBD%s'%(destin)]
                pw[taz,destin,j] = math.exp(utility)
        
        for taz in subIndividuals['TAZ']:
            for destin in range(numDestins):
                for j in subAlternatives['id']:
                    [utility] = grandIndividuals.loc[grandIndividuals['TAZ']==taz,'U_pnr_corr_%s_CBD_%s'%(j,destin)]
                    pw[taz,destin,j] = math.exp(utility)
        
        odds = {}
        for taz in subIndividuals['TAZ']:
            for destin in range(numDestins):
                for j in subAlternatives['id']:
                    odds[taz,destin,j] = pw[taz,destin,j] / pw[taz,destin,0]
                    
        Flow = {}
        for taz in subIndividuals['TAZ']:
            for destin in range(numDestins):
                [flow_i] = grandIndividuals.loc[grandIndividuals['TAZ']==taz,'car_to_CBD%s'%(destin)]
                Flow[taz,destin] = flow_i
              
        optSolution = pd.read_csv('./result_experiment_constrained/optSolution/opt_constrained_infeasible_pnr_origin%s_I%s_J%s_p%s_inst%s.csv'%(numOrigins,numOrigins*numDestins,numAlternatives,numHubs,instance))


        #accurate = 0.0
        theSelected = []  
        for j in subAlternatives['id']:
            [Y_j] = optSolution.loc[optSolution['varName']=='Y[%s]'%(j),'varVal']
            if Y_j > 1 - 0.0001:
                theSelected += [j]            

        # demand(theSelected)
        totalPW = {}
        for taz in subIndividuals['TAZ']:
            for destin in range(numDestins):
                totalPW[taz,destin] = pw[taz,destin,0]
                for j in theSelected:
                    totalPW[taz,destin] += pw[taz,destin,j]

        underCapacity = 0
        overCapacity = 0        
        unconstrainedDemand = 0.0
        constrainedDemand = 0.0
        for j in theSelected:
            demand_j = 0.0
            expectedNum = 0.0
            for taz in subIndividuals['TAZ']:
                for destin in range(numDestins):
                    demand_j += Flow[taz,destin] * pw[taz,destin,j] / totalPW[taz,destin]
            [capacity_j] = grandAlternatives.loc[grandAlternatives['id']==j,'capacity']
            constrainedDemand += min(demand_j,capacity_j)
            unconstrainedDemand += demand_j # unconstrained
            if demand_j > capacity_j:
                overCapacity += 1
                print(j,'over capacity',demand_j ,'>', capacity_j)
            else:
                underCapacity += 1
                print(j,'under capacity',demand_j ,'<=', capacity_j)
                                
        print('accurate=',unconstrainedDemand)
        print('underCapacity=',underCapacity)
        print('overCapacity=',overCapacity)
        print('accurate assuming constrained=',constrainedDemand)
        
        
        machineArray += [machineName]
        originArray += [numOrigins]
        iArray += [numOrigins*numDestins]
        jArray += [numAlternatives]
        pArray += [numHubs]
        instanceArray += [instance]
        #ilpObjArray += [model.objVal]
        accurateArray += [unconstrainedDemand]    
        constrainedArray += [constrainedDemand]
        underArray += [underCapacity]
        overArray += [overCapacity]
        #runArray += [model.Runtime]
        
        ilpTable = pd.DataFrame(list(zip(machineArray,originArray,iArray,jArray,pArray,instanceArray,accurateArray,constrainedArray,underArray,overArray)),columns =['Machine','Origins','I','J','p','instance','Accuarate','ifConstrained','underCapacity','overCapacity'])
        ilpTable.to_csv(r'recalculate_ilpTable_constrained_infeasible_pnr_origin%s_I%s_J%s_p%s.csv'%(numOrigins,numOrigins*numDestins,numAlternatives,numHubs), index = False)#Check

            
