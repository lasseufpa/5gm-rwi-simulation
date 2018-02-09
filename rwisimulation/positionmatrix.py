import os
import datetime
import multiprocessing
from operator import itemgetter

import numpy as np
from shapely import geometry

from rwimodeling import objects


def plot(polygon):
    from matplotlib import pyplot as plt
    from descartes.patch import PolygonPatch
    patch = PolygonPatch(polygon)
    ax = plt.subplot()
    ax.add_patch(patch)
    bounds = polygon.bounds
    ax.set_xlim(bounds[0] - 5, bounds[2] + 5)
    ax.set_ylim(bounds[1] - 5, bounds[3] + 5)
    plt.show()


def matrix_plot(matrix):
    from matplotlib import pyplot as plt
    plt.imshow(matrix.T, origin='lower')
    plt.show()


def position_matrix_per_object_shape(bounds, resolution):
    bounds = np.array(bounds).reshape(2,2)
    # shape each "image"
    shape = ((bounds[1] - bounds[0]) / resolution).astype(int)
    # tensorflow really wants it as int
    shape = [int(i) for i in shape]
    return tuple(shape)


def _calc_position_matrix_row(args):
    i, matrix, polygon_list, resolution, bounds, polygons_of_interest_idx_list, report_to, start, polygon_z = args
    for j in range(matrix.shape[2]):
        # create the point starting in (0, 0) with resolution "1"
        point_np = np.array((i, j))
        # apply the resolution and translate to the "area of interest"
        point_np = (point_np * resolution) + bounds[0]
        point = geometry.Point(point_np)
        #point = affinity.translate(
        #    geometry.Point(point_np),
        #    *bounds[0])
        #if point.within(all_polygons):
        for polygon_i, polygon in enumerate(polygon_list):
            if point.within(polygon):
                matrix[:, i, j] = 1 if polygon_z is None else polygon_z[polygon_i]
                if polygon_i in polygons_of_interest_idx_list:
                    polygon_idx = polygons_of_interest_idx_list.index(polygon_i)
                    matrix[polygon_idx, i, j] = 2
    if report_to is not None:
        if i != 0:
            completed_perc = (i / matrix.shape[1]) * 100
            if np.int(np.round(completed_perc)) % 10 == 0:
                now = datetime.datetime.today()
                time_p_perc = (datetime.datetime.today() - start) / completed_perc
                finish_at = time_p_perc * (100 - completed_perc) + now
            report_to.write('\rCalculating position matrix: {:.2f}% time/%: {} finish at: {}'.format(
                completed_perc,
                time_p_perc,
                finish_at,
            ))
    return matrix

def calc_position_matrix(bounds, polygon_list, resolution=1, polygons_of_interest_idx_list=None, report_to=None, polygon_z=None):
    """Represents the receivers and other objects in a position matrix

    :param bounds: (minx, miny, maxx, maxy) of the region to study
    :param polygon_list: a list of polygons
    :param resolution: size of the pixel (same unity as bounds, default meters)
    :param polygons_of_interest_list: idx of polygon_list which will be "marked as receivers" on return, default: all
    :return: a matrix with shape (len(polygon_list), (maxx - minx) / resolution, (maxy - miny) / resolution)
    each point in the matrix[polygon_i] is a "pixel", the pixel is 1 when inside any polygon;
    2 when inside polygon_i; and 0 otherwise
    """
    if polygons_of_interest_idx_list is None:
        polygons_of_interest_idx_list = list(range(len(polygon_list)))
    bounds = np.array(bounds).reshape(2,2)
    n_polygon = len(polygons_of_interest_idx_list)
    all_polygons = geometry.MultiPolygon(polygon_list)
    # shape each "image"
    shape = position_matrix_per_object_shape(bounds, resolution)
    # add n_polygon as first dimension
    shape = np.concatenate((np.array(n_polygon, ndmin=1), shape))
    matrix = np.zeros(shape, dtype=np.uint8)
    start = datetime.datetime.today()
    time_p_perc = np.inf

    args = []
    for i in range(matrix.shape[1]):
        args.append((i, matrix, polygon_list, resolution, bounds, polygons_of_interest_idx_list, report_to, start, polygon_z))

    with multiprocessing.Pool() as pool:
        matrix_out = pool.map(_calc_position_matrix_row, args)

    for mat in matrix_out:
        matrix += mat

    #import matplotlib as mpl
    #mpl.use('Agg')
    #from matplotlib import pyplot as plt

    #plt.imshow(matrix[0].T, origin='lower')
    #plt.savefig('oi.png')

    #import IPython
    #IPython.embed()

    if report_to is not None:
        report_to.write('\n')
    return matrix

if __name__ == '__main__':

    with open(os.path.join("SimpleFunciona", "random-line.object")) as infile:
        obj = objects.ObjectFile.from_file(infile)

    polygon_list = []
    for car in obj['car in line']:
        for sub_structure in car:
            polygon_list.append(sub_structure.as_polygon())

    point = geometry.Point((1,1))
    #print(point.within(all_polygon))
    matrix = calc_position_matrix((633, 456, 663, 531), polygon_list)
    print(matrix[0])
    matrix_plot(matrix[1])
