import os

from src.imputer.vae_imputer_model import VAEImputerModel
from src.dataset_class.metabolite_dataset import MetaboliteDataset
from utils.constants import DATASET_ROOT_PATH, filtered_studies


def tune_vae_imputer_model(fname):
    print('Starting:', fname)
    fpath = os.path.join(DATASET_ROOT_PATH, fname)
    metabolite_data = MetaboliteDataset(fpath, 
                                        min_missing_th=0.8, 
                                        max_missing_th=0.9, 
                                        verbose=False)
    metabolite_data.prepare_vae()
    vae_imputer_model = VAEImputerModel(metabolite_data=metabolite_data,
                                        epochs=50,
                                        study_name=metabolite_data.study_name,
                                        mode="tune",
                                        model_name="bio",
                                        verbose=True)

    vae_imputer_model.tune_vae(verbose=True)

if __name__ == "__main__":
    # Run script
    for fname in filtered_studies:
        # tune_vae_imputer_model(filtered_studies[0])
        tune_vae_imputer_model(fname)
