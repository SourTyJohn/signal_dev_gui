import numpy as np
import tensorflow as tf
from sklearn.model_selection import train_test_split
from os.path import abspath

NAME = "Газоналайзернейрон"

model = None


with open("data/gas_detection_model.txt", mode="r") as file:
    GASES = file.readline().split(".")


def load(name, header_rows, skip_columns=None):
    global model

    data = np.genfromtxt(name, delimiter='\t', dtype=str, skip_header=header_rows)
    labels = data[:, 1]

    features = np.array( data[:, 2:], dtype=int )

    unique_labels = {}
    labels_set = set()
    for label in labels:
        if label not in labels_set:
            labels_set.add(label)
            unique_labels[label] = len(unique_labels.keys())
    labels = np.array([ unique_labels[label] for label in labels ], dtype=int )

    X_train, X_test, y_train, y_test = train_test_split(features, labels, test_size=0.2, random_state=42)
    model = tf.keras.Sequential([
        tf.keras.layers.Dense(64, activation='relu', input_shape=(features.shape[1],)),
        tf.keras.layers.Dense(64, activation='relu'),
        tf.keras.layers.Dense(len(labels), activation='softmax')
    ])
    model.compile(optimizer='adam', loss='sparse_categorical_crossentropy')
    model.fit(features, labels, epochs=5, batch_size=16, validation_data=(X_test, y_test))
    model.save("data/gas_detection_model.h5")

    with open("data/gas_detection_model.txt", mode="w") as file_:
        file_.write(".".join([str(x) for x in unique_labels.keys()]))


def model_load(name="data/gas_detection_model.h5"):
    global model

    if model is None:
        model = tf.keras.models.load_model( abspath(name) )
    return model


def analyze(mass):

    test_data = [int(x) for x in mass[0:]]
    _model = model_load()
    predicted_probabilities = _model.predict([test_data])
    probabilities = predicted_probabilities[0]
    predicted_gas = np.argmax(probabilities)

    return GASES[ predicted_gas ]


def reload(name):
    data = np.genfromtxt(name, delimiter='\t', dtype=int)
    labels = data[:, 1]
    features = data[:, 2:]
    model = tf.keras.models.load_model("../data/gas_detection_model.h5")
    X_train, X_test, y_train, y_test = train_test_split(features, labels, test_size=0.2, random_state=42)
    model.fit(features, labels, epochs=5, batch_size=16, validation_data=(X_test, y_test))
    model.save("gas_detection_model.h5")
