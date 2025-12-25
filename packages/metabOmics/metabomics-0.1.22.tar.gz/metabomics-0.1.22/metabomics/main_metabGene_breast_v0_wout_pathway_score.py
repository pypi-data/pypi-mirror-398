# Normal libraries
import numpy as np
import pandas as pd
from preprocessing import *
from preprocessing.metabolitics_pipeline import MetaboliticsPipeline
import json
from sklearn_utils.preprocessing import *
from utils import load_metabolite_mapping
# Sklearn libraries
from sklearn_utils.utils import SkUtilsIO, filter_by_label
from sklearn_utils.preprocessing import FeatureRenaming
from sklearn.pipeline import Pipeline
from sklearn.decomposition import PCA
from sklearn.feature_extraction import DictVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.preprocessing import MinMaxScaler, StandardScaler
from sklearn.svm import SVC
from sklearn_utils.visualization import plot_heatmap
from sklearn_utils.utils import feature_importance_report
from sklearn.model_selection import cross_val_score, StratifiedKFold, KFold, cross_validate
from sklearn.base import clone
from sklearn.utils import shuffle
from sklearn.metrics import accuracy_score
from sklearn.metrics import f1_score

if __name__ == "__main__":
    # Set options for what ?
    # pd.set_option('display.max_columns', None)
    # pd.set_option('display.max_rows', None)
    # pd.set_option('display.float_format', '{:.2g}'.format)

    # Read data
    X_breast, y_breast = SkUtilsIO("../omicNetwork/Databases/metabData_breast.csv").from_csv(label_column='Factors')
    X_tr, y_tr = SkUtilsIO("../omicNetwork/Databases/geneData_breast.csv").from_csv(label_column='Factors')

    name_mapping_transformer = FeatureRenaming(load_metabolite_mapping("new-synonym", X_breast, "Breast_Cancer" ))
    X_breast_mapped = name_mapping_transformer.fit_transform(X_breast, y_breast)
    print("Number of matched metabolite : ", len(X_breast_mapped[0]))

    metabolitics_transformer = MetaboliticsTransformer()

    diff_score_pipe = MetaboliticsPipeline([
        'reaction-diff',
        'feature-selection',
        'pathway-transformer',
        'transport-pathway-elimination'
    ])

    # Define cross-validation parameters
    n_splits = 20

    train_scores_res = []
    test_scores_res = []

    dosya_adi = "breast_pathways_v0.txt"
    count = 1

    with open(dosya_adi, 'w') as json_file:

        skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=43)

        # Iterate over the splits
        for train_index, test_index in skf.split(X_breast, y_breast):
            try :
                y_train, y_test = [y_breast[i] for i in train_index], [y_breast[i] for i in test_index]

                # Fold Change Scaling
                fold_change_scaler_metab = FoldChangeScaler('healthy')
                X_breast_train_scaled = fold_change_scaler_metab.fit_transform(X=[X_breast_mapped[i] for i in train_index], y=y_train)
                fold_change_scaler_gene = FoldChangeScaler('healthy')
                X_tr_scaled = fold_change_scaler_gene.fit_transform(X=[X_tr[i] for i in train_index], y=y_train)

                X_train_transformed = metabolitics_transformer.transform(
                    X=X_breast_train_scaled, X_tr=X_tr_scaled, y=y_train)

                X_train_diff = diff_score_pipe.fit_transform(X=X_train_transformed, y=y_train)


                ml_pipeline = Pipeline([
                    ('vect', DictVectorizer(sparse=False)),
                    ('pca', PCA()),
                    ('std', StandardScaler()),
                    ('clf', LogisticRegression(C=0.3e-11, random_state=43))
                ])
                ml_pipeline.fit(X_train_diff, y_train)
                y_train_pred = ml_pipeline.predict(X_train_diff)
                #json_file.write(f'y_train : {y_train}\n')
                #json_file.write(f'y_train_pred : {y_train_pred}\n')
                train_score = f1_score(y_train, y_train_pred, pos_label='healthy')
                train_scores_res.append(train_score)

                # Evaluate the pipeline on the test set
                X_breast_test_scaled = fold_change_scaler_metab.transform(X=[X_breast_mapped[i] for i in test_index])
                X_tr_test_scaled = fold_change_scaler_gene.transform(X=[X_tr[i] for i in test_index])
                X_test_transformed = metabolitics_transformer.transform(X=X_breast_test_scaled, X_tr=X_tr_test_scaled)
                X_test_diff = diff_score_pipe.transform(X=X_test_transformed)


                y_test_pred = ml_pipeline.predict(X_test_diff)
                #json_file.write(f'y_test : {y_test}\n')
                #json_file.write(f'y_test_pred : {y_test_pred}\n')
                test_score = f1_score(y_test, y_test_pred, pos_label='healthy')
                test_scores_res.append(test_score)
                if count == 1 :
                    json_file.write(f'X_train_diff = {X_train_diff}\n')
                    json_file.write(f'X_test_diff = {X_test_diff}\n')
                count += 1
            except Exception as e:
                json_file.write(f'Error occured : {str(e)}\n')
                break
    with open('scores_breast_v0.txt', 'w') as f:
        try:
            average_accuracy = np.mean(test_scores_res)
            std_dev_accuracy = np.std(test_scores_res)

            average_train_score = np.mean(train_scores_res)
            std_dev_train_score = np.std(train_scores_res)

            f.write(f'Test F1 Scores: {test_scores_res}\n')
            f.write(f'Train F1 Scores: {train_scores_res}\n')

            f.write(f'Average Test Score: {average_accuracy}\n')
            f.write(f'Standard Deviation of Test Score: {std_dev_accuracy}\n')

            f.write(f'Average Train Score: {average_train_score}\n')
            f.write(f'Standard Deviation of Train Score: {std_dev_train_score}\n')
        except Exception as e:
            f.write(f'Error occured : {str(e)}\n')
