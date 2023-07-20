import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.neighbors import KNeighborsClassifier


NAME = "Метод Главных Компонент"


pca = PCA(n_components=2)
knn = KNeighborsClassifier(n_neighbors=2)


def load(name, header_rows, skip_columns=None):
    data = pd.read_csv(name, delimiter='\t', header=None, skiprows=header_rows)
    target = data.iloc[:, 1]
    features = data.iloc[:, 2:]
    pca.fit(features)
    pca_features = pca.transform(features)
    knn.fit(pca_features, target)


def analyze(test_features):
    test_features = np.array(test_features)
    test_features = test_features.reshape(1, -1)
    test_pca_features = pca.transform(test_features)
    predicted = knn.predict(test_pca_features)
    return predicted[0]


def scale_values(array):
    array = [float(value) for value in array]
    min_value = min(array)
    max_value = max(array)
    scaled_array = [((value - min_value) / (max_value - min_value)) * 2 - 1 for value in array]
    return scaled_array
