import os
import struct
import unittest

import numpy as np

from calcrxpower import calc_rx_power

EXAMPLE_DIR=os.path.dirname(os.path.realpath(__file__))
MATLAB_DATA=os.path.join(EXAMPLE_DIR, 'data',
                         'test_calc_rx_power.bin')


class CalcRxPowerTest(unittest.TestCase):

    def setUp(self):
        L = 15
        with open(MATLAB_DATA, 'rb') as infile:
            def get_float_complex(L):
                L2 = np.array(struct.unpack('d' * L * 2, infile.read(L * 2 * 8)), dtype=np.float64)
                L2 = L2.reshape((L, 2), order='F')
                L2 = L2[:, 0] + L2[:, 1] * 1j
                return L2

            self.departure_angle = get_float_complex(L * 2).reshape((L, 2), order='F')
            self.arrival_angle = get_float_complex(L * 2).reshape((L, 2), order='F')
            self.p_gain = get_float_complex(L)
            self.antenna_number = int(np.real(get_float_complex(1)))
            self.t1 = get_float_complex(16 * 16).reshape((16, 16), order='F')

    def test_input_and_translate_object_file(self):
        t1_py = calc_rx_power(self.departure_angle,
                              self.arrival_angle,
                              self.p_gain,
                              self.antenna_number)

        error = complex(np.mean(np.power(self.t1 - t1_py, 2), (0,1)))

        self.assertAlmostEqual(np.real(error), 0, 20)
        self.assertAlmostEqual(np.imag(error), 0, 20)

    def tearDown(self):
        pass