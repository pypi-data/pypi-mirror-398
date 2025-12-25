import json
import os
import time
import cobra as cb
import cobra.test
import pandas as pd
from datetime import datetime
from pathlib import Path

from collections import OrderedDict
import requests

BASE_DIR = Path(__file__).resolve().parent.parent

# Network models are in: metabomics/datasets/network_models/
NETWORK_MODELS_PATH = BASE_DIR / "datasets" / "network_models"

# Naming files are in: metabomics/datasets/naming/
NAMING_DATA_PATH = BASE_DIR / "datasets" / "naming"


def load_network_model(model):
    '''
    Loads metabolic network models in metabolitics.

    :param str model: model name
    '''
    if type(model) == str:
        if model in ['ecoli', 'textbook', 'salmonella']:
            return cb.test.create_test_model(model)
        elif model == 'recon2':
            return cb.io.load_json_model(str(NETWORK_MODELS_PATH / 'recon2.json'))
        elif model == 'recon3D':
            return cb.io.load_json_model(str(NETWORK_MODELS_PATH / 'Recon3D.json'))
        elif model == 'recon301':
            return cb.io.load_matlab_model(str(NETWORK_MODELS_PATH / 'Recon3DModel_301.mat'))
    if type(model) == cb.Model:
        return model


def load_metabolite_mapping(naming_file='synonym', dataset = [], dataset_name=''):
    '''
    Loads metabolite name mapping from different databases to recon.

    :param str naming_file: names of databases
    valid options {'kegg', 'pubChem', 'cheBl', 'hmdb', 'toy', "synonym" "new-synonym"}

    Added synonym_enhancement feature from metabolitics-api-v2 along with datasets/naming/test.csv file to store the performance test result from the enhancement

    :param arr dataset: names of metabolites (x-component of skUtilsIO)
    :param str dataset_name: name of metabolite dataset (note: fill if performance test of the enhancement want to be conducted, otherwise dont)
    '''
    mapping_file_path = NAMING_DATA_PATH / f"{naming_file}-mapping.json"

    with open(mapping_file_path, 'r') as f:
            name_mapping = json.load(f, object_pairs_hook=OrderedDict)

    refmet_path = NAMING_DATA_PATH / 'refmet_recon3d.json'
    test_csv_path = NAMING_DATA_PATH / 'test.csv'

    if (naming_file == 'synonym' or naming_file == 'new-synonym') and (len(dataset) > 0):
        metabolites=[]
        for array in dataset:
            for metabolite in array.keys():
                if metabolite.lower() not in metabolites:
                    metabolites.append(metabolite.lower())

        start_time_1 = time.time()
        unmatched_metabolites = ""
        unmatched_metabolites_num = 0
        for metabolite in metabolites:
            if metabolite not in name_mapping.keys():
                unmatched_metabolites_num += 1
                unmatched_metabolites += metabolite +'\n'
        end_time_1 = time.time()

        # everything is matched, skip the RefMet API call.
        if unmatched_metabolites == "":
            return name_mapping

        print("Enhancing synonyms...")
        enhanced_matched_num = 0
        start_time_2 = time.time()
        try:
            with open(refmet_path) as f:
                    refmet_recon3d = json.load(f, object_pairs_hook=OrderedDict)
            params = {
                "metabolite_name": unmatched_metabolites
            }
            refmet_url = "https://www.metabolomicsworkbench.org/databases/refmet/name_to_refmet_new_min.php"
            res = requests.post(refmet_url, data=params).text.split('\n')
            res.pop(0)
            for line in res:
                if line == '':
                    continue
                line = line.split('\t')
                met = line[0]
                ref = line[1]
                if ref in refmet_recon3d.keys():
                    rec_id = refmet_recon3d[ref]
                    if met not in name_mapping.keys():
                        name_mapping.update({met : rec_id})
                        enhanced_matched_num += 1
        except Exception as e:
            print(e)
        with open(mapping_file_path, 'w') as f: 
            json.dump(name_mapping, f, indent=4) 
            end_time_2 = time.time()
        print("Enhancing synonyms done.")

        if dataset_name != '':
            local_matching_runtime = round(end_time_1 - start_time_1, 2)
            metabolites_num = len(metabolites)
            local_matched_num = metabolites_num - unmatched_metabolites_num
            local_matched_percentage = round(local_matched_num/metabolites_num * 100, 2)
            enhanced_matching_runtime = round(end_time_2 - start_time_2, 2)
            total_matching_runtime = local_matching_runtime + enhanced_matching_runtime
            enhanced_matched_percentage = round(enhanced_matched_num/unmatched_metabolites_num * 100, 2)
            enhanced_matched_percentage_all = round(enhanced_matched_num/metabolites_num * 100, 2)
            total_matched_num = enhanced_matched_num + local_matched_num
            new_matched_percentage = round(total_matched_num/metabolites_num * 100, 2)

            test = pd.read_csv(test_csv_path)
            new_data = pd.DataFrame({'Dataset Name' : dataset_name,
                                    'Number of Metabolite' : [metabolites_num],
                                    'Total Matched Metabolites' : [total_matched_num],
                                    'Locally Matched Metabolites' : [local_matched_num],
                                    'Matched Metabolites Through Enhancement' : [enhanced_matched_num],
                                    'Percentage of Total Matching' : [new_matched_percentage],
                                    'Percentage of Local Matching' : [local_matched_percentage],
                                    'Percentage of Enhanced Matching out of locally unmatched metabolites' : [enhanced_matched_percentage],
                                    'Percentage of Enhanced Matching out of all metabolites' : [enhanced_matched_percentage_all],
                                    'Total matching runtime' : [total_matching_runtime],
                                    'Local matching runtime' : [local_matching_runtime],
                                    'Enhanced matching runtime' : [enhanced_matching_runtime],
                                    'Test time' : [datetime.now().strftime("%Y-%m-%d %H:%M:%S")]
                                    }) 
            test = pd.concat([test, new_data], ignore_index=True)
            test.to_csv('%s/naming/test.csv' % DATASET_PATH, index=False)

    return name_mapping