# cse544_project
This repository describes how the ontology mapping from ICD-9 to ICD-10 is conducted.
## Ontology Mapping
### Mapping method 1
We scrapped an online mapping tools [crosswalk](http://www.icd10codesearch.com/) and converted ICD9 - 10 mapping by running condition_ranking.py and results with the rankings of mapped ICD-10 codes and ICD category were saved as mapped_condition_count.csv and hierarchy_condition_count.csv
```python
python condition_ranking.py
```
### Mapping method 2
Note: This code suppose you have have already downloaded the [SynPUF data](https://drive.google.com/file/d/18EjMxyA6NsqBo9eed_Gab1ESHWPxJygz/view) and load them into a PostgreSQL database with OMOP v5.2 schema through the SQL script provided in [OMOP CommonDataModel GitHub repository](https://github.com/OHDSI/CommonDataModel/archive/v5.2.2.zip). Before run the icd9_icd10_mapper.sql file, you need to open it, go to the line 11 and ensure the path of icdconverter.csv is correct, or you will get an error. Besides, the ICD-9 code in icdconverter.csv are ICD-9 GEM, which means it does not contain the period symbol.
```sh
# Excecute the icd9_icd10_mapper.sql file to load the icdconverter.csv spreadsheet and build the mapping table for SynPUF data. 
# This will create a table called icd9_icd10_mapper, with column condition_source_concept_id(OMOP ID for that ICD-9 code), condition_source_value(ICD-9 code), icd10(corresponding ICD-10 code).
psql -h host -U username -d databasename -a -f icd9_icd10_mapper.sql
```
We built a mapping dictionary from a csv spreadsheet provided by Lussier’s lab, where relationship between ICD-9 and ICD-10 were clustered into four categories, one-to-one, many-to-one, one-to-many and no relationship. Through prioritizing these four kinds of relationship(one-to-one > many-to-one > one-to-many > no relationship ), the method can return the optimal mapping result. Meanwhile, inside each searching step, we also applied a fuzzy mapping process if we did not find it in the dictionary with the exact code.
## drug-disease relationship validation
In order to get the drug-disease(type 1 diabetes) relationship, we queried condition table and selected visits that assigned at least one type 1 diabetes diagnosis code(under category E10)and we looked into the drug prescription associated with the same visit_occurrence_id, by doing so we got all the drug prescription for type1 diabetes and we ranked it by drug frequency.

Note: You need to prepare two tables to do the drug-disease relationship validation. The first table should include the count of the patient grouped by the drug they were administered in the visit they were diagnosed with the disease we want to look up with using the real data, in the decsending order. The second table should include the count of the patient grouped by the drug they were administered in the visit they were diagnosed with the disease we want to look up with using the SynPUF data. 

```python
import pandas as pd

# We used type 1 diabetes as an example, suppose the real drug data is saved as real_type1d_drug, the SynPUF drug data is saved as synpuf_type1d_drug.
integrate_type1d_count_table = real_type1d_drug.merge(synpuf_type1d_drug, how='left', on='drug')
# We used the overlapping rate of the top 50 drug administered by that disease
overlapping_rate = 1 - integrate_type1d_count_table.synpuf_count.isna().sum() / 50
integrate_type1d_count_table.to_csv('integrate_type1d_table.csv')
```
## Binomial test and Spearman Correlation test
Note: You need to prepare an integrate count table to do this test. The table should include the count of the patient grouped by the disease they were diagnosed in the real data and the count of the patient grouped by the disease they were diagnosed in the SynPUF data, sorting in the descending order by the real data count column.
```python
from scipy import stats
import pandas as pd

# Binomial test
number_of_synpuf_patients = 98514
p_list = list()
# We used top 10 common disease occurred in the real data to do this test
for i in range(10):
    p_value = stats.binom_test(integrate_count_table['disease_conut_in_synpuf_patients'][i],
                               n=number_of_synpuf_patients, 
                               p=integrate_count_table['disease_conut_in_real_patients'][i] / number_of_real_patients)
    p_list.append(p_value)
integrate_count_table['p-value'] = pd.Series(p_list)
integrate_count_table.to_csv('integrate_table.csv')

# Spearman Correlation test
correlation_value, p_value = stats.spearmanr(integrate_count_table['disease_conut_in_real_patients'], 
                                             integrate_count_table['disease_conut_in_synpuf_patients'])
```
## Mortality prediction model
Here we provide dockerized machine learning models for mortality prediction, using three set of features:
1. demographic features;
2. demographic features + binary indicator for 5 chronic disease
3. the most common 1000 concept_ids


#### Download the data
[The Synpuf data are available here](https://www.synapse.org/#!Synapse:syn20685954). After downloading them, uncompress the archive and place the data folder where it can later be accessed by the dockerized model (see below).

#### Train the model on Synpuf data
Once the baseline model has been dockerized (see above), run the following command to train the model on Synpuf data:

```
docker run -v <path to train folder>:/train:ro
-v <path to scratch folder>:/scratch:rw
-v <path to model folder>:/model:rw  docker.synapse.org/syn12345/my_model:v0.1 bash /app/train.sh
```

where

- `<path to train folder>` is the absolute path to the training data (e.g. `/home/charlie/ehr_experiment/synpuf_data/train`).
- `<path to scratch folder>` is the absolute path to the scratch folder (e.g. `/home/charlie/ehr_experiment/scratch`).
- `<path to model folder>` is the absolute path to where the trained model will be exported (e.g. `/home/charlie/ehr_experiment/model`))

#### Predict the mortality status of patients

Run the following command to generate mortality status predictions for a group of XXX patients whose data are stored in the folder `synpuf/infer`.


```
docker run -v <path to infer folder>:/infer:ro
-v <path to scratch folder>:/scratch:rw
-v <path to output folder>:/output:rw
-v <path to model folder>:/model:rw
docker.synapse.org/syn12345/my_model:v0.1 bash /app/infer.sh
```

where

- `<path to infer folder>` is the absolute path to the inference data (e.g. `/home/charlie/ehr_experiment/synpuf_data/infer`).
- `<path to output folder>` is the absolute path to where the prediction file will be saved.

If the docker model runs successfully, the prediction file `predictions.csv` file will be created in the output folder. This file has two columns: 1) person_id and 2) 6-month mortality probability. Note: make sure the column 2) contains no NA and the values are between 0 and 1.
