import os

import torch

from metabomics.src.vae.vae_model import VAE


class VAEImputerModel:

    MODEL_PATH_NAME = 'models'

    def __init__(self, data, epochs) -> None:
        self.data = data
        self.n_feature = data.shape[1]

        self.epochs = epochs
        self.init()

    def init(self):
        self.vae = VAE(n_feature=self.n_feature)
        self.vae_optimizer = torch.optim.Adam(self.vae.parameters(), lr=1e-3)

    def _train_vae(self, verbose=True):
        """
        Args:
        self.vae (torch.nn.Module): The designed arcihtecture
        self.vae_optimizer: The self.vae_optimizer used in the architecture
        self.data: Train loader which implements mini-batches and shuffle
        self.epochs (int): The number of times the train set is iterated
        verbose (bool): Used for print statements
        """

        print(f"###################-STARTED TRAINING-###################")
        # Initialize empty loss list
        train_losses = []

        # Set to train mode
        self.vae.train()
        # Training loop
        for epoch in range(self.epochs):
            # Record epoch loss as the average of the batch losses
            train_epoch_loss = 0

            # Iterate over mini batches
            for x_train_batch, _ in self.data:
                # Forwad Pass
                recon_outputs, mu, logvar = self.vae(x_train_batch)

                # Loss Calculation
                train_batch_loss = self.vae.loss_function(recon_outputs, x_train_batch, mu, logvar)

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

                if verbose:  # Print statements
                    print(f"TRAIN:\tEpoch: {epoch:3d} | Loss: {train_epoch_loss:.5f}")

        print(f"###################-FINISHED TRAINING-###################")

        return self.vae, train_losses

    def train(self):
        self.vae, self.vae_train_losses = self._train_vae(verbose=True)

    def save_vae(self):
        if not os.path.exists(self.MODEL_PATH_NAME):
            os.mkdir(self.MODEL_PATH_NAME)

        fname = f'vae_imputer_model_E{self.epochs}.pt'
        fpath = os.path.join(self.MODEL_PATH_NAME, fname)
        torch.save(self.state_dict(), fpath)
