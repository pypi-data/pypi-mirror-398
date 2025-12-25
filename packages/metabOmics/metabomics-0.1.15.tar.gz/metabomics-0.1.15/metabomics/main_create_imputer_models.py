import os

from src.imputer.vae_imputer_model import VAEImputerModel
from src.dataset_class.metabolite_dataset import MetaboliteDataset
from utils.constants import DATASET_ROOT_PATH, filtered_studies


def run_vae_imputer_model(fname):
    print('Starting:', fname)
    fpath = os.path.join(DATASET_ROOT_PATH, fname)
    metabolite_data = MetaboliteDataset(fpath,
                                        min_missing_th=0.8,
                                        max_missing_th=0.9,
                                        verbose=False)
    metabolite_data.prepare_vae()
    vae_imputer_model = VAEImputerModel(metabolite_data=metabolite_data,
                                        epochs=100,
                                        study_name=metabolite_data.study_name,
                                        mode="Train",
                                        model_name="Bio"
                                        )

    vae_imputer_model.train()
    vae_imputer_model.save_vae()


for fname in filtered_studies:
    run_vae_imputer_model(fname)
