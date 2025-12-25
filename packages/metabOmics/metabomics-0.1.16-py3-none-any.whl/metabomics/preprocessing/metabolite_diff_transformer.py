from sklearn.base import TransformerMixin


from ..utils import load_network_model


class MetaboliteDiffTransformer(TransformerMixin):
    """Scaler reaction by diff"""

    def __init__(self, network_model="recon3D"):
        self.model = load_network_model(network_model)

    def fit(self, X, y):
        return self

    def transform(self, X, y=None):
        return [self.metabolite_diff(x) for x in X]

    def metabolite_diff(self, x):
        person_dict = {}
        for r, r_diff in x.items():
            r_ = self.model.reactions.get_by_id(r)
            for m, sto in r_.metabolites.items():
                if sto > 0:
                    person_dict.setdefault(m.id, 0)
                    person_dict[m.id] += r_diff * sto
        return person_dict
