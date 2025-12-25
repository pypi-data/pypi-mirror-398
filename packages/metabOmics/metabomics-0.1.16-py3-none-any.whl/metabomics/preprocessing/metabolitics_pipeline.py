from sklearn.feature_extraction import DictVectorizer
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.feature_selection import VarianceThreshold, SelectKBest
from sklearn.pipeline import Pipeline
from sklearn_utils.preprocessing import *

from .metabolitics_transformer import FluxTypes

from .metabolitics_transformer import FluxTypes

from . import *
from ..utils import load_metabolite_mapping
from .metabolite_diff_transformer import MetaboliteDiffTransformer


class MetaboliticsPipeline(DynamicPipeline):

    def __init__(self, selected_steps) -> None:
        super().__init__(selected_steps)

    def __init__(self, selected_steps) -> None:
        super().__init__(selected_steps)

    default_steps = [
        'metabolite-name-mapping',
        'standard-scaler',
        'metabolitics-transformer',
        'reaction-diff',
        'feature-selection',
        'pathway-transformer',
    ]

    steps = {
        'metabolite-name-mapping': FeatureRenaming(load_metabolite_mapping()),
        'imputer-mean': DictInput(SimpleImputer()),
        'standard-scaler': DictInput(StandardScaler()),
        'fold-change-scaler': FoldChangeScaler('healthy'),
        'metabolic-standard': StandardScalerByLabel('healthy'),
        'metabolitics-transformer': MetaboliticsTransformer(),
        'metabolitics-transformer-with-pfba': MetaboliticsTransformer(flux_type=FluxTypes.PFBA_TYPE),
        'metabolitics-transformer-with-geometric-fba': MetaboliticsTransformer(flux_type=FluxTypes.GEOMETRIC_FBA_TYPE),
        'metabolitics-transformer-with-moma': MetaboliticsTransformer(flux_type=FluxTypes.MOMA),
        'reaction-diff': ReactionDiffTransformer(),
        'metabolite_diff': MetaboliteDiffTransformer(),
        'feature-selection': Pipeline([
            ('vt', DictInput(VarianceThreshold(0.1), feature_selection=True)),
            ('skb', DictInput(SelectKBest(k=100), feature_selection=True))
        ]),
        'pathway-transformer': PathwayTransformer(),
        'transport-pathway-elimination': TransportPathwayElimination(),
        **{
            'naming-%s' % i: FeatureRenaming(load_metabolite_mapping(i))
            for i in {'kegg', 'pubChem', 'cheBl', 'hmdb', 'toy'}
        }
    }
