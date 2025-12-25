import os
import json


from src.dataset_class.metabolite_dataset import MetaboliteDataset

from utils.constants import DATASET_ROOT_PATH, RESULT_ROOT_PATH, filtered_studies

from preprocessing.metabolitics_pipeline import MetaboliticsPipeline
from preprocessing.metabolitics_transformer import MetaboliticsTransformer
from preprocessing.reaction_diff_transformer import ReactionDiffTransformer

from src.imputer.vae_imputer import VAEImputer

from utils import load_metabolite_mapping
from sklearn_utils.preprocessing import FeatureRenaming, FoldChangeScaler

from sklearn.impute import SimpleImputer

from sklearn.pipeline import Pipeline
from sklearn.decomposition import PCA
from sklearn.feature_extraction import DictVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier


from sklearn.model_selection import cross_val_score, StratifiedKFold

import pandas as pd
import numpy as np


def fill_missed(X, missed_x, fill_by, study_name):
    if fill_by == 'zero':
        sklearn_imputer = SimpleImputer(strategy='constant', fill_value=0)
        filled_x = sklearn_imputer.fit_transform(missed_x)
    elif fill_by == 'avg':
        sklearn_imputer = SimpleImputer(strategy='mean')
        filled_x = sklearn_imputer.fit_transform(missed_x)
    elif fill_by == 'vae':
        # raise NotImplemented
        vae_imputer = VAEImputer(study_name=study_name)
        filled_x = vae_imputer.fit_transform(missed_x)
    else:
        raise NotImplemented
    print('Sum missing for filled:', np.isnan(filled_x).sum())
    return pd.DataFrame(filled_x, index=X.index, columns=X.columns)


def run_metabolics(fname, will_miss=False, fill_by=''):
    print('Starting:', fname)
    if not will_miss:
        fill_by = ''

    fpath = os.path.join(DATASET_ROOT_PATH, fname)
    metabolite_data = MetaboliteDataset(fpath, min_missing_th=0.8, max_missing_th=0.9, verbose=False)

    scores_file_name = f'{metabolite_data.study_name}_miss_{will_miss}_filled_{fill_by}_rf_100local.csv'
    print(scores_file_name)

    X = metabolite_data.cls_x
    y = metabolite_data.cls_y
    print('X shape:', X.shape)

    if will_miss:
        missed_x = metabolite_data.miss_some_data(X, seed=1923, fill_value=None)
        print('Sum missing:', np.isnan(missed_x).sum())
        X = fill_missed(X, missed_x, fill_by, metabolite_data.study_name)

    X = json.loads(X.to_json(orient="records"))
    y = list(y.values)
    # TODO burada missing olustur ve doldur.

    # MetaboliticsPipeline.steps['metabolite-name-mapping'] = FeatureRenaming(load_metabolite_mapping("synonym"))
    MetaboliticsPipeline.steps['spetial_feature_remaining'] = FeatureRenaming(load_metabolite_mapping())
    MetaboliticsPipeline.steps['spetial_MetaboliticsTransformer'] = MetaboliticsTransformer()
    MetaboliticsPipeline.steps['reaction-diff'] = ReactionDiffTransformer(reference_label=metabolite_data.control_label)

    transformer_pipe = MetaboliticsPipeline([
        'spetial_feature_remaining',
        'spetial_MetaboliticsTransformer'
    ])

    X_transformed = transformer_pipe.fit_transform(X=X, y=y)
    # print("OLDU BU IS")

    diff_score_pipe = MetaboliticsPipeline([
        'reaction-diff',
        # 'feature-selection',
        'pathway-transformer',
        'transport-pathway-elimination'
    ])

    X_breast_pathways = diff_score_pipe.fit_transform(X=X_transformed, y=y)

    print('Pathways are created.')

    ml_pipeline = Pipeline([
        ('vect', DictVectorizer(sparse=False)),
        # ('label_encoder', LabelEncoder())
        # ('pca', PCA()),
        ('clf', RandomForestClassifier())
    ])

    kf = StratifiedKFold(n_splits=5, shuffle=True, random_state=43)

    # scores = cross_val_score(ml_pipeline, X, y, cv=kf, n_jobs=None, scoring='f1_micro')
    scores = cross_val_score(ml_pipeline, X_breast_pathways, y, cv=kf, n_jobs=None, scoring='f1_micro')
    print(f'K-Fold test: {scores}')
    print(f'Mean: {scores.mean().round(3)}')
    print(f'Std: {scores.std().round(3)}')

    scores_file_path = os.path.join(RESULT_ROOT_PATH, scores_file_name)
    scores_df = pd.DataFrame(scores, columns=['scores'])
    scores_df.to_csv(scores_file_path)


for fname in filtered_studies:
    run_metabolics(fname, will_miss=False, fill_by='')
    run_metabolics(fname, will_miss=True, fill_by='zero')
    run_metabolics(fname, will_miss=True, fill_by='avg')
    run_metabolics(fname, will_miss=True, fill_by='vae')
# fname = filtered_studies[0]
# run_metabolics(fname, will_miss=True, fill_by='zero')
# run_metabolics(fname, will_miss=False, fill_by='')
    
