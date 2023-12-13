import pandas as pd
import random 

numAlternatives = 30
numOrigins = 100
numInstances = 10

individuals = pd.read_csv('pnr_utility.csv')
numDestins = 3 # fixed


for destin in range(numDestins):
    for j in range(170):
        individuals['U_pnr_corr_%s_CBD_%s'%(j+1,destin)] = individuals['U_pnr_%s_CBD_%s'%(j,destin)]

individuals.to_csv(r'pnr_utility_corrected.csv', index = False)#Check
