import tensorflow as tf
import numpy as np

from rwimodeling import objects
from rwiparsing import P2mPaths

from config import *
from positionmatrix import calc_position_matrix, matrix_plot
from calcrxpower import calc_rx_power


def to_tfrecord(object_file_name, paths_file_name, resolution=1, antenna_number=4):
    with open(object_file_name) as infile:
        obj = objects.ObjectFile.from_file(infile)

    polygon_list = []
    for structure_group in obj:
        for structure in structure_group:
            for sub_structure in structure:
                polygon_list.append(sub_structure.as_polygon())

    matrix = calc_position_matrix((633, 456, 663, 531), polygon_list, resolution)

    print(matrix.shape)
    #matrix_plot(matrix[1])

    paths = P2mPaths(paths_file_name)


    for rec_i in range(0, matrix.shape[0]):
        departure_angle = paths.get_departure_angle_ndarray(rec_i + 1)
        arrival_angle = paths.get_arrival_angle_ndarray(rec_i + 1)
        p_gain = paths.get_p_gain_ndarray(rec_i + 1)

        t1 = calc_rx_power(departure_angle, arrival_angle, p_gain, antenna_number)
        t1 = np.abs(t1)
        best_tx_rx = np.argwhere(t1 == np.max(t1))[0]
        best_tx_rx = best_tx_rx.astype(np.uint8)

        example_dict = dict()
        example_dict['position_matrix'] = tf.train.Feature(
            bytes_list=tf.train.BytesList(value=[matrix[rec_i].tobytes()])
        )
        example_dict['best_tx_rx'] = tf.train.Feature(
            bytes_list=tf.train.BytesList(value=[best_tx_rx.tobytes()])
        )
        example = tf.train.Example(
            features=tf.train.Features(feature=example_dict)
        )
        yield example


if __name__ == '__main__':
    with tf.python_io.TFRecordWriter(tfrecord_file_name, tfrecord_options) as tfr_writer:
        for run_i in range(n_run):
            run_dir = os.path.join(results_dir, "run{:05d}".format(run_i))
            object_file_name = os.path.join(run_dir, 'random-line.object')
            paths_file_name = os.path.join(run_dir, 'study', 'model.paths.t001_01.r002.p2m')
            for example in to_tfrecord(object_file_name, paths_file_name, 1):
                tfr_writer.write(example.SerializeToString())