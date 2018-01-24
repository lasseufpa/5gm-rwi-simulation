import os

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


def calc_position_matrix(bounds, polygon_list, resolution=1):
    """Represents the receivers and other objects in a position matrix

    :param bounds: (minx, miny, maxx, maxy) of the region to study
    :param polygon_list: a list of polygons
    :param resolution: size of the pixel (same unity as bounds, default meters)
    :return: a matrix with shape (len(polygon_list), (maxx - minx) / resolution, (maxy - miny) / resolution)
    each point in the matrix[polygon_i] is a "pixel", the pixel is 1 when inside any polygon;
    2 when inside polygon_i; and 0 otherwise
    """
    n_polygon = len(polygon_list)
    all_polygons = geometry.MultiPolygon(polygon_list)
    bounds = np.array(bounds).reshape(2,2)
    # shape each "image"
    shape = ((bounds[1] - bounds[0]) / resolution).astype(np.int)
    # add n_polygon as first dimension
    shape = np.concatenate((np.array(n_polygon, ndmin=1), shape))
    matrix = np.zeros(shape, dtype=np.uint8)
    for i in range(matrix.shape[1]):
        for j in range(matrix.shape[2]):
            # create the point starting in (0, 0) with resolution "1"
            point_np = np.array((i, j))
            # apply the resolution and translate to the "area of interest"
            point_np = (point_np * resolution) + bounds[0]
            point = geometry.Point(point_np)
            #point = affinity.translate(
            #    geometry.Point(point_np),
            #    *bounds[0])
            if point.within(all_polygons):
                matrix[:,i,j] = 1
                for polygon_i, polygon in enumerate(polygon_list):
                    if point.within(polygon):
                        matrix[polygon_i,i,j] = 2
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
