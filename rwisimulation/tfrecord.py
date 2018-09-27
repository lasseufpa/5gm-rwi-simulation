import os
import logging
import json

import tensorflow as tf
import numpy as np

from rwimodeling import objects
from rwiparsing import P2mPaths

from .positionmatrix import calc_position_matrix, matrix_plot
from .calcrxpower import calc_rx_power


class UnexpectedCarsWithAntennaChangeError(Exception):
    pass


class EpisodeNotStartingFromZeroError(Exception):
    pass


class SceneNotInEpisodeSequenceError(Exception):
    pass


class Episode:

    def __init__(self, analysis_area, resolution=1, antenna_number=4, frequency=6e4, n_paths_to_tfrecord=25,
                 cars_with_antenna=None):
        self.analysis_area = analysis_area
        self.resolution = resolution
        self.antenna_number = antenna_number
        self.frequency = frequency
        self.n_paths_to_tfrecord = n_paths_to_tfrecord
        self.cars_with_antenna = cars_with_antenna

        self.n_antenna_elements = self.antenna_number ** 2

        self.position_matrix = None
        self.best_tx_rx = None
        self.departure_angle = None
        self.arrival_angle = None
        self.p_gain = None
        self.t1 = None
        self.from_obj = None

        # String (len) of then objects file
        #AK: I moved this defition from config.py
        self.dtype_of_obj_path = 'U100'

    def to_example(self):
        example_dict = dict()
        example_dict['position_matrix'] = tf.train.Feature(
            bytes_list=tf.train.BytesList(value=[self.position_matrix.tobytes()])
        )
        example_dict['best_tx_rx'] = tf.train.Feature(
            bytes_list=tf.train.BytesList(value=[self.best_tx_rx.tobytes()])
        )
        example_dict['departure_angle'] = tf.train.Feature(
            bytes_list=tf.train.BytesList(value=[self.departure_angle.tobytes()])
        )
        example_dict['arrival_angle'] = tf.train.Feature(
            bytes_list=tf.train.BytesList(value=[self.arrival_angle.tobytes()])
        )
        example_dict['p_gain'] = tf.train.Feature(
            bytes_list=tf.train.BytesList(value=[self.p_gain.tobytes()])
        )
        example_dict['t1'] = tf.train.Feature(
            bytes_list=tf.train.BytesList(value=[self.t1.tobytes()])
        )
        example_dict['from_obj'] = tf.train.Feature(
            bytes_list=tf.train.BytesList(value=[self.from_obj.tobytes()])
        )
        example = tf.train.Example(
            features=tf.train.Features(feature=example_dict)
        )
        return example

    def add_scene(self, object_file_name, paths_file_name, scene_i):
        if self.position_matrix is None:
            if scene_i != 0:
                raise EpisodeNotStartingFromZeroError("From file {}".format(object_file_name))
        else:
            if len(self.position_matrix) != scene_i:
                raise SceneNotInEpisodeSequenceError('Expecting {} found {}'.format(
                    len(self.position_matrix),
                    scene_i,
                ))

        def add_dim(array):
            return np.array(array, ndmin=array.ndim+1)

        matrix_scene, best_tx_rx_scene, departure_angle_scene, arrival_angle_scene, p_gain_scene, t1_scene = \
            [add_dim(i) for i in self.calc_scene(object_file_name, paths_file_name)]

        #I moved from config.py to this class:
        #from_obj = np.array(object_file_name, dtype=c.dtype_of_obj_path, ndmin=2)
        from_obj = np.array(object_file_name, dtype=self.dtype_of_obj_path, ndmin=2)

        def join_or_a(a, b):
            return a if b is None else np.concatenate((a, b), 0)

        self.position_matrix, self.best_tx_rx, self.departure_angle, self.arrival_angle, self.p_gain, self.t1, \
            self.from_obj = \
                [join_or_a(*i) for i in (
                    (matrix_scene, self.position_matrix),
                    (best_tx_rx_scene, self.best_tx_rx),
                    (departure_angle_scene, self.departure_angle),
                    (arrival_angle_scene, self.arrival_angle),
                    (p_gain_scene, self.p_gain),
                    (t1_scene, self.t1),
                    (from_obj, self.from_obj),
                )]

    def calc_scene(self, object_file_name, paths_file_name):
        with open(object_file_name) as infile:
            obj = objects.ObjectFile.from_file(infile)

        # store the polygons for which matrix will be calculated
        polygons_of_interest_idx_list = []
        # store the index of the receiver for each polygon in the first dimension of matrix
        position_matrix_rec_map = []
        l = self.n_paths_to_tfrecord
        polygon_list = []
        for structure_group in obj:
            for structure in structure_group:
                for sub_structure in structure:
                    if structure.name in self.cars_with_antenna:
                        polygons_of_interest_idx_list.append(len(polygon_list))
                        position_matrix_rec_map.append(self.cars_with_antenna.index(structure.name))
                    polygon_list.append(sub_structure.as_polygon())

        matrix = calc_position_matrix(self.analysis_area, polygon_list, self.resolution,
                                      polygons_of_interest_idx_list=polygons_of_interest_idx_list)

        #print(matrix.shape)
        #matrix_plot(matrix[1])

        paths = P2mPaths(paths_file_name)

        n_rec = len(self.cars_with_antenna)
        matrix_scene = np.empty((n_rec, *matrix.shape[1:]), matrix.dtype)
        matrix_scene.fill(np.nan)
        best_tx_rx_scene = np.empty((n_rec, 2), np.uint8)
        best_tx_rx_scene.fill(np.nan)
        departure_angle_scene = np.empty((n_rec, l, 2), np.float32)
        departure_angle_scene.fill(np.nan)
        arrival_angle_scene = np.empty((n_rec, l, 2), np.float32)
        arrival_angle_scene.fill(np.nan)
        p_gain_scene = np.empty((n_rec, l), np.float32)
        p_gain_scene.fill(np.nan)
        t1_scene = np.empty((n_rec, self.n_antenna_elements, self.n_antenna_elements), np.complex64)
        t1_scene.fill(np.nan)

        for rec_i, rec_name in enumerate(self.cars_with_antenna):
            try:
                obj_order_rec_i = position_matrix_rec_map.index(rec_i)
            except ValueError:
                pass

            departure_angle = paths.get_departure_angle_ndarray(obj_order_rec_i + 1).astype(np.float32)
            arrival_angle = paths.get_arrival_angle_ndarray(obj_order_rec_i + 1).astype(np.float32)
            p_gain = paths.get_p_gain_ndarray(obj_order_rec_i + 1).astype(np.float32)

            if l < len(departure_angle):
                logging.warning("Saving only {} of {} available paths for {}".format(
                    l,
                    len(departure_angle),
                    paths_file_name
                ))

            matrix_scene[rec_i, :] = matrix[obj_order_rec_i]

            departure_angle_scene[rec_i, :len(departure_angle), :] = departure_angle
            arrival_angle_scene[rec_i, :len(arrival_angle), :] = arrival_angle
            p_gain_scene[rec_i, :len(p_gain)] = p_gain

            t1 = calc_rx_power(departure_angle, arrival_angle, p_gain, self.antenna_number, self.frequency) \
                .astype(np.complex64)
            t1_abs = np.abs(t1)
            t1_scene[rec_i, :] = t1
            best_tx_rx = np.argwhere(t1_abs == np.max(t1_abs))[0]
            best_tx_rx_scene[rec_i, :] = best_tx_rx.astype(np.uint8)
            #best_idx = np.argmax(p_gain)
            #best_tx_rx = np.array((departure_angle[best_idx], arrival_angle[best_idx]), dtype=np.float32)
        return matrix_scene, best_tx_rx_scene, departure_angle_scene, arrival_angle_scene, p_gain_scene, t1_scene


def main():
    import config as c
    with tf.python_io.TFRecordWriter(c.tfrecord_file_name, c.tfrecord_options) as tfr_writer:
        ex_c = 0
        episode = None
        for run_i in c.n_run:
            run_dir = os.path.join(c.results_dir, c.base_run_dir_fn(run_i))
            object_file_name = os.path.join(run_dir, os.path.basename(c.dst_object_file_name))
            abs_paths_file_name = os.path.join(run_dir, os.path.basename(c.project_output_dir), c.paths_file_name)
            #abs_paths_file_name = os.path.join(run_dir, c.paths_file_name)
            abs_simulation_info_file_name = os.path.join(run_dir, c.simulation_info_file_name)
            with open(abs_simulation_info_file_name) as infile:
                simulation_info = json.load(infile)

            while True:
                # start of episode
                if episode is None:
                    episode = Episode(c.analysis_area, c.analysis_area_resolution, c.antenna_number, c.frequency,
                                      c.n_paths_to_tfrecord, simulation_info['cars_with_antenna'])
                else:
                    try:
                        episode.add_scene(object_file_name, abs_paths_file_name, simulation_info['scene_i'])
                        # go to next scene
                        if episode.cars_with_antenna != simulation_info['cars_with_antenna']:
                            raise UnexpectedCarsWithAntennaChangeError('In run {}'.format(run_dir))
                        break
                    # episode is over, write and start a new one
                    except SceneNotInEpisodeSequenceError:
                        tfr_writer.write(episode.to_example().SerializeToString())
                        ex_c += 1
                        episode = None
                        raise Exception()

            print('wrote {} examples'.format(ex_c))

if __name__ == '__main__':
    main()