from joblib import Parallel, delayed
from sklearn.base import TransformerMixin
from sklearn_utils.utils import SkUtilsIO, filter_by_label
from ..analysis import MetaboliticsAnalysis
from sklearn_utils.preprocessing import FoldChangeScaler
import pandas as pd

class FluxTypes:
    FVA_TYPE = 'fva'
    PFBA_TYPE = 'pfba'
    GEOMETRIC_FBA_TYPE = "geometric_fba"
    MOMA = "moma"


class MetaboliticsTransformer(TransformerMixin):
    """Performs metabolitics analysis and 
    convert metabolitic value into reaction min-max values."""

    def __init__(self, X_tr=None, network_model='recon3D', drug='', reaction='', target='', flux_type: str = 'fva'):
        '''
        :param network_model: cobra.Model or name of the model.
        :param n_jobs: the maximum number of concurrently running jobs.
        :param flux_type: distance calculation method, can be ['fva', 'pfba']
            if it is None then default value (fva) will be set.
        '''
        self.set_flux_type(flux_type=flux_type)
        self.analyzer = MetaboliticsAnalysis(model=network_model, drug=drug, reaction=reaction, target=target)
        self.X_tr = X_tr

    def set_flux_type(self, flux_type):
        if flux_type is None:
            self.flux_type = FluxTypes.FVA_TYPE
        self.flux_type = flux_type

    def fit(self, X, y=None):
        return self

    def transform(self, X, y=None):
        '''
        :param X: list of dict which contains metabolic measurements.
        '''
        '''genomic = pd.read_csv('../omicNetwork/Databases/geneData.csv')
        # Fold Change
        column_means = genomic[genomic['Factors'] == 'healthy'].iloc[:, 1:].astype(float).mean(numeric_only=True)
        norm_genomic = genomic.iloc[:, 1:].astype(float).subtract(column_means)
        norm_genomic['Factors'] = genomic['Factors']
        file_path = '../omicNetwork/Databases/norm_geneData.csv'
        norm_genomic.to_csv(file_path, index=False)
        
        X_tr, y_tr = SkUtilsIO('../omicNetwork/Databases/norm_geneData.csv').from_csv(label_column='Factors')'''
        #X_tr, y_tr = SkUtilsIO('../omicNetwork/Databases/geneData_pdac.csv').from_csv(label_column='Factors')
        #fold_change_scaler = FoldChangeScaler('healthy')
        #X_tr_scaled = fold_change_scaler.fit_transform(X_tr, y_tr)
        #X_tr_selected = [X_tr_scaled[i] for i in index]
        #print("y_tr_train : ", [y_tr[i] for i in index])
        return Parallel(n_jobs=-1)(delayed(self._transform)(x, x_tr)
                                   for x, x_tr in zip(X, self.X_tr))

    #def fit_transform(self, X, X_tr, y=None):
    #    return self.transform(X, X_tr, y)
    def __fva_transform(self, x, x_tr):
        x_t = dict()
        analyzer = self.analyzer.copy()

        for r in analyzer.variability_analysis(x, x_tr).itertuples():
            x_t['%s_max' % r.Index] = r.maximum
            x_t['%s_min' % r.Index] = r.minimum

        return x_t

    def __pfba_transform(self, x):
        x_t = dict()
        analyzer = self.analyzer.copy()

        for reaction, flux in analyzer.pfba_analysis(x).iteritems():
            x_t['%s_flux' % reaction] = flux

        return x_t

    def __geometric_fba_transform(self, x):
        x_t = dict()
        analyzer = self.analyzer.copy()

        for reaction, flux in analyzer.geometric_fba_analysis(x).iteritems():
            x_t['%s_flux' % reaction] = flux

        return x_t

    def __moma_transform(self, x):
        x_t = dict()
        analyzer = self.analyzer.copy()

        for reaction, flux in analyzer.moma_analysis(x).iteritems():
            x_t['%s_flux' % reaction] = flux

        return x_t

    def _transform(self, x, x_tr):
        # TODO_BC bunu dict kullanarak otomatik hale getirebiliriz belki.
        if self.flux_type == FluxTypes.FVA_TYPE:
            x_t = self.__fva_transform(x, x_tr)
        elif self.flux_type == FluxTypes.PFBA_TYPE:
            x_t = self.__pfba_transform(x)
        elif self.flux_type == FluxTypes.GEOMETRIC_FBA_TYPE:
            x_t = self.__geometric_fba_transform(x)
        elif self.flux_type == FluxTypes.MOMA:
            x_t = self.__moma_transform(x)

        return x_t
