import copy
import os

import numpy as np

from rwimodeling import errors, objects, txrx


def place_on_line(origin, destination, dim, space, object,
                  antenna=None, antenna_origin=None):
    """ Place object in a line separated by space

    :param origin: (x, y, z)
    :param destination: the maximum coordinate of the line
    :param dim: 0, 1, 2 for x, y or z
    :param space: function that return the space between `object`
    :param object: a RWI Structure with "origin" in (0, 0, 0) (must have a valid dimension)
    :param antanna_origin: (x, y, z) normally "inside" the object
    :param antenna: VerticeList
    :return: a structure group
    """

    origin = np.array(origin)
    if object.dimensions is None:
        raise errors.FormatError('"{}" has no dimensions'.format(object))

    structure_group = objects.StructureGroup()
    structure_group.name = object.name + ' in line'

    if antenna is not None:
        vertice_list = copy.deepcopy(antenna)
        vertice_list.clear()
        if antenna_origin is None:
            vertice_list_origin = np.array(0, 0, 0)
        else:
            vertice_list_origin = np.array(antenna_origin)


    # position on `dim` accounting for all `object` and `space` placed
    last_obj_loc = origin[dim]
    n_obj = 0
    while True:
        # no more objects fit (last could be the space)
        if last_obj_loc >= destination:
            break
        # check if object fit
        if object.dimensions[dim] + last_obj_loc >= destination:
            break
        # the object to be added
        new_object = copy.deepcopy(object)
        new_object.name += '{:03d}'.format(n_obj)
        # the origin of the new object
        new_object_origin = origin
        new_object_origin[dim] = last_obj_loc
        # move object to the new origin
        new_object.translate(new_object_origin)
        if antenna is not None:
            vertice_list.add_vertice(new_object_origin + vertice_list_origin)
        # add the new object to the structure group
        structure_group.add_structures(new_object)
        # where new objects should be placed
        last_obj_loc = new_object_origin[dim] + new_object.dimensions[dim] + space()
        n_obj += 1
    if antenna is not None:
        return structure_group, vertice_list
    else:
        return structure_group

if __name__=='__main__':

    with open(os.path.join("SimpleFunciona", "base.object")) as infile:
        obj = objects.ObjectFile.from_file(infile)
    with open(os.path.join('SimpleFunciona', 'base.txrx')) as infile:
        txrxFile = txrx.TxRxFile.from_file(infile)
    obj.clear()

    car = objects.RectangularPrism(1.76, 4.54, 1.47, material=0)
    car_structure = objects.Structure(name="car")
    car_structure.add_sub_structures(car)
    car_structure.dimensions = car.dimensions

    city_origin = np.array((648, 456, 0.2))
    antenna_origin = np.array((car.height / 2, car.width / 2, car.height))
    antenna = txrxFile['Rx'].location_list[0]

    structure_group, location = place_on_line(
        city_origin, 531, 1, lambda: np.random.uniform(1, 3), car_structure, antenna, antenna_origin)
    obj.add_structure_groups(structure_group)
    obj.write(os.path.join("SimpleFunciona", "random-line.object"))

    txrxFile['Rx'].location_list[0] = location
    txrxFile.write(os.path.join('SimpleFunciona', 'model.txrx'))