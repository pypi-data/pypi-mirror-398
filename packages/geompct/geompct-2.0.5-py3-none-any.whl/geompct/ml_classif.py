import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from sklearn.neighbors import KNeighborsClassifier
from sklearn import svm
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
# from sklearn.metrics import accuracy_score, classification_report, confusion_matrix

def knn_classifier(X_train, y_train, X_test, y_test, n_neighbors=5):
    knn = KNeighborsClassifier(n_neighbors=2)
    knn.fit(X_train, y_train)
    test_points = X_test
    y_pred = knn.predict(test_points)
    return y_pred

def svm_classifier(X_train, y_train, X_test, y_test):
    svm_clf = svm.SVC(kernel='linear')
    svm_clf.fit(X_train, y_train)
    y_pred = svm_clf.predict(X_test)
    return y_pred

def gradient_boosting_classifier(X_train, y_train, X_test, y_test):
    gb_clf = GradientBoostingClassifier(n_estimators=100, learning_rate=1.0, max_depth=1, random_state=0)
    gb_clf.fit(X_train, y_train)
    y_pred = gb_clf.predict(X_test)
    return y_pred

def logistic_regression_classifier(X_train, y_train, X_test, y_test):
    pipe = Pipeline([
        ('scaler', StandardScaler()),
        ('logreg', LogisticRegression())
    ])
    pipe.fit(X_train, y_train)
    y_pred = pipe.predict(X_test)
    return y_pred

def random_forest_classifier(X_train, y_train, X_test, y_test):
    rf_clf = RandomForestClassifier(n_estimators=100, random_state=42)
    rf_clf.fit(X_train, y_train)
    y_pred = rf_clf.predict(X_test)
    return y_pred