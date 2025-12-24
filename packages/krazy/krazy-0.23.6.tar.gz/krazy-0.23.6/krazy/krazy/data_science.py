import pandas as pd
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.metrics import accuracy_score
# from autosklearn.classification import AutoSklearnClassifier
from sklearn import preprocessing
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.metrics import confusion_matrix
from sklearn.ensemble import GradientBoostingRegressor
import numpy as np


# def models_auto_ml_100(df, features:list, y_col:str, test_size=0.3, random_state=1)->list:
#     '''
#     @params:
#     df          - required  - dataframe
#     features    - required  - list of features
#     y_col       - required  - dependent variable as string
#     test_size   - optional  - default is 0.3
#     random_state- optional  - default is 1

#     Returns list of [model, [X_train, X_test, y_train, y_test], accuracy score]
#     '''

#     y = df[y_col].copy()
#     X = df[features]

#     X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size, random_state=random_state)

#     model = AutoSklearnClassifier(
#         time_left_for_this_task=6*60,
#         per_run_time_limit=40
#     )

#     model.fit(X_train, y_train)

#     y_hat = model.predict(X_test)
#     acc = accuracy_score(y_test, y_hat)

#     return [model, [X_train, X_test, y_train, y_test], acc]

def models_4std(df:pd.DataFrame, features:list, dep_var:list, selection=['gradientboostingregressor','logistic', 'svm', 'tree', 'knn'], test_size=0.2, random_state=11, cv=2):

    '''
    @params:
    df          - required  - dataframe
    features    - required  - list of features
    dep_var     - required  - dependent variable as list
    selection   - optional  - list of models to be applied
                  accepted options for selection: ['gradientboostingregressor','logistic', 'svm', 'tree', 'knn']
    test_size   - optional  - default is 0.2
    random_state- optional  - default is 1
    cv          - optional  - default is 2

    Returns results from all models as a list of lists.
    '''

    # data validations
    if len(df) < 15:
        return [None, 'Too less data to apply ML']

    # list of models acceptable
    models = ['logistic', 'svm', 'tree', 'knn']

    # placeholder for output
    results = []

    # standardize features
    X = df[features]
    transform = preprocessing.StandardScaler()
    X = transform.fit_transform(X)

    # get depedendent values
    y = df[dep_var].to_numpy()

    # train test split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size, random_state=random_state)


    #parameters

    # logistic regression
    params_logistic_reg ={'C':[0.01,0.1,1, 2],
                'penalty':['l2'],
                'solver':['lbfgs']}
                # l1 lasso l2 ridge

    # SVM / SVC
    params_svm = {'kernel':('linear', 'rbf','poly', 'sigmoid'),
                'C': np.logspace(-3, 3, 5),
                'gamma':np.logspace(-3, 3, 5)}

    # decisions tree classifier
    params_decision_tree = {'criterion': ['gini', 'entropy'],
        'splitter': ['best', 'random'],
        'max_depth': [2*n for n in range(1,10)],
        'max_features': ['auto', 'sqrt'],
        'min_samples_leaf': [1, 2, 4],
        'min_samples_split': [2, 5, 10]}

    # knn
    params_knn = {'n_neighbors': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
                'algorithm': ['auto', 'ball_tree', 'kd_tree', 'brute'],
                'p': [1,2]}

    # gradient boosting regressor
    params_gradientboostingregressor = {'learning_rate': [0.01,0.02,0.03,0.04],
                'subsample'    : [0.9, 0.5, 0.2, 0.1],
                'n_estimators' : [100,500,1000, 1500],
                'max_depth'    : [4,6,8,10]
                }

    # models

    for model in selection:

        if model == 'gradientboostingregressor':
            model = GradientBoostingRegressor()
            model_cv = GridSearchCV(model, params_gradientboostingregressor, cv=cv)
            model_cv.fit(X_train, y_train)
            yhat = model_cv.predict(X_test)
            confusion = confusion_matrix(y_test, yhat)
            results.append(['Gradient Boosting Regressor', f'Best Params:{model_cv.best_params_}',
                f'Best Score: {model_cv.best_score_}', f'Score:{model_cv.score(X_test, y_test)}', [model_cv, [X_train, X_test, y_train, y_test], confusion]])

        if model == 'logistic':
            model = LogisticRegression()
            model_cv = GridSearchCV(model, params_logistic_reg, cv=cv)
            model_cv.fit(X_train, y_train)
            yhat = model_cv.predict(X_test)
            confusion = confusion_matrix(y_test, yhat)
            results.append(['Logistic Regression', f'Best Params:{model_cv.best_params_}',
                f'Best Score: {model_cv.best_score_}', f'Score:{model_cv.score(X_test, y_test)}', [model_cv, [X_train, X_test, y_train, y_test], confusion]])
    
        if model == 'svm':
            model = SVC()
            model_cv = GridSearchCV(model, params_svm, cv=cv)
            model_cv.fit(X_train, y_train)
            yhat = model_cv.predict(X_test)
            confusion = confusion_matrix(y_test, yhat)
            results.append(['SVM/SVC', f'Best Params:{model_cv.best_params_}',
                f'Best Score: {model_cv.best_score_}', f'Score:{model_cv.score(X_test, y_test)}', [model_cv, [X_train, X_test, y_train, y_test], confusion]])

        if model == 'tree':
            model = DecisionTreeClassifier()
            model_cv = GridSearchCV(model, params_decision_tree, cv=cv)
            model_cv.fit(X_train, y_train)
            yhat = model_cv.predict(X_test)
            confusion = confusion_matrix(y_test, yhat)
            results.append(['Tree', f'Best Params:{model_cv.best_params_}',
                f'Best Score: {model_cv.best_score_}', f'Score:{model_cv.score(X_test, y_test)}', [model_cv, [X_train, X_test, y_train, y_test], confusion]])

        if model == 'knn':
            model = KNeighborsClassifier()
            model_cv = GridSearchCV(model, params_knn, cv=cv)
            model_cv.fit(X_train, y_train)
            yhat = model_cv.predict(X_test)
            confusion = confusion_matrix(y_test, yhat)
            results.append(['KNN', f'Best Params:{model_cv.best_params_}',
                f'Best Score: {model_cv.best_score_}', f'Score:{model_cv.score(X_test, y_test)}', [model_cv, [X_train, X_test, y_train, y_test], confusion]])

    return results
