import pandas as pd
import requests
import re
import json

def is_icd9(icd_code):
     return False if icd_code in json.load(open('./icd10_description.json')) else True

def get_icd9(icd_code):
    return icd_code.replace('.','')

def get_icd10(icd_code):
    if icd_code[0].isupper():
        if len(icd_code) > 3:
            return (icd_code[:3] + '.' + icd_code[3:])
        else:
            return icd_code

def converter(icd_code):
    if is_icd9(icd_code):
        icd9 = get_icd9(icd_code)
        text = requests.get('http://www.icd10codesearch.com/scripts/icd9search.php?searchQuery={}&queryCodeType=icd9&longDesc=true'.format(icd9))
        ##print(text.text)
        s = text.text
        p = re.compile("[A-Z]{1}\d{2}[A-Z0-9]*")
        result = p.findall(s)
        if len(result) >= 1:
            icd10_raw = result[-1]
            return get_icd10(icd10_raw)
        else:
            print(icd_code)
            return('NULL')
    else:
        print("Input is not a ICD 9 code.")
        return('NULL')

def icd10_check_category(icd10):
    return icd10[:3]

def description(icd10):
    if icd10 in json.load(open('./icd10_description.json')):
        return json.load(open('./icd10_description.json'))[icd10]
    else:
        return "icd10code not in the json file"

def check_category_icd9(icd9):
    icd10 = converter(icd9)
    icd10_category = icd10_check_category(icd10)
    return description(icd10_category)
