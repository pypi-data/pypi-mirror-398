import torch
from torch import nn, optim
import torch.nn.functional as F


class EncoderVAE(torch.nn.Module):
    def __init__(self, n_features: int, n_intermediate: int):
        """
            Encoder module of the Gomari Metabolite Variational Autoencoder

            Keras LeakyReLU alpha: float = 0.3

            Args:
                n_features: Input feature size, metabolite names as columns, eg. 217 in TwinsUK
                n_intermediate: Intermediate dimension, eg. 200 in referance study
        """
        super(EncoderVAE, self).__init__()

        self.n_features = n_features
        self.n_intermediate = n_intermediate

        # Encoder module
        self.encoder = nn.Sequential(
            nn.Linear(in_features=self.n_features, out_features=self.n_intermediate),
            nn.LeakyReLU(negative_slope=0.3, inplace=True)
        )

    def forward(self, x):
        return self.encoder(x)


class DecoderVAE(torch.nn.Module):
    def __init__(self, n_features: int, n_intermediate: int, n_latent: int):
        """
            Decoder module of the Gomari Metabolite Variational Autoencoder

            Keras LeakyReLU alpha: float = 0.3

            Args:
                n_features: Input feature size, metabolite names as columns, eg. 217 in TwinsUK
                n_intermediate: Intermediate dimension, eg. 200 in referance study
                n_latent: Latent dimension to sample mu and sigma, eg. 18 in study
        """
        super(DecoderVAE, self).__init__()

        self.n_features = n_features
        self.n_intermediate = n_intermediate
        self.n_latent = n_latent

        # Decoder module
        self.decoder = nn.Sequential(
            nn.Linear(in_features=self.n_latent, out_features=self.n_intermediate),
            nn.LeakyReLU(negative_slope=0.3, inplace=True),

            nn.Linear(in_features=self.n_intermediate, out_features=self.n_features)
        )

    def forward(self, x):
        return self.decoder(x)


class GomariVAE(torch.nn.Module):
    def __init__(self, n_features: int, n_intermediate: int, n_latent: int):
        """
            Variational Autoencoder (VAE) Model proposed in paper with PyTorch by Sadi Çelik:

            Variational autoencoders learn universal latent representations of metabolomics data
            Daniel P. Gomari, Annalise Schweickart, Leandro Cerchietti, Elisabeth Paietta,
            Hugo Fernandez, Hassen Al-Amin, Karsten Suhre, Jan Krumsiek

            Args:
                n_features: Input feature size, metabolite names as columns, eg. 217 in TwinsUK
                n_intermediate: Intermediate dimension, eg. 200 in referance study
                n_latent: int = Latent dimension to sample mu and sigma, eg. 18 in study
        """
        super(GomariVAE, self).__init__()

        self.n_features = n_features
        self.n_intermediate = n_intermediate
        self.n_latent = n_latent

        # VAE consists of encoder, latent space and a decoder part
        # Encoder block
        self.encoder = EncoderVAE(self.n_features, self.n_intermediate)

        # Fully connected layers for logvar and mu
        self.latent_mu = nn.Linear(in_features=self.n_intermediate, out_features=self.n_latent)
        self.latent_sigma = nn.Linear(in_features=self.n_intermediate, out_features=self.n_latent)

        # Decoder block
        self.decoder = DecoderVAE(self.n_features, self.n_intermediate, self.n_latent)

        self.device = self.__get_device()
        self.to(device=self.device)

    @staticmethod
    def __get_device():
        device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"Training on {device}.")
        return device

    def forward(self, x):
        x = x.to(self.device)
        mu = None
        logvar = None

        # Encoder block
        x = self.encoder(x)
        # Latent space block
        x = self.fcn(x)

        # Update mu and logvar
        mu = self.latent_mu(x)
        logvar = self.latent_sigma(x)
        # Reparameterize
        x = self.reparameterize(mu=mu, logvar=logvar)

        # Decoder block
        x = self.decoder(x)

        return x, mu, logvar

    def reparameterize(self, mu, logvar):
        out = None

        std = torch.exp(0.5 * logvar)
        eps = torch.rand_like(std)
        out = torch.add(torch.multiply(eps, std), mu)

        return out

    def loss_function(self, recon_x, x, mu, logvar):
        recon_x = recon_x.to(self.device)
        x = x.to(self.device)
        mu = mu.to(self.device)
        logvar = logvar.to(self.device)

        # Initialize loss
        loss = None

        # Reconstruction loss
        reconstruction_loss = nn.MSELoss(reduction="sum")(recon_x, x)
        # KL divergence loss
        kl_loss = -0.5 * torch.sum(1 + logvar - torch.square(mu) - torch.exp(logvar))
        # Total loss = KL loss + reconstruction loss
        loss = kl_loss + reconstruction_loss

        return loss
