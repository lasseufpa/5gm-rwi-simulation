import os

from matplotlib import pyplot as plt
import numpy as np

from rwimodeling import objects
from rwiparsing import P2mPaths

import config as c
from rwisimulation.positionmatrix import calc_position_matrix, matrix_plot
from rwisimulation.calcrxpower import calc_rx_power


def to_tfrecord(analysis_area, object_file_name, paths_file_name, resolution=1, antenna_number=4):
    with open(object_file_name) as infile:
        obj = objects.ObjectFile.from_file(infile)

    interest_car_i = None
    polygon_list = []
    for structure_group in obj:
        for structure_i, structure in enumerate(structure_group):
            if structure.name == 'flowC.0':
                interest_car_i = structure_i
            for sub_structure in structure:
                polygon_list.append(sub_structure.as_polygon())

    matrix = calc_position_matrix(analysis_area, polygon_list, resolution)

    #print(matrix.shape)
    #matrix_plot(matrix[1])

    paths = P2mPaths(paths_file_name)

    rec_i = 0
    departure_angle = paths.get_departure_angle_ndarray(rec_i + 1)
    arrival_angle = paths.get_arrival_angle_ndarray(rec_i + 1)
    p_gain = paths.get_p_gain_ndarray(rec_i + 1)

    t1 = calc_rx_power(departure_angle, arrival_angle, p_gain, antenna_number)
    t1 = np.abs(t1)
    best_tx_rx = np.argwhere(t1 == np.max(t1))[0]
    best_tx_rx = best_tx_rx.astype(np.uint8)

    return matrix[interest_car_i], best_tx_rx

def main():
    cache = True
    cache_file_name = 'plotbeans.npz'
    pos_matrix_array = None
    bean_array = None
    if cache:
        try:
            cache_file = np.load(cache_file_name)
            pos_matrix_array = cache_file['pos_matrix_array']
            bean_array = cache_file['bean_array']
        except FileNotFoundError:
            pass

    if pos_matrix_array is None:
        bean_array = np.zeros((20, 2))
        pos_matrix_array = np.zeros((20, *c.position_matrix_shape))
        for run_i in c.n_run:
            run_dir = os.path.join(c.results_dir, c.base_run_dir_fn(run_i))
            object_file_name = os.path.join(run_dir, os.path.basename(c.dst_object_file_name))
            abs_paths_file_name = os.path.join(run_dir, os.path.basename(c.project_output_dir), c.paths_file_name)
            pos_matrix, best_tx_rx = to_tfrecord(c.analysis_area, object_file_name, abs_paths_file_name,
                                                 c.analysis_area_resolution, c.antenna_number)
            pos_matrix_array[run_i,:] = pos_matrix
            bean_array[run_i,:] = best_tx_rx
        if cache:
            np.savez(cache_file_name, pos_matrix_array=pos_matrix_array, bean_array=bean_array)

    bean_line = []
    for run_i in range(pos_matrix_array.shape[0]):
        pos_matrix = pos_matrix_array[run_i]
        best_tx_rx = bean_array[run_i]

        bean_line.append(best_tx_rx[0] * 16 + best_tx_rx[1])

        ax = plt.subplot(3,10,11 + run_i)
        ax.imshow(pos_matrix.T, origin='lower')
    bean_line = np.array(bean_line)

    ax = plt.subplot(3,1,1)
    ax.plot(bean_line)
    plt.show()

if __name__ == '__main__':
    main()