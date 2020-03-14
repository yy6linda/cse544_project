# cse544_project
This repository describes how the ontology mapping from ICD-9 to ICD-10 is conducted.
## Ontology Mapping
### Mapping method 1
We scrapped an online mapping tools [crosswalk]((http://www.icd10codesearch.com/)) and converted ICD9 - 10 mapping by running condition_ranking.py and results with the rankings of mapped ICD-10 codes and ICD category were saved as mapped_condition_count.csv and hierarchy_condition_count.csv
```python
python condition_ranking.py
```
### Mapping method 2

[to do for Sicheng] put your code, and running order here; brief describe your methods in 2-3 lines
## drug-disease relationship validation
In order to get the drug-disease(type 1 diabetes) relationship, we queried condition table and selected visits that assigned at least one type 1 diabetes diagnosis code(under category E10)and we looked into the drug prescription associated with the same visit_occurrence_id, by doing so we got all the drug prescription for type1 diabetes and we ranked it by drug frequency

[to do for Sicheng] put your code and running order here
## Binomial test
[to do for Sicheng] put your code and running order here
## mortality prediction model
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
