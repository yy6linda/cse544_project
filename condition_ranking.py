import pandas as pd
import database_functions as dbf
import argparse
from datetime import datetime
import dateutil.relativedelta
import os
import icd9_10 as icdconverter


def get_cutoff_date():
    query = """
        SELECT MAX(death_datetime) as date
        FROM "OMOP"."death"
    """
    output = dbf.query(query)
    date = output["date"][0].date()
    cutoff = date - dateutil.relativedelta.relativedelta(months=6)
    return cutoff

def select_person():
    cutoff_date = get_cutoff_date().strftime("%Y-%m-%d")
    query = f"""
        SELECT *
        FROM "OMOP".person p
        WHERE
            p.person_id not in (
                SELECT p.person_id
                FROM
                    "OMOP".visit_occurrence v
                        RIGHT JOIN
                    "OMOP".person p
                        ON p.person_id = v.person_id
                GROUP BY p.person_id, CAST(CAST(p.year_of_birth AS varchar) + '-' + CAST(p.month_of_birth AS varchar) + '-' + CAST(p.day_of_birth AS varchar) AS DATETIME)
                HAVING MIN(visit_start_date) < CAST(CAST(p.year_of_birth AS varchar) + '-' + CAST(p.month_of_birth AS varchar) + '-' + CAST(p.day_of_birth AS varchar) AS DATETIME)
            ) AND
            p.person_id not in (
                SELECT d.person_id
                FROM
                    "OMOP".visit_occurrence v
                        RIGHT JOIN
                    "OMOP".death d
                        ON d.person_id = v.person_id
                GROUP BY d.person_id, d.death_date
                HAVING MAX(visit_start_date) > d.death_date
            ) AND
            p.person_id in (
                SELECT vis.person_id
                FROM "OMOP".visit_occurrence vis
                GROUP BY vis.person_id
                HAVING COUNT( DISTINCT vis.visit_occurrence_id) >= 3
            )
    """
    person = dbf.query(query)
    person.to_csv('./OMOP/person.csv')
    person_id = person['person_id'].to_list()
    #print(type(person_id))
    return person_id


def create_dataset(person_id):
    tables = [
        'condition_occurrence',
        'death',
        'drug_exposure',
        'measurement',
        'observation',
        'observation_period',
        'procedure_occurrence',
        'visit_occurrence'
    ]
    tables_dates = {
        'condition_occurrence': 'condition_start_date',
        'death': 'death_datetime',
        'drug_exposure': 'drug_exposure_start_date',
        'measurement': 'measurement_date',
        'observation': 'observation_date',
        'observation_period': 'observation_period_start_date',
        'visit_occurrence': 'visit_start_date',
        'procedure_occurrence': 'procedure_date',
    }
    cutoff_date = get_cutoff_date().strftime("%Y-%m-%d")
    sql_person_id = ', '.join(str(id) for id in person_id)
    for table in tables:
        query = f"""
            SELECT *
            FROM "OMOP".{table} tab
            WHERE
                tab.person_id in ({sql_person_id})
                AND
                tab.{tables_dates[table]} < '{cutoff_date}'

        """
        data = dbf.query(query)
        data.to_csv(f"./5p_omop/{table}_5.csv", index = False)


def query_condition_count():
    query = """
        SELECT condition_source_value,count(condition_source_value) AS count
        FROM "OMOP"."condition_occurrence"
        GROUP BY condition_source_value ORDER
        BY count(condition_source_value) DESC
    """
    condition_count = dbf.query(query)
    return condition_count

## converting individual code to icd10 code
def individual_check(item):
    if icdconverter.is_icd9(item):
        return icdconverter.converter(item)
    else:
        return item
## convert individual code to it's root level. e.g. 'E11'for 'E11.5'
def individual_category(item):
    if icdconverter.is_icd9(item):
        icd10 = icdconverter.converter(item)
        return icdconverter.icd10_check_category(icd10)
    else:
        return icdconverter.icd10_check_category(item)

def mapped_condition_count(condition_count):
    for index, row in condition_count.iterrows():
        condition_count["condition_source_value"][index] = icdconverter.description(individual_check(row[0]))
    #print(condition_count.head(10))
        print(index)
    condition_count = pd.DataFrame(condition_count.groupby("condition_source_value", sort = False)["count"].sum()).reset_index()
    condition_count.sort_values(by = 'count', ascending = False,inplace = True)
    condition_count.to_csv(f"./mapped_condition_count.csv", index = False)

def hierarchy_condition_count(condition_count):
    for index, row in condition_count.iterrows():
        condition_count["condition_source_value"][index] = icdconverter.description(individual_category(row[0]))
        print(index)
    print("descriptors all found")
    condition_count = pd.DataFrame(condition_count.groupby("condition_source_value", sort=False)["count"].sum()).reset_index()
    condition_count.sort_values(by='count', ascending=False,inplace = True)
    condition_count.to_csv(f"./hierarchy_condition_count.csv", index = False)

def count_icd9(condition_count):
    icd9_num = 0
    for index, row in condition_count.iterrows():
        if icdconverter.is_icd9(row[0]):
            icd9_num = icd9_num + 1
    return icd9_num

if __name__ == "__main__":
    print("started", flush = True)
    condition_count = query_condition_count()
    icd9_num = count_icd9(condition_count)
    print("number of icd9 codes is" + str(icd9_num))
    condition_count = query_condition_count()
    mapped_condition_count(condition_count)
    print("mapping part done", flush = True)

    #condition_count = query_condition_count()
    #hierarchy_condition_count(condition_count)
    #print(icdconverter.description('NULL'))
