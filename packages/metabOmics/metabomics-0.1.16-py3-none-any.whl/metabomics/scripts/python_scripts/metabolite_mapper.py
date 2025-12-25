""" Python script that applies syonym-mapping-new.json to studies downloaded
    studies from Metabolitics Workbench
"""
import os
import pandas as pd

# Metabolitics pipeline step to use name mapping
from metabomics.preprocessing.metabolitics_pipeline import MetaboliticsPipeline

from metabomics.utils import load_metabolite_mapping
from metabomics.utils.constants import DATASET_ROOT_PATH

from sklearn_utils.preprocessing import FeatureRenaming
from sklearn_utils.utils import SkUtilsIO






def apply_mapping(x_data, y_data):
    """ Apply mapping to unmapped labelled Metabolitics Workbench .csv file
        and return mapped version of it in a .csv format.
    """
    # Choose mapping json
    MetaboliticsPipeline.steps['metabolite-name-mapping'] = FeatureRenaming(load_metabolite_mapping("new-synonym"))

    # Apply pipeline step
    transformer_pipe = MetaboliticsPipeline([
        "metabolite-name-mapping"
    ])

    X_transformed = transformer_pipe.fit_transform(X=x_data, y=y_data)

    

    return None



if __name__ == "__main__":
    X_study, y_study = SkUtilsIO("datasets/disease_datasets/Breast_Cancer_v3_2patient_2healthy.csv").from_csv(label_column='Factors')

    apply_mapping(X_study, y_study)


    print("Hello World")