import numpy as np

means_data = []
air_means = []
names = []
sensors_data = []


DEF_TYPE = np.float32
NAME = "Метод Расстояний"
FILTER_PERCENT = 0.05
FILTER_AMOUNT = 10


def distance(a: np.ndarray, b: np.ndarray, r: float = 1,
             p: float = 4) -> float:  # расстояние между n-мерными точками. Евклидово
    return sum((a - b) ** p) ** r


def get_means(vec_like: list) -> np.ndarray:  # считает средние значения по столбцам
    arr = np.array(vec_like, dtype=DEF_TYPE)
    means = np.mean(arr, axis=0, )
    return means


def toInt(s: str) -> int:
    return int(s)


def normalize(vec: np.ndarray) -> np.ndarray:
    len_ = (vec ** 2).sum() ** 0.5
    return vec / len_


def get_active_sensors(norm_means):
    new_means_i = []

    for i, mean in enumerate(norm_means):
        if mean > FILTER_PERCENT:
            new_means_i.append(i)

    return new_means_i


def load(file_name, header_rows, skip_columns=None):
    global means_data
    global air_means
    global sensors_data

    means_data = []
    names.clear()
    data_model = {}

    #  LOAD FILE
    with open(file_name, mode="r") as file:
        lines = file.readlines()
        raw_data = [line.strip().split() for line in lines[header_rows + 1:]]

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
        means_data.append(means)

    #  UPDATE
    air_means = means_data[ [x.lower() for x in names].index("air") ]
    del means_data[ [x.lower() for x in names].index("air") ]
    means_data = np.array(means_data, dtype=DEF_TYPE)
    air_means = np.array(air_means, dtype=DEF_TYPE)

    # NORMALIZE ALL DATA. USE FILTER_AMOUNT
    normalized_means = []
    for x, means in enumerate(means_data):
        means_data[x] = means - air_means
        norm = normalize(means_data[x])
        for i, mean in enumerate(list(means_data[x])):
            if abs(mean) <= FILTER_AMOUNT:
                norm[i] = DEF_TYPE(0)
        normalized_means.append(norm)

    # CREATE GAS MODELS WITH ACTIVE SENSORS AND THEIR FEEDBACKS
    sensors_data = []
    for x, norm_means in enumerate(normalized_means):
        new_means_i = get_active_sensors(norm_means)
        sensors_data.append([
                new_means_i,
                np.array([means_data[x][i] for i in new_means_i], dtype=DEF_TYPE)
            ])


def analyze(test_features):
    test_features = np.array(test_features, dtype=DEF_TYPE)
    test_features -= air_means
    normalized = normalize(test_features)
    test_sensors = get_active_sensors(normalized)
    test_feedback = np.array([test_features[i] for i in test_sensors], dtype=DEF_TYPE)

    if not test_sensors:
        return ["Air", ]

    gases = []
    for i, [sensors, model_feedbacks] in enumerate(sensors_data):
        # Пока проверяю полное соответсвие. Можно потом сделать частичное
        if sensors in test_sensors:  # совпадение сенсоров с образом
            if all([test_feedback[i] > 0 for i in range(len(test_feedback)) if i in test_sensors]):
                pass  # если у сенсоров остались свободные сигналы

            # соотношения показаний с показаниями в модели
            sensor_ks = [test_feedback[i] / model_feedbacks[i] for i in range(len(test_feedback)) if i in test_sensors]
            min_k = min(sensor_ks)

            # вычитаем показания сенсоров, которые включены в текущую модель
            test_feedback -= test_feedback * min_k

            gases.append(names[i])

    return gases if gases else ["Air", ]
