import numpy as np


def coords_from_spec(start, end, step):
    num = round((abs(start-end)/step) + 1)
    coords = np.linspace(start, end, num)
    return coords, num


def ind_for_spec(start, end, step, val):
    return int((val-start)/step * np.sign(end-start))
