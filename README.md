# cse544_project
This repository describes how the ontology mapping from ICD-9 to ICD-10 is conducted.
## Ontology Mapping
### Mapping method 1
We scrapped an online mapping tools [crosswalk]((http://www.icd10codesearch.com/)) and converted ICD9 - 10 mapping by running condition_ranking.py and results with the rankings of mapped ICD-10 codes and ICD category were saved as mapped_condition_count.csv and hierarchy_condition_count.csv
```python
python condition_ranking.py
```
### Mapping method 2
Note: This code suppose you have have already downloaded the SynPUF data (https://drive.google.com/file/d/18EjMxyA6NsqBo9eed_Gab1ESHWPxJygz/view) and load them into a PostgreSQL database with OMOP v5.2 schema through the SQL script provided in OMOP CommonDataModel GitHub repository (https://github.com/OHDSI/CommonDataModel/archive/v5.2.2.zip).
```sql

```
We built a mapping dictionary from a csv spreadsheet provided by Lussier’s lab, where relationship between ICD-9 and ICD-10 were clustered into four categories, one-to-one, many-to-one, one-to-many and no relationship. Through prioritizing these four kinds of relationship(one-to-one > many-to-one > one-to-many > no relationship ), the method can return the optimal mapping result. Meanwhile, inside each searching step, we also applied a fuzzy mapping process if we did not find it in the dictionary with the exact code.
## drug-disease relationship validation
In order to get the drug-disease(type 1 diabetes) relationship, we queried condition table and selected visits that assigned at least one type 1 diabetes diagnosis code(under category E10)and we looked into the drug prescription associated with the same visit_occurrence_id, by doing so we got all the drug prescription for type1 diabetes and we ranked it by drug frequency.

Note: You need to prepare 2 separate csv files to do the drug-disease relationship validation
```python
import pandas as pd


integrate_type1d_count_table = uw_type2d_drug.merge(synpuf_type2d_drug, how='left', on='drug')
1 - integrate_type1d_count_table.synpuf_count.isna().sum() / 50

integrate_type1d_count_table.to_csv('integrate_1d_table.csv')
```
## Binomial test
Note: You need to prepare a integrate count table to do this test.
```python
from scipy import stats
import pandas as pd


number_of_synpuf_patients = 98514
p_list = list()
for i in range(10):
    p_value = stats.binom_test(integrate_count_table['disease_conut_in_synpuf_patients'][i],
                               n=number_of_synpuf_patients, 
                               p=integrate_count_table['disease_conut_in_real_patients'][i] / number_of_real_patients)
    p_list.append(p_value)

integrate_count_table['p-value'] = pd.Series(p_list)
integrate_count_table.to_csv('integrate_table.csv')
```
## Spearman Correlation test
Note: You need to prepare a integrate count table to do this test.
```python
from scipy import stats
import pandas as pd


stats.spearmanr(integrate_count_table['disease_conut_in_real_patients'], integrate_count_table['disease_conut_in_synpuf_patients'])
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
