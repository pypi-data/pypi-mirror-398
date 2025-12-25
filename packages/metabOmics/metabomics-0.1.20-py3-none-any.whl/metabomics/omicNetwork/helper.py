import pandas as pd
import numpy as np
import json


def read_data():
    with open('Databases/universalGraph.json', 'r') as json_file:
        data_dict = json.load(json_file)
    return data_dict 

def save_path(data, file_name):
    data_json = json.dumps(data, indent=2)
    with open(file_name, 'w') as file:
        file.write(data_json)
        
def save_csv(data, file_name):
    data.to_csv(file_name, index=False)