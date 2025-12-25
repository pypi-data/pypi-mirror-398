import os
import random

import numpy as np
import torch

# Model architectures
from metabomics.src.vae.vae_model import VAE
from metabomics.models.gomari_vae_pytorch import GomariVAE

# Dataset class
from metabomics.src.dataset_class.metabolite_dataset import MetaboliteDataset

# # Tuning libraries
import optuna

# Logging
import logging

# import ray
# from ray import tune
# from ray.air.config import RunConfig
# from ray.tune import CLIReporter
# from ray.tune.schedulers import ASHAScheduler

# # Ray Tune globals
# # Training parameters.
# EPOCHS = 50
# # For ASHA scheduler in Ray Tune.
# MAX_NUM_EPOCHS = 100
# GRACE_PERIOD = 1
# # For search run (Ray Tune settings).
# CPU = 1
# GPU = 1
# # Number of random search experiments to run.
# NUM_SAMPLES = 10



class VAEImputerModel:
    """
        Args:
            metabolite_data (MetaboliteDataset): Study csv file obtained from Metabolomics Workbench
            epochs (int): Number of times the data is optimized
            study_name (str): Name of the study file for naming
            mode (str): Tune or Train select one
            model_name (str): VAE model to select, options as Bio, Gomari
    """

    MODEL_PATH_NAME = 'models'
    LOGS_PATH_NAME = os.path.join(MODEL_PATH_NAME,"logs")

    def __init__(self,
                metabolite_data: MetaboliteDataset,
                epochs: int,
                study_name: str,
                mode: str,
                model_name: str,
                verbose: bool) -> None:
        
        self.metabolite_data = metabolite_data

        self.data = self.metabolite_data.vae_dataloader
        self.n_features = self.metabolite_data.n_features

        self.epochs = epochs
        self.study_name = study_name
        self.mode = mode
        self.model_name = model_name
        self.verbose = verbose

        if mode == "train":
            self.init()
        elif mode == "tune":
            self._init_tune_logs()

    def init(self):
        # Models
        if self.model_name == "bio":
            self.vae = VAE(n_features=self.n_features, n_latent=8)
        elif self.model_name == "gomari":
            self.vae = GomariVAE(n_features=217, n_intermediate=200, n_latent=18)

        # Optimizers
        # TODO: lr=1e-3
        self.vae_optimizer = torch.optim.Adam(self.vae.parameters(), lr=1e-3)

    def _train_vae(self, verbose: bool):
        """
            Args:
                self.vae (torch.nn.Module): The designed arcihtecture
                self.vae_optimizer: The self.vae_optimizer used in the architecture
                self.data: Train loader which implements mini-batches and shuffle
                self.epochs (int): The number of times the train set is iterated
                verbose (bool): Used for print statements
        """

        print(f"###################-STARTED TRAINING-###################")
        train_losses = []

        # Set model to train mode
        self.vae.train()
        # Training loop
        for epoch in range(self.epochs):
            # Record epoch loss as the average of the batch losses
            train_epoch_loss = 0

            # Iterate over mini batches
            for x_train_batch, y_train_batch in self.data:
                # Forwad Pass
                recon_outputs, mu, logvar = self.vae(x_train_batch)

                # Loss Calculation
                train_batch_loss = self.vae.loss_function(recon_outputs, y_train_batch, mu, logvar)

                # Backward Pass
                self.vae_optimizer.zero_grad()
                train_batch_loss.backward()

                # Parameter update
                self.vae_optimizer.step()

                # Update epoch loss
                train_epoch_loss += train_batch_loss.item()
            else:
                # One epoch of training complete, calculate average training epoch loss
                train_epoch_loss /= len(self.data)

                # Append epoch loss to main lists
                train_losses.append(train_epoch_loss)

                if verbose:
                    print(f"TRAIN:\tEpoch: {epoch:3d} | Loss: {train_epoch_loss:.5f}")

        print(f"###################-FINISHED TRAINING-###################")

        return self.vae, train_losses

    # def _tune_init(self):
    #     # Ray init for dashboard.log file
    #     ray.init(
    #         include_dashboard=False,
    #         _temp_dir="./outputs/dashboard_raytune_logs"
    #     ) 

    #     # Define the search space for the hyperparameters
    #     self.config = {
    #         "lr": tune.loguniform(1e-5, 1e-2)
    #     }

    #     # Schduler to stop bad performing trails.
    #     self.scheduler = ASHAScheduler(
    #         # metric="loss",
    #         # mode="min",
    #         max_t=MAX_NUM_EPOCHS,
    #         grace_period=GRACE_PERIOD,
    #         reduction_factor=2
    #     )

    # def _tune_vae(self):
    #     self._tune_init()

    #     # Implementation #2
    #     tuner = tune.Tuner(
    #         tune.with_resources(
    #             tune.with_parameters(self._tune_train_vae, n_features=self.n_features, data=self.data),
    #             resources={"cpu": CPU, "gpu": GPU}
    #         ),
    #         tune_config=tune.TuneConfig(
    #             metric="loss",
    #             mode="min",
    #             scheduler=self.scheduler,
    #             num_samples=NUM_SAMPLES, # random sample size = 10
    #         ),
    #         run_config=RunConfig(local_dir='./outputs/raytune_result'),
    #         param_space=self.config,
    #     )
    #     result = tuner.fit()

    #     # Extract the best trial run from the search.
    #     best_trial = result.get_best_trial(metric="loss", mode="min", scope="last")

    #     print(f"Best trial config: {best_trial.config}")
    #     print(f"Best trial final validation loss: {best_trial.last_result['loss']}")

    def train(self):
        self.vae, self.vae_train_losses = self._train_vae(verbose=self.verbose)

    # Optuna tune objective function
    def objective(self, trial):
        # Hyperparameter space to search from
        params = {
            "optimizer_name" : trial.suggest_categorical("optimizer", ["Adam", "SGD"]),
            "learning_rate": trial.suggest_float("learning_rate", 1e-6, 1e-3),
            "latent_dim": trial.suggest_int("latent_dim", 5, 50)
        }

        # Initialize
        self.vae = VAE(n_features=self.n_features, n_latent=params["latent_dim"])    
        self.vae_optimizer = getattr(torch.optim, params["optimizer_name"])(self.vae.parameters(), lr=params["learning_rate"])

        # Train
        self.train()

        model_loss = self.vae_train_losses[-1] # Last loss in the list, is final loss

        # Save every model with its trial.number
        self.save_vae(mode="tune", trial_number=trial.number, verbose=self.verbose)

        return model_loss

    def tune_vae(self, verbose: bool):
        """
            Hyperparameter tuning with Optuna

            Args:
                verbose (bool): Used for print statements
        """
        # Create a study object and optimize the objective function.
        study = optuna.create_study(
            direction='minimize',
            study_name=f'{self.study_name}-MetaboliteVAE-Hyperparameter-Tuning'
        )
        study.optimize(self.objective, n_trials=15)
        
        best_trial = study.best_trial

        if verbose:
            print(f"Number of finished trials: {len(study.trials)}")
            print("Best trial:")
            print(f"  Value: {best_trial.value}")
            print("  Params: ")
            for key, value in best_trial.params.items():
                print(f"    {key}: {value}")

        # Finish recording
        self._finish_tune_logs()

    def create_fname(self, study_name, epochs):
        if self.model_name == "Bio":
            return f'{study_name}_vae_imputer_model_E{epochs}.pt'
        elif self.model_name == "Gomari":
            return f'{study_name}_gomari_imputer_model_E{epochs}.pt'

    @staticmethod
    def create_tune_model_fname(study_name, trial_number):
        return f"{study_name}_vae_imputer_trial_{trial_number}.pt"

    @staticmethod
    def create_logfname(study_name):
        return f"{study_name}_vae_imputer_tune_results.log"

    def save_vae(self, mode: str, trial_number: int, verbose: bool):
        """Save the PyTorch model into .pt file."""
        if not os.path.exists(self.MODEL_PATH_NAME):
            os.mkdir(self.MODEL_PATH_NAME)

        if mode == "train":
            fname = self.create_fname(self.study_name, self.epochs)
            fpath = os.path.join(self.MODEL_PATH_NAME, fname)

        elif mode == "tune":
            # Store different trials in a single folder for each model, trial_0, trial_1 ...
            model_tune_fpath = os.path.join(self.MODEL_PATH_NAME, f"{self.study_name}_vae_imputer")
            if not os.path.exists(model_tune_fpath):
                os.mkdir(model_tune_fpath)

            fname = self.create_tune_model_fname(self.study_name, trial_number)
            fpath = os.path.join(model_tune_fpath, fname)

        torch.save(self.vae, fpath)

        if verbose:
            print(f"Model {fname} was saved.")

    def _init_tune_logs(self):
        """Save Optuna tuning logs into a log file."""
        if not os.path.exists(self.LOGS_PATH_NAME):
            os.mkdir(self.LOGS_PATH_NAME)

        # Logging
        logfname = self.create_logfname(self.study_name)
        logfpath = os.path.join(self.LOGS_PATH_NAME, logfname)

        # Create a logger and configure it to log to a file
        self.logger = optuna.logging.get_logger("optuna")
        self.file_handler = logging.FileHandler(logfpath)
        self.logger.addHandler(self.file_handler)

    def _finish_tune_logs(self):
        """Save Optuna tuning logs into a log file."""
        # Close the logger to ensure all logs are flushed to the file
        self.logger.removeHandler(self.file_handler)
        self.file_handler.close()
