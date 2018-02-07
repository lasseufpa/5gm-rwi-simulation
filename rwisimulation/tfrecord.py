import os

import tensorflow as tf
import numpy as np

from rwimodeling import objects
from rwiparsing import P2mPaths

import config as c
from .positionmatrix import calc_position_matrix, matrix_plot
from .calcrxpower import calc_rx_power


def to_tfrecord(analysis_area, object_file_name, paths_file_name, resolution=1, antenna_number=4, frequency=6e4):
    with open(object_file_name) as infile:
        obj = objects.ObjectFile.from_file(infile)

    polygon_list = []
    for structure_group in obj:
        for structure in structure_group:
            for sub_structure in structure:
                polygon_list.append(sub_structure.as_polygon())

    matrix = calc_position_matrix(analysis_area, polygon_list, resolution)

    #print(matrix.shape)
    #matrix_plot(matrix[1])

    paths = P2mPaths(paths_file_name)

    for rec_i in range(matrix.shape[0]):
        departure_angle_o = paths.get_departure_angle_ndarray(rec_i + 1).astype(np.float32)
        arrival_angle_o = paths.get_arrival_angle_ndarray(rec_i + 1).astype(np.float32)
        p_gain_o = paths.get_p_gain_ndarray(rec_i + 1).astype(np.float32)

        l = 25

        departure_angle = np.empty((l, 2), np.float32)
        departure_angle[:] = np.nan
        departure_angle[:len(departure_angle_o),:] = departure_angle_o
        arrival_angle = np.empty((l, 2), np.float32)
        arrival_angle[:] = np.nan
        arrival_angle[:len(arrival_angle_o),:] = arrival_angle_o
        p_gain = np.empty((l,), np.float32)
        p_gain[:] = np.nan
        p_gain[:len(p_gain_o)] = p_gain_o

        t1 = calc_rx_power(departure_angle, arrival_angle, p_gain, antenna_number, frequency).astype(np.complex64)
        t1_abs = np.abs(t1)
        best_tx_rx = np.argwhere(t1_abs == np.max(t1_abs))[0]
        best_tx_rx = best_tx_rx.astype(np.uint8)
        #best_idx = np.argmax(p_gain)
        #best_tx_rx = np.array((departure_angle[best_idx], arrival_angle[best_idx]), dtype=np.float32)

        example_dict = dict()
        example_dict['position_matrix'] = tf.train.Feature(
            bytes_list=tf.train.BytesList(value=[matrix[rec_i].tobytes()])
        )
        example_dict['best_tx_rx'] = tf.train.Feature(
            bytes_list=tf.train.BytesList(value=[best_tx_rx.tobytes()])
        )
        example_dict['departure_angle'] = tf.train.Feature(
            bytes_list=tf.train.BytesList(value=[departure_angle.tobytes()])
        )
        example_dict['arrival_angle'] = tf.train.Feature(
            bytes_list=tf.train.BytesList(value=[arrival_angle.tobytes()])
        )
        example_dict['p_gain'] = tf.train.Feature(
            bytes_list=tf.train.BytesList(value=[p_gain.tobytes()])
        )
        example_dict['t1'] = tf.train.Feature(
            bytes_list=tf.train.BytesList(value=[t1.tobytes()])
        )
        example = tf.train.Example(
            features=tf.train.Features(feature=example_dict)
        )
        yield example


def main():
    with tf.python_io.TFRecordWriter(c.tfrecord_file_name, c.tfrecord_options) as tfr_writer:
        ex_c = 0
        for run_i in c.n_run:
            run_dir = os.path.join(c.results_dir, c.base_run_dir_fn(run_i))
            object_file_name = os.path.join(run_dir, os.path.basename(c.dst_object_file_name))
            #abs_paths_file_name = os.path.join(run_dir, os.path.basename(c.project_output_dir), c.paths_file_name)
            abs_paths_file_name = os.path.join(run_dir, c.paths_file_name)
            for example in to_tfrecord(c.analysis_area, object_file_name, abs_paths_file_name,
                                       c.analysis_area_resolution, c.antenna_number, c.frequency):
                ex_c += 1
                tfr_writer.write(example.SerializeToString())

            print('wrote {} examples'.format(ex_c))

if __name__ == '__main__':
    main()