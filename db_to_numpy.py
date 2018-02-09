import datetime

import numpy as np
from shapely import geometry
from matplotlib import pyplot as plt

from rwisimulation.positionmatrix import position_matrix_per_object_shape, calc_position_matrix

import save5gmdata as fgdb

#import config as c
class c:
    #analysis_area = (648, 348, 850, 685)
    analysis_area = (744, 429, 767, 679)
    analysis_area_resolution = 0.5
analysis_polygon = geometry.Polygon([(c.analysis_area[0], c.analysis_area[1]),
                                     (c.analysis_area[2], c.analysis_area[1]),
                                     (c.analysis_area[2], c.analysis_area[3]),
                                     (c.analysis_area[0], c.analysis_area[3])])

npz_name = 'episode.npz'

session = fgdb.Session()

pm_per_object_shape = position_matrix_per_object_shape(c.analysis_area, c.analysis_area_resolution)

# do not look, just to report
start = datetime.datetime.today()
perc_done = None

plt.ion()
for ep in session.query(fgdb.Episode):
    # 50 scenas, 10 receivers per scena
    position_matrix_array = np.zeros((50, 10, *pm_per_object_shape), np.int8)
    best_ray_array = np.zeros((50, 10, 4), np.float32)
    best_ray_array.fill(np.nan)
    rec_name_to_array_idx_map = [obj.name for obj in ep.scenes[0].objects if len(obj.receivers) > 0]
    print(rec_name_to_array_idx_map)
    for sc_i, sc in enumerate(ep.scenes):
        polygon_list = []
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
                        best_ray_array[sc_i, rec_array_idx, :] = np.array((
                            best_ray.departure_elevation,
                            best_ray.departure_azimuth,
                            best_ray.arrival_elevation,
                            best_ray.arrival_azimuth))
                    # the next polygon added will be the receiver
                    polygons_of_interest_idx_list.append(len(polygon_list))
                    rec_present.append(obj.name)
                polygon_list.append(obj_polygon)
        scene_position_matrix = calc_position_matrix(
            c.analysis_area,
            polygon_list,
            c.analysis_area_resolution,
            polygons_of_interest_idx_list,
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
            time_p_perc * (100 - perc_done),
        ), end='')
    print()

    np.savez(npz_name, position_matrix_array=position_matrix_array,
             best_ray_array=best_ray_array)
    break