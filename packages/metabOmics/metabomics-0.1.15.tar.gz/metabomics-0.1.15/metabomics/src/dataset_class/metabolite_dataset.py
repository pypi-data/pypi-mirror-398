# Dataset class for Metabolite Concentration data taken from https://www.metabolomicsworkbench.org/

from metabomics.utils.io_utils import load_json
from metabomics.utils.constants import DATASET_ROOT_PATH
from sklearn.model_selection import train_test_split
import pandas as pd
import numpy as np
import torch
from torch.utils.data import Dataset
import os
import random


class MetaboliteDataset(Dataset):
    CONTROL_MAP = load_json(os.path.join(DATASET_ROOT_PATH, 'control_mapp.json'))

    def __init__(self, file_path: str = None,
                 min_missing_th: float = None,
                 max_missing_th: float = None,
                 verbose=True, vae_multiplier=8) -> None:
        super(MetaboliteDataset, self).__init__()

        # Args
        self.file_path = file_path
        self.study_name = os.path.basename(self.file_path).split('/')[-1].replace('.csv', '')
        self.control_label = self.CONTROL_MAP[self.study_name]

        self.min_missing_th = min_missing_th
        self.max_missing_th = max_missing_th
        self.verbose = verbose
        self.vae_multiplier = vae_multiplier

        # Get device for tensor operations
        self.device = self.__get_device()

        # These part can change with the data
        self.data = None

        self.load_data()

        self.split_data_to_vae_and_cls()

        # TODO miss data olayini ayri ayri ds lere yapmak lazim gibi, bir de pandas ta yordu beni :D
        # self.__miss_some_data()

        # TODO belki bunu en son model asamasinda datayi alirken yapariz.
        # bu asamada problem oluyor numeric data kabul ediyor sadece
        # self.x_train = torch.tensor(self.x_train, device=self.device)

    def load_data(self):
        if self.file_path is None:
            raise ValueError(f"{self.file_path = }, please give a data directory to load.")

        # Read data with csv library
        self.data = pd.read_csv(self.file_path)
        self.data = self.data[:-1] # Last row is the average

        # Tabular data get n_instances, n_features and feature names
        self._feature_names = list(self.data.columns)
        self.n_instances = self.data.shape[0]
        self.n_features = self.data.shape[1] - 1

    def split_data_to_vae_and_cls(self):
        self.vae_data, self.cls_data = train_test_split(self.data, test_size=0.5, random_state=1)

    def prepare_vae(self):
        if 'Labels' in self.vae_data.columns:
            self.vae_data = self.vae_data.drop(['Labels'], axis=1)
        self.multiply_vae_data()
        self.create_vae_dataloader()

    def multiply_vae_data(self):
        if self.vae_multiplier is not None:
            ind = np.repeat(np.arange(len(self.vae_data)), self.vae_multiplier)  # 0,0,0,1,1,1
            self.vae_data = self.vae_data.iloc[ind].sample(frac=1)

    def __getitem__(self, index):
        return self.data[index]

    def __len__(self):
        return self.n_instances

    def __get_device(self):
        device = "cuda" if torch.cuda.is_available() else "cpu"
        if self.verbose:
            print(f"Tensors will be created on device {device}.")
        return device

    def __get_random_indicies(self, n_instances, n_features):
        """ Get random incides for cells in the tabular data.
        """
        if (self.min_missing_th is None) or (self.max_missing_th is None):
            raise ValueError(f"Incorrect threshold values.")

        min_size = int(n_instances * n_features * self.min_missing_th)
        max_size = int(n_instances * n_features * self.max_missing_th)
        size = random.randint(min_size, max_size)
        print('Size:', size)

        selected_columns = np.random.randint(n_features, size=size)
        selected_instances = np.random.randint(n_instances, size=size)

        return selected_instances, selected_columns

    def miss_some_data(self, data, seed=1, fill_value=0):
        """ Manipulate given data, change some of them to 0.
        """
        random.seed(seed)
        np.random.seed(seed)

        n_instances, n_features = data.shape
        selected_instances, selected_columns = self.__get_random_indicies(n_instances, n_features)

        if isinstance(data, pd.DataFrame):
            data = data.to_numpy()
            data[selected_instances, selected_columns] = fill_value

        return data

    def create_vae_dataloader(self):
        x = self.miss_some_data(self.vae_data)
        y = self.vae_data.to_numpy()

        x = torch.Tensor(x)
        y = torch.Tensor(y)
        dataset = torch.utils.data.TensorDataset(x, y)

        if self.vae_multiplier is not None:
            self.batch_size = self.vae_multiplier
        else:
            self.batch_size = len(self.vae_data)
        self.vae_dataloader = torch.utils.data.DataLoader(dataset, batch_size=self.batch_size, shuffle=True)

    @property
    def cls_x(self):
        x = self.cls_data.drop(['Labels'], axis=1)
        return x

    @property
    def cls_y(self):
        y = self.cls_data['Labels']
        return y
