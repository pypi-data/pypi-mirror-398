import torch
import os
import numpy as np

from sklearn.base import TransformerMixin
from sklearn.impute import SimpleImputer

from metabomics.src.imputer.vae_imputer_model import VAEImputerModel


class VAEImputer(TransformerMixin):

    def __init__(self, study_name) -> None:
        self.model = None

        self.load_model(study_name=study_name)

    def load_model(self, study_name):
        self.study_name = study_name
        self.model_name = VAEImputerModel.create_fname(self.study_name, epochs=100)
        self.model_path = os.path.join(VAEImputerModel.MODEL_PATH_NAME, self.model_name)

        model = torch.load(self.model_path)
        model.eval()
        self.model = model

    def fit(self, X, y):
        return self

    def transform(self, X):
        sklearn_imputer = SimpleImputer(strategy='constant', fill_value=0)
        nan_mask = np.isnan(X)
        X = sklearn_imputer.fit_transform(X)
        X_ = torch.Tensor(X)
        recon_outputs, mu, logvar = self.model(X_)
        recon_x = recon_outputs.detach().numpy()
        X[nan_mask] = recon_x[nan_mask]

        return X

    def fit_transform(self, X):
        return self.transform(X)
