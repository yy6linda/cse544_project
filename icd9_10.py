import pandas as pd
sys.path.append("./DxCodeHandler/")
from DxCodeHandler.ICD9 import ICD9
from DxCodeHandler.Converter import Converter

def convert_condition():
    condition = pd.read_csv('condition_occurrence.csv')
    icd9 = ICD9()
    con = Converter()
    for index, row in condition.iterrows():
        if icd9.isCode(condition["condition_source_value"][index]):
            condition["condition_source_value"][index] = con.convert_10_9(condition["condition_source_value"][index])
    print("descriptors all found, number of icd10 finally")
    print( condition.condition_source_value.nunique())
    condition.to_csv(f"./condition_occurrence_icd10.csv", index = False)
