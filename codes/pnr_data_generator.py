import pandas as pd
import random 

numAlternatives = 30
numOrigins = 100
numInstances = 10

alternatives = pd.read_csv('pnr_list_corrected.csv')
individuals = pd.read_csv('pnr_utility_corrected.csv')
numDestins = 3 # fixed

for instance in range(numInstances):

    randomAlternatives = sorted(random.sample(list(alternatives['id']), k = numAlternatives))
    randomOrigins = sorted(random.sample(list(individuals['TAZ']), k = numOrigins))
    
    print('alternatives = ',randomAlternatives)
    print()
    print('individuals = ',randomOrigins)

    randomAlternativesTable = pd.DataFrame(list(zip(range(len(randomAlternatives)),randomAlternatives)),columns =['pnr','id'])
    randomAlternativesTable.to_csv(r'pnr_J%s_inst%s.csv'%(numAlternatives,instance), index = False)#Check
    
    randomOriginsTable = pd.DataFrame(list(zip(range(len(randomOrigins)),randomOrigins)),columns =['origin','TAZ'])
    randomOriginsTable.to_csv(r'origin%s_I%s_inst%s.csv'%(numOrigins, numOrigins * numDestins,instance), index = False)#Check


