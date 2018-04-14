import os
import json
import numpy as np

import config as c

from rwisimulation.tfrecord import UnexpectedCarsWithAntennaChangeError, SceneNotInEpisodeSequenceError, \
    EpisodeNotStartingFromZeroError
from rwimodeling import objects
from rwiparsing import P2mPaths

import save5gmdata as fgdb

last_simulation_info = None
simulation_info = None
session = fgdb.Session()

sc_i = 0
ep_i = 0
episode = None
for run_i in c.n_run:
#for run_i in range(50, 100):
    run_dir = os.path.join(c.results_dir, c.base_run_dir_fn(run_i))
    object_file_name = os.path.join(run_dir, os.path.basename(c.dst_object_file_name))
    abs_paths_file_name = os.path.join(run_dir, os.path.basename(c.project_output_dir), c.paths_file_name)
    abs_simulation_info_file_name = os.path.join(run_dir, c.simulation_info_file_name)
    with open(abs_simulation_info_file_name) as infile:
        simulation_info = json.load(infile)

    # start of episode
    if simulation_info['scene_i'] == 0:
        ep_i += 1
        if episode is not None:
            session.add(episode)
            session.commit()

        episode = fgdb.Episode(
            insite_pah=run_dir,
            sumo_path='',
            # TODO
            simulation_time_begin=0,
            sampling_time=c.sampling_interval,
        )

    if episode is None:
        raise EpisodeNotStartingFromZeroError("From file {}".format(object_file_name))

    if simulation_info['scene_i'] != episode.number_of_scenes:
        raise SceneNotInEpisodeSequenceError('Expecting {} found {}'.format(
            len(episode.number_of_scenes),
            simulation_info['scene_i'],
        ))

    with open(object_file_name) as infile:
        obj_file = objects.ObjectFile.from_file(infile)
    paths = P2mPaths(abs_paths_file_name)

    scene = fgdb.Scene()
    # TODO read from InSite
    scene.study_area = ((0, 0, 0), (0, 0, 0))

    rec_i = 0
    for structure_group in obj_file:
        for structure in structure_group:
            for sub_structure in structure:
                object = fgdb.InsiteObject(name=structure.name)
                object.vertice_array = sub_structure.as_vertice_array()
                dimension_max = np.max(object.vertice_array, 0)
                dimension_min = np.min(object.vertice_array, 0)
                object.dimension = dimension_max - dimension_min
                object.position = dimension_max - (object.dimension / 2)

                if structure.name in simulation_info['cars_with_antenna']:
                    receiver = fgdb.InsiteReceiver()
                    if paths.get_total_received_power(rec_i+1) is not None:
                        receiver.total_received_power = paths.get_total_received_power(rec_i+1)
                        receiver.mean_time_of_arrival=paths.get_mean_time_of_arrival(rec_i+1)
                        receiver.position = object.position

                        for departure, arrival, path_gain, arrival_time, interactions_list in zip(
                                paths.get_departure_angle_ndarray(rec_i+1),
                                paths.get_arrival_angle_ndarray(rec_i+1),
                                paths.get_p_gain_ndarray(rec_i+1),
                                paths.get_arrival_time_ndarray(rec_i+1),
                                paths.get_interactions_list(rec_i+1)):
                            ray = fgdb.Ray()
                            ray.departure_elevation, ray.departure_azimuth = departure
                            ray.arrival_elevation, ray.arrival_azimuth = arrival
                            ray.path_gain = path_gain
                            ray.time_of_arrival = arrival_time
                            ray.interactions = interactions_list

                            receiver.rays.append(ray)

                    object.receivers.append(receiver)
                    rec_i += 1
            scene.objects.append(object)

    episode.scenes.append(scene)
    sc_i += 1
    print('\rProcessed episode: {} scene: {} '.format(ep_i, sc_i), end='')
print()
session.add(episode)
session.commit()
session.close()