#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Oct 31 10:45:12 2016

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

#Start from all the lab files

CACU = pd.read_csv('DATA/CACUJul9.csv')

#Rename columns to english
#Turnaround is how long it took to register and do the test (in days)

colsEng = ['Medical_unit','Patient','Date_Request','Turnaround']

CACU.columns = colsEng

#Make the date a date variable and replace NIS in medical unit

CACU.Date_Request = pd.to_datetime(CACU.Date_Request,format = '%Y-%m-%d')
CACU.Medical_unit = CACU.Medical_unit.str.replace('NIS','UMF')

#We need to get the last capture date per clinic in the dataset

CACU['Capture'] = CACU['Date_Request'] + pd.to_timedelta(CACU['Turnaround'], unit = 'd')

MaxCapture = CACU[['Medical_unit','Capture']].groupby('Medical_unit').max()
MaxCapture['Medical_unit'] = MaxCapture.index

#Now we need to get the relevant treatment dates per clinic in the dataset given 
#the treatment dates. So we can cut it by that:

TMTstats = pd.read_table('DATA/TMTstats.csv')

colsEng = ['index','Medical_unit','Treatment','TMTdate']
TMTstats.columns = colsEng
TMTstats.TMTdate = pd.to_datetime(TMTstats.TMTdate,format = '%Y-%m-%d')

TMTstats = pd.merge(TMTstats[['Medical_unit','Treatment','TMTdate']], 
                    MaxCapture, how='left')

TMTstats['MaxTurnaround'] = TMTstats['Capture']-(TMTstats['TMTdate']+pd.to_timedelta(30,unit = 'd'))

CACUcut = pd.merge(CACU,TMTstats[['Medical_unit','MaxTurnaround']],how='left')

#Fill the clinics that are not in the TMTstats database with the mean
CACUcut['MaxTurnaround']= CACUcut['MaxTurnaround'].fillna(TMTstats['MaxTurnaround'].mean())

CACUcut.Turnaround = pd.to_timedelta(CACUcut.Turnaround, unit = 'D')

CACUcut = CACUcut[CACUcut.Turnaround<=CACUcut.MaxTurnaround]

#Now only the clinics we want:
CACUcut = CACUcut[CACUcut.Medical_unit.isin(set(TMTstats.Medical_unit))]

## Now we need to see by patients, who got a test and how many times in order to
#construct patient histories. Missing values are all zeroes or all 8's, so let's
#get rid of them:
    
CACUcut = CACUcut[CACUcut.Patient.str.contains('8888888888|0000000000') == False]

#Now let's make a unique patient database with all the tests each patient got
# every column is a new test, with the date. 

CACUcut = CACUcut.sort_values(['Patient','Date_Request'],ascending=True,axis=0)

list = CACUcut.groupby('Patient').apply(lambda x: range(len(x))).tolist()
loop = [val for sublist in list for val in sublist]
CACUcut['obs']=loop


CACUwide = CACUcut[['Patient','Date_Request','obs']].pivot(index='Patient',
                 columns= 'obs', values='Date_Request')

colsEng = [str(x) for x in range(0,9)]
colsEng = ['Date.' + s for s in colsEng]

CACUwide.columns = colsEng

#Now let's determine elegibility for each one of the tests:
    
colsEng = [str(x) for x in range(0,9)]
colsEng = ['Elegible.' + s for s in colsEng]

CACUwide = pd.concat([CACUwide,pd.DataFrame(columns=colsEng)])

#The first one, since there is no previous one, is always needed
CACUwide['Elegible.0'] = 'HT'

CACUwide['B_Cper.0'] = CACUwide.iloc[:,0]
CACUwide['E_Cper.0'] = CACUwide.iloc[:,0]+pd.to_timedelta(365,unit ='D')


for i in range(0,8):
#first find the relevant columns for each date
    cols = CACUwide.columns.values.tolist()
    cols = [cols.index(s) for s in cols if str(i) in s]
#then, based on the period covered determine if that date was within covered period (HNT) or not (HT)
    CACUwide.iloc[:,cols[1]+1] = np.where(CACUwide.iloc[:,cols[0]+1]<=CACUwide.iloc[:,cols[3]],
    'HNT','HT')
    CACUwide.iloc[:,cols[1]+1] = np.where(pd.isnull(CACUwide.iloc[:,cols[0]+1])==True,
    CACUwide.iloc[:,cols[0]+1],CACUwide.iloc[:,cols[1]+1])
#then determine new covered period
#first, if test was done but not needed, just add 365 to E_Pc
    CACUwide.iloc[:,cols[3]]= np.where(CACUwide.iloc[:,cols[1]+1]=='HNT',
    CACUwide.iloc[:,cols[0]+1]+pd.to_timedelta(365,unit='D'),CACUwide.iloc[:,cols[3]])
#Then create new columns for Beginning and end of coverage period
    CACUwide['B_Cper.' + str(i+1)] = pd.to_datetime('nan')
    CACUwide['E_Cper.' + str(i+1)] = pd.to_datetime('nan')
#Then fill them with the date, and the date+365 if the patient got the test
#the beginning of the coverage period is always the date request
    CACUwide.iloc[:,cols[3]+1] = np.where(CACUwide.iloc[:,cols[1]+1]=='HT',
    CACUwide.iloc[:,cols[0]+1],CACUwide.iloc[:,cols[3]+1])
#the end is more complicated. there are three cases if she's had two in the past years:
    CACUwide.iloc[:,cols[3]+2] = np.where((CACUwide.iloc[:,cols[1]+1]=='HT') &
    (CACUwide.iloc[:,cols[0]+1]-CACUwide.iloc[:,cols[0]]<pd.to_timedelta(400,unit='D')),
    CACUwide.iloc[:,cols[0]+1]+pd.to_timedelta(1095,unit ='D'),CACUwide.iloc[:,cols[3]+1])
#if she hasn't she needs another one next year
    CACUwide.iloc[:,cols[3]+2] = np.where((CACUwide.iloc[:,cols[1]+1]=='HT') &
    (CACUwide.iloc[:,cols[0]+1]-CACUwide.iloc[:,cols[0]]>=pd.to_timedelta(400,unit='D')),
    CACUwide.iloc[:,cols[0]+1]+pd.to_timedelta(365,unit ='D'),CACUwide.iloc[:,cols[3]+1])
#and if she didn't need it she just gets +365
    CACUwide.iloc[:,cols[3]+2] = np.where(CACUwide.iloc[:,cols[1]+1]=='HNT',
    CACUwide.iloc[:,cols[0]+1]+pd.to_timedelta(365,unit ='D'),CACUwide.iloc[:,cols[3]+1])
#and then the ones we didn't categorize we just import the old coverage period
    CACUwide.iloc[:,cols[3]+1] = np.where((pd.isnull(CACUwide.iloc[:,cols[1]+1])==False) &
    (pd.isnull(CACUwide.iloc[:,cols[3]+1])==True),CACUwide.iloc[:,cols[2]],CACUwide.iloc[:,cols[3]+1])
    CACUwide.iloc[:,cols[3]+2] = np.where((pd.isnull(CACUwide.iloc[:,cols[1]+1])==False) &
    (pd.isnull(CACUwide.iloc[:,cols[3]+2])==True),CACUwide.iloc[:,cols[3]],CACUwide.iloc[:,cols[3]+2])









