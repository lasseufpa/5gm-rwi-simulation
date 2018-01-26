import struct
import os
import datetime

import numpy as np

from rwiparsing import P2mPaths

"""TODO: maybe we could insert in the DNN a snapshot of street situation and ask for the best path for each receiver
to map this as a reinforced learning we could give a low reward when two users are allocated the same tx element
and a high reward when a good fairness is achieved
"""


def dft_codebook(dim):
    seq = np.matrix(np.arange(dim))
    mat = seq.conj().T * seq
    w = np.exp(-1j * 2 * np.pi * mat / dim)
    return w


def calc_rx_power(departure_angle, arrival_angle, p_gain, antenna_number, frequency=6e10):
    """This .m file uses a m*m SQUARE UPA, so the antenna number at TX, RX will be antenna_number^2.

    - antenna_number^2 number of element arrays in TX, same in RX
    - assumes one beam per antenna element

    the first column will be the elevation angle, and the second column is the azimuth angle correspondingly.
    p_gain will be a matrix size of (L, 1)
    departure angle/arrival angle will be a matrix as size of (L, 2), where L is the number of paths

    t1 will be a matrix of size (nt, nr), each
    element of index (i,j) will be the received
    power with the i-th precoder and the j-th
    combiner in the departing and arrival codebooks
    respectively

    :param departure_angle: ((elevation angle, azimuth angle),) (L, 2) where L is the number of paths
    :param arrival_angle: ((elevation angle, azimuth angle),) (L, 2) where L is the number of paths
    :param p_gain: path gain (L, 1) where L is the number of paths
    :param antenna_number: antenna number at TX, RX is antenna_number**2
    :param frequency: default
    :return:
    """
    c = 3e8
    mlambda = c/frequency
    k = 2 * np.pi / mlambda
    d = mlambda / 2
    nt = np.power(antenna_number, 2)
    m = np.shape(departure_angle)[0]
    nr = nt
    wt = dft_codebook(nt)
    wr = dft_codebook(nr)
    H = np.matrix(np.zeros((nt, nr)))
    gain_dB = p_gain
    path_gain = np.power(10, gain_dB/10)
    antenna_range = np.arange(antenna_number)
    def calc_omega(angle):
        sin = np.sin(angle)
        k_d_sin = k * d * sin[:, 1]
        omegay = k_d_sin * sin[:, 0]
        omegax = k_d_sin * np.cos(angle[:, 0])
        return np.matrix((omegax, omegay))
    departure_omega = calc_omega(departure_angle)
    arrival_omega = calc_omega(arrival_angle)
    def calc_vec_i(i, omega, antenna_range):
        vec = np.exp(1j * omega[:,i] * antenna_range)
        return np.matrix(np.kron(vec[1], vec[0]))
    for i in range(m):
        departure_vec = calc_vec_i(i, departure_omega, antenna_range)
        arrival_vec = calc_vec_i(i, arrival_omega, antenna_range)
        H = H + path_gain[i] * departure_vec.conj().T * arrival_vec
    t1 = wt.conj().T * H * wr
    return t1

if __name__ == '__main__':

    RESULTS_DIR='/Users/psb/ownCloud/Projects/DNN Wireless/rwi-3d-modeling/restuls/run00000'

    BASE_DIR=os.path.dirname(os.path.realpath(__file__))
    P2MPATHS_FILE=os.path.join(RESULTS_DIR, 'study', 'model.paths.t001_01.r002.p2m')

    with open(P2MPATHS_FILE, 'rb') as infile:

        paths = P2mPaths(P2MPATHS_FILE)
        departure_angle = paths.get_departure_angle_ndarray(1)
        arrival_angle = paths.get_arrival_angle_ndarray(1)
        p_gain = paths.get_p_gain_ndarray(1)
        antenna_number = 4
        print(arrival_angle.shape)

        start = datetime.datetime.today()
        t1_py = calc_rx_power(departure_angle, arrival_angle, p_gain, antenna_number)
        stop = datetime.datetime.today()

        #print(np.mean(np.power(t1 - t1_py, 2)))
        print(stop - start)
        print(t1_py)