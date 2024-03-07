import numpy as np
from typing import Union

means_data = []
deviations = []
names = []

DEF_TYPE = np.float32


NAME = "Метод Расстояний"


def get_means(vec_like: list) -> np.ndarray:  # считает средние значения по столбцам
    arr = np.array(vec_like, dtype=DEF_TYPE)
    means = np.mean(arr, axis=0, )
    return means


def distance(a: np.ndarray, b: np.ndarray, r: float = 1,
             p: float = 4) -> float:  # расстояние между n-мерными точками. Евклидово
    return sum((a - b) ** p) ** r


def standard_deviation(full_vec: np.ndarray, mean: np.ndarray) -> np.ndarray:
    arr: np.ndarray = (full_vec - mean) ** 2
    return (arr.sum(axis=0) / arr.shape[0]) ** 0.5


def probabilities(
        signals: np.ndarray, _means_data: Union[np.ndarray, list], _deviations: Union[np.ndarray, list]
) -> np.ndarray:
    A = []

    for B in range(len(_means_data)):
        A.append(
            min(
                distance(signals, _means_data[B] - _deviations[B]),
                distance(signals, _means_data[B] + _deviations[B]),
                distance(signals, _means_data[B])
            )
        )

    return np.array(A, dtype=DEF_TYPE)


def toInt(s: str) -> int:
    return int(s)


def load(file_name, header_rows, skip_columns=None):
    global means_data
    global deviations

    means_data = []
    deviations = []
    names.clear()
    data_model = {}

    #  LOAD FILE
    with open(file_name, mode="r") as file:
        COLUMNS_DATA_LINE = 5

        lines = file.readlines()
        raw_data = [line.strip().split() for line in lines[header_rows + 1:]]
        skip_cols_file = lines[COLUMNS_DATA_LINE].strip()

    # if skip_cols_file == str([x - 2 for x in skip_columns]):
    #     skip_columns = []

    #  DELETE ROWS
    raw_data = np.array( raw_data,)
    for col in skip_columns:
        raw_data = np.delete( raw_data, col, 1 )
    raw_data = list(raw_data)

    for _, name, *signals in raw_data:
        signals = [toInt(s) for s in signals]
        if name in data_model.keys():
            data_model[name].append(signals)
        else:
            data_model[name] = [signals, ]
            names.append( name )

    #  LOAD MODELS
    for x in data_model.keys():
        means = get_means(data_model[x])
        deviation = standard_deviation(np.array(data_model[x], dtype=DEF_TYPE), means)
        means_data.append(means)
        deviations.append(deviation)

    means_data = np.array(means_data, dtype=DEF_TYPE)
    deviations = np.array(deviations, dtype=DEF_TYPE)


def analyze(test_features):
    test_features = np.array(test_features, dtype=DEF_TYPE)
    prob = probabilities(test_features, means_data, deviations)
    return names[ list(prob).index(prob.min()) ]
