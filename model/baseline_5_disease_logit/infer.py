import pickle
import math
import re
import csv
import concurrent.futures
import os
from functools import reduce
import datetime
from operator import add
import pandas as pd
import numpy as np
from datetime import datetime
'''for implementing simple logisticregression'''
import sklearn
from sklearn.linear_model import LogisticRegressionCV
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
from sklearn.metrics import roc_curve,roc_auc_score,auc
from sklearn.model_selection import train_test_split
from sklearn.metrics import precision_recall_curve
from joblib import load


ROOT = "/"

class OmopParser(object):
    '''this structures the omop dataset and extracting information from the original dataset'''
    def __init__(self):
        self.name = 'omop_parser'

    def add_demographic_data(self,file_name):
        '''find the last visit date for all patients in the inference set'''
        visit = pd.read_csv('/infer/visit_occurrence.csv')
        person_last_visit = visit.sort_values(['person_id', 'visit_start_date'],ascending = False).groupby('person_id').head(1)
        person_last_visit = person_last_visit[['person_id', 'visit_start_date']]
        person_last_visit.columns = ["person_id", "last_visit_date"]
        print("infer set: person_last_visit")
        print(person_last_visit.head(10),flush = True)
        '''add demographic date'''
        person = pd.read_csv('/infer/person.csv')
        cols = ['person_id', 'gender_concept_id', 'year_of_birth', 'race_concept_id']
        person = person[cols]
        person = pd.merge(person_last_visit, person,on = ['person_id'], how = 'left')
        person['year_of_birth'] = pd.to_datetime(person['year_of_birth'], format = '%Y')
        person['last_visit_date'] = pd.to_datetime(person['last_visit_date'], format = '%Y-%m-%d')
        person['age'] = person['last_visit_date'] - person['year_of_birth']
        person['age'] = person['age'].apply(lambda x: x.days/365.25)
        person["count"] = 1
        race = person.pivot(index = "person_id", columns = "race_concept_id", values = "count")
        race.reset_index(inplace = True)
        race.fillna(0, inplace = True)
        '''
        race 8516 for "black and African American", 8515 for "Asian", 8527 for "White",
        8557 for "Native Hawaiian or other Pacific Islander", 8657 for "American Indian or Alaska Native"
        '''
        race = race[['person_id', 8516, 8515, 8527, 8557, 8657]]
        from sklearn.preprocessing import MinMaxScaler
        scaler = MinMaxScaler()
        scaled_column = scaler.fit_transform(person[['age']])
        person = pd.concat([person, pd.DataFrame(scaled_column,columns = ['scaled_age'])],axis = 1)
        gender = person.pivot(index = "person_id", columns = "gender_concept_id", values = "count")
        gender.reset_index(inplace = True)
        gender.fillna(0,inplace = True)
        '''8532 for gender female '''
        gender = gender[['person_id',8532]]
        person = person[['person_id','scaled_age']]
        person = person.merge(gender, how = "left", on = ['person_id'])
        person = person.merge(race, how = "left", on = ['person_id'])
        person.fillna(0, inplace = True)
        print("person.head(10)")
        print(person.head(10))
        person.to_csv( file_name[0:-4] + '_add_demographic_data.csv',index=False)
        print("list(person.columns.values)")
        print(list(person.columns.values))

    def add_cancer(self,file_name):
        cancer = pd.read_csv('/app/cancer_condition_id.csv')
        cancer['condition_concept_id'] = cancer['concept_id'].apply(pd.to_numeric,errors = 'ignore',downcast = 'signed')
        condition = pd.read_csv('/infer/condition_occurrence.csv')
        condition_cancer = pd.merge(cancer, condition, on = ['condition_concept_id'], how = 'inner')
        condition_cancer = condition_cancer.drop_duplicates(subset = ['person_id'], keep ='first')
        print("#patients with cancer{} ".format(condition_cancer.shape[0]))
        person_prediction_demographic = pd.read_csv(file_name)
        print("#patients total{} ".format(person_prediction_demographic.shape[0]))
        person_prediction_demographic['cancer'] = np.zeros(person_prediction_demographic.shape[0])
        person_prediction_demographic.loc[person_prediction_demographic.person_id.isin(condition_cancer.person_id),'cancer'] = 1
        person_prediction_demographic.to_csv(file_name[0:-4] + '_cancer.csv',index=False)


    def add_hd(self,file_name):
        hd = pd.read_csv('/app/HD_condition_id.csv')
        hd['condition_concept_id'] = hd['concept_id'].apply(pd.to_numeric,errors = 'ignore',downcast = 'signed')
        condition = pd.read_csv('/infer/condition_occurrence.csv')
        condition_hd = pd.merge(hd, condition, on = ['condition_concept_id'], how = 'inner')
        condition_hd = condition_hd.drop_duplicates(subset = ['person_id'], keep = 'first')
        print("#patients with hd {} ".format(condition_hd.shape[0]))
        person_prediction_demographic = pd.read_csv(file_name)
        person_prediction_demographic['HD'] = np.zeros(person_prediction_demographic.shape[0])
        person_prediction_demographic.loc[person_prediction_demographic.person_id.isin(condition_hd.person_id),'HD'] = 1
        person_prediction_demographic.to_csv(file_name[0:-4] + '_HD.csv',index=False)

    def add_copd(self,file_name):
        copd = pd.read_csv('/app/COPD_condition_id.csv')
        copd['condition_concept_id'] = copd['concept_id'].apply(pd.to_numeric, errors = 'ignore',downcast = 'signed')
        condition = pd.read_csv('/infer/condition_occurrence.csv')
        condition_copd = pd.merge(copd, condition, on = ['condition_concept_id'], how = 'inner')
        condition_copd = condition_copd.drop_duplicates(subset = ['person_id'], keep = 'first')
        print("#patients with copd {}".format(condition_copd.shape[0]))
        person_prediction_demographic = pd.read_csv(file_name)
        person_prediction_demographic['COPD'] = np.zeros(person_prediction_demographic.shape[0])
        person_prediction_demographic.loc[person_prediction_demographic.person_id.isin(condition_copd.person_id),'COPD'] = 1
        person_prediction_demographic.to_csv(file_name[0:-4] + '_COPD.csv',index = False)

    def add_t2dm(self,file_name):
        t2dm = pd.read_csv('/app/T2DM_condition_id.csv')
        t2dm['condition_concept_id'] = t2dm['concept_id'].apply(pd.to_numeric,errors = 'ignore',downcast = 'signed')
        condition = pd.read_csv('/infer/condition_occurrence.csv')
        condition_t2dm = pd.merge(t2dm, condition, on = ['condition_concept_id'], how = 'inner')
        condition_t2dm = condition_t2dm.drop_duplicates(subset = ['person_id'], keep = 'first')
        print("#patients with t2dm {}".format(condition_t2dm.shape[0]))
        person_prediction_demographic = pd.read_csv(file_name)
        person_prediction_demographic['T2DM'] = np.zeros(person_prediction_demographic.shape[0])
        person_prediction_demographic.loc[person_prediction_demographic.person_id.isin(condition_t2dm.person_id),'T2DM'] = 1
        person_prediction_demographic.to_csv(file_name[0:-4] + '_T2DM.csv',index = False)

    def add_stroke(self,file_name):
        stroke = pd.read_csv('/app/stroke_condition_id.csv')
        stroke['condition_concept_id'] = stroke['concept_id'].apply(pd.to_numeric, errors = 'ignore',downcast = 'signed')
        condition = pd.read_csv('/infer/condition_occurrence.csv')
        condition_stroke = stroke.merge(condition, on = ['condition_concept_id'], how = 'inner')
        condition_stroke = condition_stroke.drop_duplicates(subset = ['person_id'], keep = 'first')
        print(condition_stroke.iloc[:,1:5].head(20))
        print("#patients with stroke {} ".format(condition_stroke.shape[0]))
        person_prediction_demographic = pd.read_csv(file_name)
        person_prediction_demographic['stroke'] = np.zeros(person_prediction_demographic.shape[0])
        person_prediction_demographic.loc[person_prediction_demographic.person_id.isin(condition_stroke.person_id),'stroke'] = 1
        person_prediction_demographic.to_csv(file_name[0:-4] + '_stroke.csv',index = False)

    def inference(self,file_name):
        data = pd.read_csv(file_name)
        print(list(data.columns.values))
        X = data.drop(['person_id'], axis = 1).fillna(0)
        X = np.array(X)
        clf =  load('/model/baseline.joblib')
        Y_pred = clf.predict_proba(X)[:,1]
        person_id = data.person_id
        output = pd.DataFrame(Y_pred,columns = ['score'])
        #print(output.tail(10))
        output_prob = pd.concat([person_id,output],axis = 1)
        output_prob.to_csv('/output/predictions.csv')


if __name__ == '__main__':
    print("start infering", flush = True)
    FOLDER = 'scratch/'
    FILE_STR = 'infer_cleaned'
    op = OmopParser()
    print("add demographics", flush = True)
    op.add_demographic_data(ROOT + FOLDER + FILE_STR + '.csv')
    op.add_cancer(ROOT + FOLDER + FILE_STR + '_add_demographic_data.csv')
    op.add_hd(ROOT + FOLDER + FILE_STR + '_add_demographic_data_cancer.csv')
    op.add_copd(ROOT + FOLDER + FILE_STR + '_add_demographic_data_cancer_HD.csv')
    op.add_t2dm(ROOT + FOLDER + FILE_STR + '_add_demographic_data_cancer_HD_COPD.csv')
    op.add_stroke(ROOT + FOLDER + FILE_STR + '_add_demographic_data_cancer_HD_COPD_T2DM.csv')
    print("finish add 5 diseases", flush = True)
    op.inference(ROOT + FOLDER + FILE_STR + '_add_demographic_data_cancer_HD_COPD_T2DM_stroke.csv')
    print("finish infer",flush = True)
