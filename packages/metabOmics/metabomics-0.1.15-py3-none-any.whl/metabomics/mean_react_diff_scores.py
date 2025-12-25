import numpy as np
import pandas as pd
import os
import warnings
warnings.filterwarnings("ignore")
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier
from sklearn.svm import SVC
from sklearn.neural_network import MLPClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GridSearchCV
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction import DictVectorizer
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import f1_score

if __name__ == "__main__" :
    def read_diff_scores(directory, dataset_name):
        X_train_folds = []
        X_test_folds = []
        y_train_folds = []
        y_test_folds = []
        print(dataset_name + '_react_v0')
        for filename in os.listdir(directory):
            if filename.startswith(dataset_name + '_react_v0'):
                file_path = os.path.join(directory, filename)
                # print(file_path)
                with open(file_path, 'r') as file:
                    content = file.read()
                    pathways_diff_scores_train = eval(content.split("Train diff score:")[1].split("\n")[0].strip())
                    pathways_diff_scores_test = eval(content.split("Test diff score:")[1].split("\n")[0].strip())
                    y_train = eval(content.split("y_train:")[1].split("\n")[0].strip())
                    y_test = eval(content.split("y_test:")[1].split("\n")[0].strip())
                    label_mapping = {'healthy': 1, 'c': 0}
                    y_train = list(map(lambda x: label_mapping[x], y_train))
                    y_test = list(map(lambda x: label_mapping[x], y_test))
                X_train_folds.append(pathways_diff_scores_train)
                X_test_folds.append(pathways_diff_scores_test)
                y_train_folds.append(y_train)
                y_test_folds.append(y_test)
        return X_train_folds, X_test_folds, y_train_folds, y_test_folds


    def different_ML_models_f1scores(pathways_diff_scores_train, pathways_diff_scores_test, y_train_folds, y_test_folds,
                                     models, param_grids):
        count = 1
        train_f1_scores = {}
        test_f1_scores = {}
        for X_train, X_test, y_train, y_test in zip(pathways_diff_scores_train, pathways_diff_scores_test,
                                                    y_train_folds, y_test_folds):
            # print(f"\nFold {count} : ")
            for model_name, model in models.items():
                # print(f"Tuning {model_name}...")
                if count == 1:
                    train_f1_scores[model_name] = []
                    test_f1_scores[model_name] = []
                # Define pipeline for each model
                pipeline = Pipeline([
                    ('vect', DictVectorizer(sparse=False)),
                    ('pca', PCA()),
                    ('std', StandardScaler()),
                    ('clf', model)
                ])

                # Initialize GridSearchCV with F1 score as the metric
                grid_search = GridSearchCV(pipeline, param_grids[model_name], cv=5, scoring='f1')

                # Fit to data (replace X and y with your actual data)
                grid_search.fit(X_train, y_train)

                # Print best parameters and best F1 score
                # print(f"Best parameters for {model_name}: {grid_search.best_params_}")
                # print(f"Best F1 score for {model_name}: {grid_search.best_score_}\n")

                # Use the best estimator to make predictions on the test set
                best_model = grid_search.best_estimator_

                y_pred_train = best_model.predict(X_train)
                y_pred_test = best_model.predict(X_test)

                # Calculate and print F1 score on the test set
                train_f1 = f1_score(y_train, y_pred_train)
                test_f1 = f1_score(y_test, y_pred_test)

                train_f1_scores[model_name].append(train_f1)
                test_f1_scores[model_name].append(test_f1)
                # print(f"Train F1 score for {model_name}: {train_f1}\n")
                # print(f"Test F1 score for {model_name}: {test_f1}\n")
            count += 1
            # print("test_f1_scores : ", test_f1_scores)
        return train_f1_scores, test_f1_scores


    def mean_f1_scores(train_f1_scores, test_f1_scores):
        avg_train_f1_scores = {}
        avg_test_f1_scores = {}
        for key, val in train_f1_scores.items():
            avg_train_f1_scores[key] = np.mean(val)
            avg_test_f1_scores[key] = np.mean(test_f1_scores[key])
            # print(f"For {dataset_name}, average train f1 score for {key} : {avg_train_f1_scores[key]}")
            # print(f"For {dataset_name}, average test f1 score for {key} : {avg_test_f1_scores[key]}")
        return avg_train_f1_scores, avg_test_f1_scores

    def mean_react_diff_test_scores(directory, dataset_name, models, param_grids):
        react_diff_scores_train, react_diff_scores_test, y_train_folds, y_test_folds = read_diff_scores(directory,
                                                                                                        dataset_name)
        train_f1_scores, test_f1_scores = different_ML_models_f1scores(react_diff_scores_train, react_diff_scores_test,
                                                                       y_train_folds, y_test_folds, models, param_grids)
        mean_train_f1_scores, mean_test_f1_scores = mean_f1_scores(train_f1_scores, test_f1_scores)
        print(f"Mean Train F1-Scores for {dataset_name} : ")
        for model, score in mean_train_f1_scores.items():
            print(f"{model} : {score:.3f}")
        print(f"\nMean Test F1-Scores for {dataset_name} : ")
        for model, score in mean_test_f1_scores.items():
            print(f"{model} : {score:.3f}")
            # Write both train and test scores to a single file
        filename = f"{dataset_name}_mean_f1_scores.txt"
        with open(filename, 'w') as file:
            file.write(f"Mean F1-Scores for {dataset_name}\n")
            file.write("-" * 40 + "\n")

            file.write("Train F1-Scores:\n")
            for model, score in mean_train_f1_scores.items():
                file.write(f"{model}: {score:.3f}\n")

            file.write("\nTest F1-Scores:\n")
            for model, score in mean_test_f1_scores.items():
                file.write(f"{model}: {score:.3f}\n")

        print(f"\nAll scores have been saved to {filename}.")


    param_grids = {
        'logistic_regression': {
            'clf__C': [1e-13, 1e-11, 1e-10, 1e-8, 10]
        },
        'random_forest': {
            'clf__n_estimators': [50, 100, 200],
            'clf__max_depth': [None, 10, 20, 30]
            # 'clf__min_samples_split': [2, 5, 10]
        },
        'xgboost': {
            'clf__n_estimators': [20, 50, 100],
            'clf__learning_rate': [0.0001, 0.01, 0.1],
            'clf__max_depth': [2, 3, 6]
        },
        'svm': {
            'clf__C': [0.1, 1, 10, 100]
            # 'clf__kernel': ['linear', 'rbf']
        },
        'mlp': {
            'clf__hidden_layer_sizes': [(50,), (100,), (50, 50)],
            'clf__alpha': [0.0001, 0.001, 0.01]
            # 'clf__learning_rate': ['constant', 'adaptive']
        }
    }

    # Define the models for each pipeline
    models = {
        'logistic_regression': LogisticRegression(random_state=43),
        'random_forest': RandomForestClassifier(random_state=43),
        'xgboost': XGBClassifier(use_label_encoder=False, eval_metric='logloss', random_state=43),
        'svm': SVC(random_state=43),
        'mlp': MLPClassifier(max_iter=500, random_state=43)
    }

    directory = os.getcwd()
    cancer_name = ['breast','ccRCC3', 'ccRCC4', 'coad', 'pdac', 'prostat']
    for name in cancer_name:
        mean_react_diff_test_scores(directory, name, models, param_grids)