#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Nov  6 15:37:37 2016

@author: marleneguraieb
"""
import pandas as pd
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import os
from datetime import timedelta

matplotlib.style.use('ggplot') # Look Pretty

os.chdir('/Users/marleneguraieb/Google Drive/Healthcare_metrics')

#We're going to need TMT stats

TMTstats = pd.read_table('DATA/TMTstats.csv')

TMTstats.TMTdate = pd.to_datetime(TMTstats.TMTdate,format = '%Y-%m-%d')

#And ATEbyNurse

ATEbyNurse = pd.read_table('DATA/ATEbyNurse.csv')

ATEbyNurse = pd.merge(ATEbyNurse,TMTstats[['Medical_unit', 
                                           'Treatment','MatchItCR','MatchItCC']],
                      how = 'left',left_on = 'ExpectedUnitAtTMT', 
                      right_on = 'Medical_unit')

#Now let's get all the unique ones here:
tempDF = ATEbyNurse[['NurseID','ExpectedUnitAtTMT', 'treatment', 'TMT_Date', 'Medical_unit',
           'Treatment', 'MatchItCR', 'MatchItCC']].copy()

tempDF = tempDF.drop_duplicates()

ATEbyNurse = pd.pivot_table(ATEbyNurse, index=['NurseID'],columns='TMT_time',
                                  values = ['NumConsPer','Grade1',
                                         'Said1or2Lab0_Said1','Said9LabNo_cons',
                                         'Said0LabNo_Toc'])
#i forgot the underscore :)
#ATEbyNurse.columns = [w.replace('t_', '_t_') for w in ATEbyNurse.columns.tolist()]

ATEbyNurse.columns =[s1 +'_'+ str(s2) for (s1,s2) in ATEbyNurse.columns.tolist()]

ATEbyNurse = pd.merge(ATEbyNurse,tempDF,how='inner',left_index=True,right_on='NurseID')


cols = ATEbyNurse.columns.values.tolist()
t_0_2013 = [cols.index(s) for s in cols if 't_0_2013' in s]
t_1_2013 = [cols.index(s) for s in cols if 't_1_2013' in s]
t_0_2014 = [cols.index(s) for s in cols if 't_0_2014' in s]
t_1_2014 = [cols.index(s) for s in cols if 't_1_2014' in s]

for i in range(1,5):
    ATEbyNurse[ATEbyNurse.columns.tolist()[t_0_2013[i]].replace('_t_0_2013',
    '_Dif2013')] = ATEbyNurse.ix[:,t_1_2013[i]-t_0_2013[i]]
    ATEbyNurse[ATEbyNurse.columns.tolist()[t_0_2014[i]].replace('_t_0_2014',
    '_Dif2014')] = ATEbyNurse.ix[:,t_1_2014[i]-t_0_2014[i]]

cols = ATEbyNurse.columns.values.tolist()
values = ['Grade1','Said1or2Lab0_Said1','Said9LabNo_cons','Said0LabNo_Toc']

for i in range(0,4):                          
    difs = [cols.index(s) for s in cols if values[i] in s]
    ATEbyNurse[cols[difs[5]].replace('Dif2014','d13_14')] = ATEbyNurse[cols[difs[5]]]-ATEbyNurse[cols[difs[4]]]

ATEbyNurse['NumCons2013'] = (ATEbyNurse['NumConsPer_t_0_2013']+ATEbyNurse['NumConsPer_t_1_2013'])/2
ATEbyNurse['NumCons2014'] = (ATEbyNurse['NumConsPer_t_0_2014']+ATEbyNurse['NumConsPer_t_1_2014'])/2

ATEbyNurse['NumCons2013'] = ATEbyNurse['NumCons2013'].fillna(0)
ATEbyNurse['NumCons2014'] = ATEbyNurse['NumCons2014'].fillna(0)

ResultsbyClin = ATEbyNurse[['ExpectedUnitAtTMT','Grade1_Dif2014', 'Said1or2Lab0_Said1_Dif2014',
       'Said9LabNo_cons_Dif2014', 'Said0LabNo_Toc_Dif2014', 'Grade1_d13_14',
       'Said1or2Lab0_Said1_d13_14', 'Said9LabNo_cons_d13_14',
       'Said0LabNo_Toc_d13_14']].groupby(ATEbyNurse['ExpectedUnitAtTMT']).apply(lambda x: 
    np.average(x.wt, weights=ATEbyNurse['NumCons2014'].sum()))
           
# Define a lambda function to compute the weighted mean:
wm = lambda x: np.average(x.fillna(0), weights=ATEbyNurse.loc[x.index, 'NumCons2014'].fillna(0))

# Define a dictionary with the functions to apply for a given column:
f = {'Grade1_Dif2014': {'weighted_mean': wm}, 
     'Said1or2Lab0_Said1_Dif2014': {'weighted_mean': wm},
     'Said9LabNo_cons_Dif2014': {'weighted_mean': wm}, 
     'Said0LabNo_Toc_Dif2014': {'weighted_mean':wm},
     'Grade1_d13_14': {'weighted_mean': wm}, 
     'Said1or2Lab0_Said1_d13_14': {'weighted_mean': wm}, 
     'Said9LabNo_cons_d13_14': {'weighted_mean': wm},
     'Said0LabNo_Toc_d13_14': {'weighted_mean': wm}}

# Groupby and aggregate with your dictionary:
ATEbyNurse.groupby(['ExpectedUnitAtTMT']).agg(f)


 