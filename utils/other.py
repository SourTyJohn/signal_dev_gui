from PyQt5 import QtWidgets as QW
import numpy as np

from constants import *
import importlib.util
import sys


__all__ = (
    "get_center",
    "load_script",

    "normalize",
    "restrain",
)


def get_center():
    point = QW.QDesktopWidget().availableGeometry().center()
    return int( point.x() * 0.6 ), int( point.y() * 0.6 )


def load_script(file_name, module_name="ActiveLib"):
    try:
        spec = importlib.util.spec_from_file_location(module_name, file_name)
        lib = importlib.util.module_from_spec( spec )
        sys.modules[module_name] = lib
        spec.loader.exec_module( lib )

        try:
            lib.load()
            lib.analyze()

        except AttributeError:
            return None, "Script must have load(text: str) and analyze(data: list) functions"

        except TypeError:
            pass

    except Exception as e:
        return None, e

    return lib, 0


def normalize(vec: np.ndarray) -> np.ndarray:
    len_ = (vec ** 2).sum() ** 0.5
    return vec / len_ * 1000 // 1


def restrain(vec: np.ndarray, prev_vec: np.ndarray) -> np.ndarray:
    vec = list(vec)
    for x in range(len(vec)):
        diff = abs(1 - vec[x] / int(float(prev_vec[x])))
        if diff > RESTRAIN_K:
            vec[x] *= (1 - RESTRAIN_K)

    return np.array(vec, dtype=np.int32)
