import torch
from torch import nn


class EncoderVAE(torch.nn.Module):
    ENC_HIDDEN_1 = 2**7
    ENC_HIDDEN_2 = int(ENC_HIDDEN_1 / 2)
    ENC_HIDDEN_3 = int(ENC_HIDDEN_2 / 2)
    ENC_HIDDEN_4 = int(ENC_HIDDEN_3 / 2)

    def __init__(self, in_features):
        """
            Encoder module of the Metabolite Variational Autoencoder

            Args:
                in_features (int): Initial feature size of the specific study, columns
        """
        super(EncoderVAE, self).__init__()

        self.in_features = in_features

        # Encoder module
        self.encoder = nn.Sequential(
            nn.Linear(in_features=self.in_features, out_features=self.ENC_HIDDEN_1),
            nn.LeakyReLU(negative_slope=0.2, inplace=True),

            nn.Linear(in_features=self.ENC_HIDDEN_1, out_features=self.ENC_HIDDEN_2),
            nn.LeakyReLU(negative_slope=0.2, inplace=True),

            nn.Linear(in_features=self.ENC_HIDDEN_2, out_features=self.ENC_HIDDEN_3),
            nn.LeakyReLU(negative_slope=0.2, inplace=True),

            nn.Linear(in_features=self.ENC_HIDDEN_3, out_features=self.ENC_HIDDEN_4),
            nn.LeakyReLU(negative_slope=0.2, inplace=True)
        )

    def forward(self, x):
        return self.encoder(x)


class DecoderVAE(torch.nn.Module):
    DEC_HIDDEN_1 = EncoderVAE.ENC_HIDDEN_4
    DEC_HIDDEN_2 = EncoderVAE.ENC_HIDDEN_3
    DEC_HIDDEN_3 = EncoderVAE.ENC_HIDDEN_2
    DEC_HIDDEN_4 = EncoderVAE.ENC_HIDDEN_1

    def __init__(self, in_features: int, out_features: int):
        """
            Decoder module of the Metabolite Variational Autoencoder

            Args:
                in_features (int): Input size, equals to the latent dimension size
                out_features (int): Initial feature size of the specific study, columns
        """
        super(DecoderVAE, self).__init__()

        self.in_features = in_features
        self.out_features = out_features

        # Decoder module
        self.decoder = nn.Sequential(
            nn.Linear(in_features=in_features, out_features=self.DEC_HIDDEN_1),
            # TODO: nn.BatchNorm1d(num_features=self.DEC_HIDDEN_1),
            nn.LeakyReLU(negative_slope=0.2, inplace=True),

            nn.Linear(in_features=self.DEC_HIDDEN_1, out_features=self.DEC_HIDDEN_2),
            nn.LeakyReLU(negative_slope=0.2, inplace=True),

            nn.Linear(in_features=self.DEC_HIDDEN_2, out_features=self.DEC_HIDDEN_3),
            nn.LeakyReLU(negative_slope=0.2, inplace=True),

            nn.Linear(in_features=self.DEC_HIDDEN_3, out_features=self.DEC_HIDDEN_4),
            nn.LeakyReLU(negative_slope=0.2, inplace=True),

            nn.Linear(in_features=self.DEC_HIDDEN_4, out_features=self.out_features),
        )

    def forward(self, x):
        return self.decoder(x)


class VAE(torch.nn.Module):
    def __init__(self, n_features: int, n_latent: int):
        """
            Fully connected Metabolite Variational Autoencoder

            Args:
                n_features (int): Initial feature size of the specific study, columns
                n_latent (int): Latent dimension to sample mu and sigma
        """
        super(VAE, self).__init__()

        self.n_features = n_features
        self.n_latent = n_latent

        # VAE consists of encoder, latent space and a decoder part
        # Encoder block
        self.encoder = EncoderVAE(in_features=self.n_features)

        # # Fully-connected block
        # self.fcn = nn.Sequential(
        #     nn.Linear(in_features=EncoderVAE.ENC_HIDDEN_4, out_features=self.n_latent),
        #     nn.LeakyReLU(negative_slope=0.2, inplace=True)
        # )

        # Fully connected layers for logvar and mu
        self.latent_mu = nn.Linear(in_features=EncoderVAE.ENC_HIDDEN_4, out_features=self.n_latent)
        self.latent_sigma = nn.Linear(in_features=EncoderVAE.ENC_HIDDEN_4, out_features=self.n_latent)

        # Decoder block
        self.decoder = DecoderVAE(in_features=self.n_latent, out_features=self.n_features)

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
        # x = self.fcn(x)
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

        loss = None

        # Reconstruction loss
        reconstruction_loss = nn.MSELoss(reduction="mean")(recon_x, x)
        # KL divergence loss
        kl_loss = -0.5 * torch.sum(1 + logvar - torch.square(mu) - torch.exp(logvar))
        # Total loss = KL loss + reconstruction loss
        loss = kl_loss + reconstruction_loss

        return loss
