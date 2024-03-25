import numpy as np

air_means = []

names = []
sensors_data = []
means_data = []


DEF_TYPE = np.float32
NAME = "Метод Расстояний"
FILTER_PERCENT = 0.05
FILTER_AMOUNT = 10
FILTER_FINAL_K = 0.01

DEFAULT_RETURN = [ ['Air', 1.0],  ]

LIMIT_K = 1
MAX_K_PER_ANALYZE = 1.0


def distance(a: np.ndarray, b: np.ndarray, r: float = 0.5,
             p: float = 2) -> float:  # расстояние между n-мерными точками. Евклидово
    return sum((a - b) ** p) ** r


def get_means(vec_like: list) -> np.ndarray:  # считает средние значения по столбцам
    arr = np.array(vec_like, dtype=DEF_TYPE)
    means = np.mean(arr, axis=0, )
    return means


def toInt(s: str) -> int:
    return int(s)


def normalize(vec: np.ndarray) -> np.ndarray:
    len_ = (vec ** 2).sum() ** 0.5
    if len_ == 0:
        return vec
    return vec / len_


def get_active_sensors(norm_means):
    new_means_i = []

    for i, mean in enumerate(norm_means):
        if mean > FILTER_PERCENT:
            new_means_i.append(1)  # i
        else:  # delete
            new_means_i.append(0)

    return new_means_i


def load(file_name, header_rows, skip_columns=None, raw_data=None):
    global means_data
    global air_means
    global sensors_data

    means_data = []
    names.clear()
    data_model = {}

    #  LOAD FILE
    if raw_data is None:
        with open(file_name, mode="r") as file:
            lines = file.readlines()
            raw_data = [line.strip().split() for line in lines[header_rows + 1:]]

    #  DELETE ROWS
    if skip_columns:
        raw_data = np.array( raw_data,)
        for col in skip_columns:
            raw_data = np.delete( raw_data, col, 1 )
        raw_data = list(raw_data)

    '''for _, name, *signals in raw_data:'''
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
    air_index = [x.lower() for x in names].index("air")
    del means_data[air_index]
    del names[air_index]
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
                np.array(means_data[x], dtype=DEF_TYPE),
                norm_means
            ])

    printData()


def contains(_list: list, sub_list: list) -> bool:
    for i in range( len(sub_list) ):
        if sub_list[i] == 1 and _list[i] == 0:
            return False
    return True


def analyze(test_features):
    test_features = np.array(test_features, dtype=DEF_TYPE)
    test_features -= air_means
    normalized = normalize(test_features)
    test_sensors = get_active_sensors(normalized)
    test_feedback = np.array(test_features, dtype=DEF_TYPE)
    if all(x == 0 for x in test_sensors):
        return DEFAULT_RETURN[:]

    distances = [ [x, distance(item[2], test_feedback)] for x, item in enumerate(sensors_data) ]
    distances.sort(key=lambda x: x[1])
    curr_lim_k = MAX_K_PER_ANALYZE
    gases = []
    for [i, _] in distances:
        sensors, model_feedbacks, _ = sensors_data[i]

        if contains(test_sensors, sensors):  # совпадение сенсоров с образом
            # if all([test_feedback[i] > 0 for i in range(len(test_feedback)) if i in test_sensors]):
            #     pass  # если у сенсоров остались свободные сигналы

            # соотношения показаний с показаниями в модели
            sensor_ks = [test_feedback[i] / model_feedbacks[i] for i in range(len(test_feedback)) if sensors[i] != 0]
            if LIMIT_K: sensor_ks += [LIMIT_K, ]
            sensor_ks += [curr_lim_k, ]
            min_k = min(sensor_ks)
            curr_lim_k -= min_k

            if min_k > FILTER_FINAL_K:
                # вычитаем показания сенсоров, которые включены в текущую модель
                test_feedback -= [model_feedbacks[x] * min_k if sensors[x] else 0 for x in range(len(test_feedback))]
                gases.append( [names[i], min_k] )

    return gases if gases else DEFAULT_RETURN[:]


def printData():
    print(sensors_data)
    for x in range(len(sensors_data)):
        print(x, names[x])
        print('SENSORS_DATA: ')
        for line in range(len(sensors_data[x][0])):
            print(line, end='\t')
            print(int( sensors_data[x][0][line] ), end='\t')
            print(int( sensors_data[x][1][line] ), end='\t')
            t = str( sensors_data[x][2][line] )
            print(t[:min(len(t), 4)])
        print('MEANS_DATA')
        print(means_data[x])
        print('--------------------')


if __name__ == '__main__':
    """testing"""

    dt = [
        [0, 'Air',     1,      1,  1,  1,  1],
        [0, 'Gas_1',   1,      1,  1,  90, 1],
        [0, 'Gas_2',   1,      80, 1,  1,  1],
        [0, 'Gas_0+2', 100,    1,  20, 1,  1],
        [0, 'Gas_4+2', 1,      1,  40, 1,  60]
    ]
    load('', 0, raw_data=dt)

    print(names)
    print(sensors_data)

    print('--- TESTS ---')
    print()
    #
    test = [1, 1, 1, 1, 1]
    test_res = ['Air', ]
    res = analyze(test)
    print(res, '\t\t\t\t\t', test_res if res != test_res else "GOOD")

    test = [1, 40, 1, 1, 1]
    test_res = ['Gas_2', ]
    res = analyze(test)
    print(res, '\t\t\t\t\t', test_res if res != test_res else "GOOD")

    test = [1,  1,  1,  120, 1]
    test_res = ['Gas_1', ]
    res = analyze(test)
    print(res, '\t\t\t\t\t', test_res if res != test_res else "GOOD")

    test = [1, 1, 100, 1, 1]
    test_res = ['Air', ]
    res = analyze(test)
    print(res, '\t\t\t\t\t', test_res if res != test_res else "GOOD")

    test = [1, 40, 1, 30, 1]
    test_res = ['Gas_1', 'Gas_2']
    res = analyze(test)
    print(res, '\t\t\t\t\t', test_res if res != test_res else "GOOD")

    test = [1, 40, 1, 30, 1]
    test_res = ['Gas_1', 'Gas_2']
    res = analyze(test)
    print(res, '\t\t\t\t\t', test_res if res != test_res else "GOOD")

    test = [100, 1, 30, 1, 60]
    test_res = ['Gas_0+2', 'Gas_4+2']
    res = analyze(test)
    print(res, '\t\t\t\t\t', test_res if res != test_res else "GOOD")
