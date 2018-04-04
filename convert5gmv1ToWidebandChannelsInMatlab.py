import datetime
#Will parse all database and create numpy arrays that represent all channels in the database.
#Specificities: some episodes do not have all scenes. And some scenes do not have all receivers.
#Assuming Ne episodes, with Ns scenes each, and Nr receivers (given there was only one transmitter),
#there are Ne x Ns x Nr channel matrices and each must represent L=25 rays.
#With Ne=119, Ns=50, Nr=10, we have 59500 matrices with 25 rays. It is better to save
#each episode in one file, with the matrix given by
#scene 1:Ns x Tx_index x Rx_index x numberRays and the follow for each ray
        # path_gain
        # timeOfArrival
        # departure_elevation
        # departure_azimuth
        # arrival_elevation
        # arrival_azimuth
        # isLOS

import numpy as np
from shapely import geometry
from matplotlib import pyplot as plt

from rwisimulation.positionmatrix import position_matrix_per_object_shape, calc_position_matrix
from rwisimulation.calcrxpower import calc_rx_power

import save5gmdata as fgdb

#import config as c
class c:
    #analysis_area = (648, 348, 850, 685)
    analysis_area = (744, 429, 767, 679)
    analysis_area_resolution = 0.5
    antenna_number = 4
    frequency = 6e10
analysis_polygon = geometry.Polygon([(c.analysis_area[0], c.analysis_area[1]),
                                     (c.analysis_area[2], c.analysis_area[1]),
                                     (c.analysis_area[2], c.analysis_area[3]),
                                     (c.analysis_area[0], c.analysis_area[3])])
only_los = True

npz_name = 'episode.npz' #output file name

print('Creating file ', npz_name)

session = fgdb.Session()
totalNumEpisodes = session.query(fgdb.Episode).count()

pm_per_object_shape = position_matrix_per_object_shape(c.analysis_area, c.analysis_area_resolution)
print(pm_per_object_shape)

# do not look, just to report
start = datetime.datetime.today()
perc_done = None

fileNamePrefix = 'insiteFile'
extension = '.5gmv1'

plt.ion()
numEpisode = 1
for ep in session.query(fgdb.Episode): #go over all episodes
    # 50 scenes per episode, 10 receivers per scene
    outputFileName = fileNamePrefix + str(numEpisode) + extension
    print('Episode: ' + str(numEpisode) + ' out of ' + str(totalNumEpisodes) + '. Output=' + outputFileName)

    #initialization
    position_matrix_array = np.zeros((50, 10, *pm_per_object_shape), np.int8)
    best_ray_array = np.zeros((50, 10, 4), np.float32)
    best_ray_array.fill(np.nan)
    
    #from the first scene, get all receiver names
    rec_name_to_array_idx_map = [obj.name for obj in ep.scenes[0].objects if len(obj.receivers) > 0]
    print(rec_name_to_array_idx_map)
    
    #process each scene in this episode

    #count # of ep.scenes

    for sc_i, sc in enumerate(ep.scenes):
        #print('Processing scene # ', sc_i)
        polygon_list = []
        polygon_z = []
        polygons_of_interest_idx_list = []
        rec_present = []
        for obj in sc.objects:
            obj_polygon = geometry.asMultiPoint(obj.vertice_array[:,(0,1)]).convex_hull
            # check if object is inside the analysis_area
            if obj_polygon.within(analysis_polygon):
                # if the object is a receiver calc a position_matrix for it
                if len(obj.receivers) > 0:
                    rec_array_idx = rec_name_to_array_idx_map.index(obj.name)
                    for rec in obj.receivers:
                        best_ray = None
                        best_path_gain = - np.inf
                        for ray in rec.rays:
                            if ray.path_gain > best_path_gain:
                                best_path_gain = ray.path_gain
                                best_ray = ray
                        if (best_ray is not None and not best_ray.is_los) or not only_los:
                                best_ray_array[sc_i, rec_array_idx, :] = np.array((
                                    best_ray.departure_elevation,
                                    best_ray.departure_azimuth,
                                    best_ray.arrival_elevation,
                                    best_ray.arrival_azimuth))
                    if (best_ray is not None and not best_ray.is_los) or not only_los:
                        # the next polygon added will be the receiver
                        polygons_of_interest_idx_list.append(len(polygon_list))
                        rec_present.append(obj.name)
                polygon_list.append(obj_polygon)
                polygon_z.append(-obj.dimension[2])
        if len(polygons_of_interest_idx_list) != 0:
            scene_position_matrix = calc_position_matrix(
                c.analysis_area,
                polygon_list,
                c.analysis_area_resolution,
                polygons_of_interest_idx_list,
                polygon_z=polygon_z,
            )
        for rec_i, rec_name in enumerate(rec_present):
            rec_array_idx = rec_name_to_array_idx_map.index(rec_name)
            position_matrix_array[sc_i, rec_array_idx, :] = scene_position_matrix[rec_i]

        # do not look, just to reporting spent time
        perc_done = ((sc_i + 1) / ep.number_of_scenes) * 100
        elapsed_time = datetime.datetime.today() - start
        time_p_perc = elapsed_time / perc_done
        print('\r Done: {:.2f}% Scene: {} time per scene: {} time to finish: {}'.format(
            perc_done,
            sc_i + 1,
            elapsed_time / (sc_i + 1),
            time_p_perc * (100 - perc_done)), end='')

    print()
    numEpisode += 1 #increment episode counter

    #np.savez(npz_name, position_matrix_array=position_matrix_array,
    #         best_ray_array=best_ray_array)
    #break