import pandas as pd
import database_functions as dbf
import argparse
from datetime import datetime
import dateutil.relativedelta
import os
import icd9_10 as icdconverter
import requests


def get_t2_patient():
    query = f'''
        SELECT top 100 d.drug_concept_id, count(*) as count
        FROM "OMOP"."condition_occurrence" c left join "OMOP"."drug_exposure" d
        on c.visit_occurrence_id = d.visit_occurrence_id
        where c.condition_source_value like 'E11.[A-Z0-9]%'
        or c.condition_source_value in ('250','250.2','250.3','250.4','250.5','250.6','250.7','250.8','250.9','357.2','366.41','349.89','353.5','355.9'
        ,'357.2','362.01','362.02','362.04','362.03','362.05','362.06','362.07','443.81','523.8','536.3','713.5','716.8','785.6','250.22','250.32','250.42','250.52',
        '250.62','250.72','250.82','250.92')
        group by d.drug_concept_id
        order by count(*) desc
    '''
    output = dbf.query(query)
    d = dict(sorted(output.values.tolist()))
    drug_list_query = list(x for x in output.drug_concept_id)
    final = pd.DataFrame()
    for drug in drug_list_query:
        text = requests.get('http://athena.ohdsi.org/api/v1/concepts?pageSize=15&domain=Drug&page=1&query=' + str(drug))
        content = text.json()["content"]
        for i in content:
            if i['id'] == drug:
                #temp = pd.DataFrame([i['name'], d[i['id']]])
                temp = pd.DataFrame(data = {'drug': i['name'] , 'count': d[i['id']]}, index = [0])
                final = pd.concat([final,temp])
    final.to_csv('./t2_drug.csv', index = False)

def get_t1_patient():
    query = f'''
        SELECT top 100 d.drug_concept_id, count(*) as count
        FROM "OMOP"."condition_occurrence" c left join "OMOP"."drug_exposure" d
        on c.person_id = d.person_id
        where c.condition_source_value like 'E10.[A-Z0-9]%'
        or c.condition_source_value in ('250.01','250.03','250.13','250.23','250.11','250.31','250.33','250.41','250.42','250.43','250.51','250.61','250.71',
        '250.81','250.91','357.2','366.41','250.41','250.51','250.61','250.71','349.89','353.5','355.9','357.2','362.01','362.02','362.04','362.05',
        '362.06','362.07','443.81','523.8','536.3','713.5','716.8','785.4','250.53','250.63','250.73','250.83','250.93')
        group by d.drug_concept_id
        order by count(*) desc
    '''
    output2 = dbf.query(query)
    d = dict(sorted(output2.values.tolist()))
    drug_list_query = list(x for x in output2.drug_concept_id)
    final = pd.DataFrame()
    for drug in drug_list_query:
        text = requests.get('http://athena.ohdsi.org/api/v1/concepts?pageSize=15&domain=Drug&page=1&query=' + str(drug))
        content = text.json()["content"]
        for i in content:
            if i['id'] == drug:
                temp = pd.DataFrame(data = {'drug': [i['name']] , 'count': [d[i['id']]] }, index=[0])
                final = pd.concat([final,temp])
    final.to_csv('./t1_drug.csv', index = False)

    
get_t2_patient()
get_t1_patient()
