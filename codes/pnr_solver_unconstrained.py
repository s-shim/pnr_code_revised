import pandas as pd
import random 
from gurobipy import *
import math

# (numHubs,numAlternatives,numOrigins,numInstances) = (15,30,100,10)
# (numHubs,numAlternatives,numOrigins,numInstances) = (30,60,200,10)
(numHubs,numAlternatives,numOrigins,numInstances) = (45,90,300,10)

instance = 0

grandAlternatives = pd.read_csv('pnr_list_corrected.csv')
grandIndividuals = pd.read_csv('pnr_utility_corrected.csv')
numDestins = 3 # fixed
tolError = 7 # limit of error of odds

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

# ILP Model
model = Model('pnr')

# Employ Variables
y_vars = []
y_names = []
for j in subAlternatives['id']:
    y_vars += [(j)]
    y_names += ['Y[%s]'%(j)]
Y = model.addVars(y_vars, vtype = GRB.BINARY, name = y_names)

p_vars = []
p_names = []
for taz in subIndividuals['TAZ']:
    for destin in range(numDestins):
        p_vars += [(taz,destin,0)]
        p_names += ['P[%s,%s,%s]'%(taz,destin,0)]
        for j in subAlternatives['id']:
            p_vars += [(taz,destin,j)]
            p_names += ['P[%s,%s,%s]'%(taz,destin,j)]
P = model.addVars(p_vars, vtype = GRB.CONTINUOUS, name = p_names)
            
# Add Constraints

## Given Number of Hubs
LHS = []
for j in subAlternatives['id']:
    LHS += [(1,Y[j])]
model.addConstr(LinExpr(LHS)==numHubs, name='p-Hub')
            
## P <= Y            
for taz in subIndividuals['TAZ']:
    for destin in range(numDestins):
        for j in subAlternatives['id']:
            LHS = [(1,P[taz,destin,j]),(-1,Y[j])]
            model.addConstr(LinExpr(LHS)<=0, name='P<=Y[%s,%s,%s]'%(taz,destin,j))
            
## Entire Probability = 1
for taz in subIndividuals['TAZ']:
    for destin in range(numDestins):
        LHS = [(1,P[taz,destin,0])]
        for j in subAlternatives['id']:
            LHS += [(1,P[taz,destin,j])]
        model.addConstr(LinExpr(LHS)==1, name='sumP=1[%s,%s]'%(taz,destin))
        
## 1. P[taz,destin,j] <= odds[taz,destin,j] * P[taz,destin,0]
## 2. P[taz,destin,0] <= 1 / odds[taz,destin,j] * P[taz,destin,j] + (1 - Y[j]) 
for taz in subIndividuals['TAZ']:
    for destin in range(numDestins):
        for j in subAlternatives['id']:
# =============================================================================
#             LHS1 = [(-odds[taz,destin,j],P[taz,destin,0])]
#             LHS1 += [(1,P[taz,destin,j])]
#             model.addConstr(LinExpr(LHS1)<=0, name='choice<=base[%s,%s,%s]'%(taz,destin,j))
# =============================================================================

            if odds[taz,destin,j] > 10 ** (-tolError) and odds[taz,destin,j] < 10 ** tolError:
                LHS1 = [(-odds[taz,destin,j],P[taz,destin,0])]
                LHS1 += [(1,P[taz,destin,j])]
                model.addConstr(LinExpr(LHS1)<=0, name='choice<=base[%s,%s,%s]'%(taz,destin,j))
    
                LHS2 = [(1,P[taz,destin,0])]
                LHS2 += [(- 1 / odds[taz,destin,j],P[taz,destin,j]),(1,Y[j])]
                model.addConstr(LinExpr(LHS2)<=1, name='choice>=base[%s,%s,%s]'%(taz,destin,j))

            if odds[taz,destin,j] <= 10 ** (-tolError):
                LHS1 = [(1,P[taz,destin,j])]
                model.addConstr(LinExpr(LHS1)==0, name='choice<=base[%s,%s,%s]'%(taz,destin,j))

            if odds[taz,destin,j] >= 10 ** tolError:
                print('Too large an odds[taz,destin,j]=',odds[taz,destin,j])
                

# Set Objective
objTerms = []
for taz in subIndividuals['TAZ']:
    for destin in range(numDestins):
        for j in subAlternatives['id']:
            objTerms += [(Flow[taz,destin],P[taz,destin,j])]
model.setObjective(LinExpr(objTerms), GRB.MAXIMIZE)

            
# update and solve the model
model.update()
#model = model.relax()
model.optimize()


variableName = []
variableValue = []
for v in model.getVars():
    variableName += [v.varname]
    variableValue += [v.x]

optSolution = pd.DataFrame(list(zip(variableName, variableValue)),columns =['varName', 'varVal'])
optSolution.to_csv(r'opt_unconstrained_pnr_origin%s_I%s_J%s_p%s_inst%s.csv'%(numOrigins,numOrigins*numDestins,numAlternatives,numHubs,instance), index = False)#Check

underCapacity = 0
overCapacity = 0
accurate = 0.0
theSelected = []  
constrainedVal = 0.0          
for j in subAlternatives['id']:
    [Y_j] = optSolution.loc[optSolution['varName']=='Y[%s]'%(j),'varVal']
    if Y_j > 1 - 0.0001:
        theSelected += [j]            
        [capacity_j] = grandAlternatives.loc[grandAlternatives['id']==j,'capacity']
        expectedNum = 0.0
        for taz in subIndividuals['TAZ']:
            for destin in range(numDestins):
                [probability_ij] = optSolution.loc[optSolution['varName']=='P[%s,%s,%s]'%(taz,destin,j),'varVal']
                expectedNum += Flow[taz,destin] * probability_ij
                accurate += Flow[taz,destin] * probability_ij            
        if expectedNum <= capacity_j:
            print(j, expectedNum, capacity_j, 'under capacity')
            underCapacity += 1
            constrainedVal += expectedNum          
        else:
            print(j, expectedNum, capacity_j, 'over capacity')
            overCapacity += 1
            constrainedVal += capacity_j          
            
print('ILP OPT Val=',model.objVal)
print('accurate=',accurate)
print('underCapacity=',underCapacity)
print('overCapacity=',overCapacity)
print('accurate assuming constrained=',constrainedVal)
        
