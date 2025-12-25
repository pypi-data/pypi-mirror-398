from sklearn.pipeline import Pipeline
from sklearn.decomposition import PCA
from sklearn.linear_model import LogisticRegression
from sklearn.feature_extraction import DictVectorizer
from sklearn.model_selection import cross_val_score, StratifiedKFold
from sklearn.metrics import f1_score
from sklearn_utils.utils import SkUtilsIO
from sklearn_utils.preprocessing import FeatureRenaming
from sklearn_utils.utils import feature_importance_report
from sklearn_utils.visualization import plot_heatmap

from datetime import datetime

import numpy as np
import pandas as pd

from preprocessing import *
from preprocessing.metabolitics_pipeline import MetaboliticsPipeline
from utils.properties import get_file_path, create_out_dir, FLUX_TYPE, PREPROCESS_PIPELINE_TYPE
from utils import load_metabolite_mapping
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)
pd.set_option('display.float_format', '{:.2g}'.format)
print("global")

def log_state(state):
    print("LOG STATE", state, datetime.now())

def main():
    # TODO debug icin 2 normalde 5 olmali
    NUM_SPLITS = 5
    log_state("Starting")
    now = datetime.now()
    now_str = str(now).replace(":", "").replace(".", "").replace(" ", "").replace("-", "")
    print(now_str)
    
    out_dirname = create_out_dir(FLUX_TYPE, PREPROCESS_PIPELINE_TYPE, now_str)
    print(out_dirname)
    
    feature_importance_report_filename = get_file_path(out_dirname, "feature_importance.pickle")
    reaction_diff_filename = get_file_path(out_dirname, "reaction_diff.json")
    scores_file_name = get_file_path(out_dirname, "scores.csv")
    
    # feature_importance_report_filename = f'{out_dirname}/{FLUX_TYPE}_feature_importance_{now_str}.pickle'
    # reaction_diff_filename = f'{out_dirname}/{FLUX_TYPE}_reaction_diff_{now_str}.json'
    # scores_file_name = f'{out_dirname}/{FLUX_TYPE}_scores_{now_str}.csv'
    log_state("Load Data")
    X_breast, y_breast = SkUtilsIO("datasets/disease_datasets/Breast_Cancer_v3_2patient_2healthy.csv").from_csv(label_column='Factors')
    # X_breast, y_breast = SkUtilsIO("datasets/disease_datasets/Breast_Cancer_v3.csv").from_csv(label_column='Factors')
    
    log_state("Initialize steps")

    MetaboliticsPipeline.steps['metabolite-name-mapping'] = FeatureRenaming(load_metabolite_mapping("synonym"))

    diff_score_pipe = MetaboliticsPipeline([
        'metabolite-name-mapping',
        'fold-change-scaler',
        FLUX_TYPE,
        'reaction-diff',
        # 'feature-selection',
        'pathway-transformer',
        'transport-pathway-elimination'
    ])
    
    reaction_diff = MetaboliticsPipeline([
        'metabolite-name-mapping',
        'fold-change-scaler',
        FLUX_TYPE,
        'reaction-diff'
    ])
    
    PREPROCESES = {
        "reaction": reaction_diff,
        "pathway": diff_score_pipe
    }
    # X_breast_reaction_diff = reaction_diff.fit_transform(X=X_breast, y=y_breast)
    # SkUtilsIO(reaction_diff_filename).to_json(X_breast_reaction_diff, y_breast)
    
    log_state("Start Fit Transform Path ways")

    # X_breast_pathways = diff_score_pipe.fit_transform(X=X_breast, y=y_breast)
    # log_state("Done pathways")
    # print(X_breast_pathways)
    
    
    # df = feature_importance_report(X_breast_pathways, y_breast)
    # df.to_pickle(path=feature_importance_report_filename)

    # plot_heatmap(X_breast_pathways, y_breast)

    ml_pipeline = Pipeline([
        # ('preprocess', PREPROCESES[PREPROCESS_PIPELINE_TYPE]),
        ('vect', DictVectorizer(sparse=False)),
        ('pca', PCA()),
        ('clf', LogisticRegression(C=0.3e-6, random_state=43))
    ])

    kf = StratifiedKFold(n_splits=NUM_SPLITS, shuffle=True, random_state=43)
    log_state("Starting cross val score")
    scores = []
    X = np.array(X_breast)
    y = np.array(y_breast)
    cross_val_index = 0
    
    
    # for train_index, test_index in kf.split(X, y):
    #     X_train, X_test = X[train_index], X[test_index]
    #     y_train, y_test = y[train_index], y[test_index]
    if True:
        X_train, X_test = X, X
        y_train, y_test = y, y
        log_state("Starting preprocess fit")
        
        pre_model = PREPROCESES[PREPROCESS_PIPELINE_TYPE].fit(X_train, y_train)
        log_state("Done preprocess fit")
        
        X_train_tr = pre_model.transform(X_train)
        log_state("Done preprocess train transform")
        
        X_test_tr = pre_model.transform(X_test)
        log_state("Done preprocess test transform")
        
        preprocessed_file_path = get_file_path(out_dirname, f"{PREPROCESS_PIPELINE_TYPE}_{cross_val_index}.json")
        SkUtilsIO(preprocessed_file_path).to_json(X_train_tr, y_train)
        log_state(preprocessed_file_path)
        
        log_state("Starting ml_pipeline fit")
        ml_model = ml_pipeline.fit(X_train_tr, y_train)
        log_state("Done ml_pipeline fit")
        
        pred_y = ml_model.predict(X_test_tr)
        log_state("Done ml_pipeline predict")
        
        # print("y", y_test, pred_y)
        score = f1_score(y_true=list(y_test), y_pred=pred_y, average="micro")
        print(score)
        
        scores.append(score)
        log_state("DONE split")
        cross_val_index += 1
        
        # print("pred_y:", pred_y)
    log_state(scores)
    # scores = cross_val_score(ml_pipeline, X_breast, y_breast, cv=kf, n_jobs=None, scoring='f1_micro')
    log_state("End cross val score")
    scores = np.array(scores)
    log_state('K-Fold test: %s' % scores)
    log_state('Mean: %s' % scores.mean().round(3))
    log_state('Std: %s' % scores.std().round(3))
    scores_df = pd.DataFrame(scores, columns=['scores'])
    scores_df.to_csv(scores_file_name)
    log_state(scores_file_name)
    return scores_df


if __name__ == "__main__":
    log_state("main")
    main()
    log_state("Done")
