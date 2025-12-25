import os

# VAEImputerModel globals
DATASET_ROOT_PATH = os.path.join('datasets', 'disease_datasets', 'mapped_metabolitics_workbench')
RESULT_ROOT_PATH = 'results'
filtered_studies = ['ST001118.csv',
                    'ST000356.csv',
                    'ST001400.csv',
                    'ST001736.csv',
                    'ST001516.csv',
                    'ST001420.csv',
                    'ST001735.csv',
                    'ST000974.csv',
                    'ST001517.csv',
                    'ST000975.csv',
                    'ST002000.csv',
                    'ST000355.csv']

# Disease data globals
RAW_WORKBENCH_PATH = os.path.join('datasets', 'disease_datasets', 'metabolomics_workbench', "raw")
PROBLEMATIC_STUDY_PATH = os.path.join('datasets', 'disease_datasets', 'metabolomics_workbench', "problematic_json")
UNMAPPED_WORKBENCH_PATH = os.path.join('datasets', 'disease_datasets', 'metabolomics_workbench', "unmapped")
MAPPED_WORKBENCH_PATH = os.path.join('datasets', 'disease_datasets', 'metabolomics_workbench', "mapped_new_synonym")