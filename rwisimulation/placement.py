import copy
import os

import numpy as np

import traci

from rwimodeling import errors, objects, txrx, X3dXmlFile

from sumo import coord


#def place_by_sumo(antenna, car_material_id, lane_boundary_dict, cars_with_antenna=None):
def place_by_sumo(antenna, car_material_id, lane_boundary_dict, cars_with_antenna, use_fixed_receivers=False):
    antenna = copy.deepcopy(antenna)
    antenna.clear()

    structure_group = objects.StructureGroup()
    structure_group.name = 'SUMO cars'

    veh_i = None
    c_present = False
    for veh_i, veh in enumerate(traci.vehicle.getIDList()):
        (x, y), angle, lane_id, length, width, height = [f(veh) for f in [
            traci.vehicle.getPosition,
            traci.vehicle.getAngle,
            traci.vehicle.getLaneID,
            traci.vehicle.getLength,
            traci.vehicle.getWidth,
            traci.vehicle.getHeight
        ]]

        x, y = coord.convert_distances(lane_id, (x,y), lane_boundary_dict=lane_boundary_dict)

        #the prism is draw using the first coordinate aligned with x, then y and z. Length is initially along x
        #and later the object will be rotates
        car = objects.RectangularPrism(length, width, height, material=car_material_id)

        #for proper rotation, first centralize the object on plane xy
        car.translate((-length/2, -width/2, 0))
        #now can rotate, but note SUMO assumes y-axis as the reference, and angle increases towards x-axis,
        #while we assume angles start from x-axis in our rotate method (see https://en.wikipedia.org/wiki/Rotation_matrix)
        car.rotate(90-angle) #use 90 degrees - angle to convert from y to x-axis the reference

        #SUMO reports position of middle of front bumper. We need to reposition to the middle of the vehicle
        #for that, use the angle to find to where the vehicle is facing and then translate
        thisAngleInRad = np.radians(angle) #*np.pi/180
        deltaX = (length/2.0) * np.sin(thisAngleInRad)
        deltaY = (length/2.0) * np.cos(thisAngleInRad)
        car.translate((x-deltaX, y-deltaY, 0)) #now can translate

        car_structure = objects.Structure(name=veh)
        car_structure.add_sub_structures(car)
        structure_group.add_structures(car_structure)

        #antenna_vertice
        #if cars_with_antenna is None or veh in cars_with_antenna:
            #translate the antenna as the vehicle. Note the antenna is not rotated (we are using isotropic anyways)
            #antenna.add_vertice((x-deltaX, y-deltaY, height))
        #AK-TODO: not sure why Pedro checks cars_with_antenna is None. It seems it will add arbitrary cars
        #if cars_with_antenna is None or veh in cars_with_antenna:
        if veh in cars_with_antenna:
            c_present = True
            #translate the antenna as the vehicle. Note the antenna is not rotated (we are using isotropic anyways)
            antenna.add_vertice((x-deltaX, y-deltaY, height))

    if use_fixed_receivers:
        return structure_group, None

    if not c_present: #there are no vehicles with antennas
        return None, None

    if veh_i is None: #there are no vehicles in the scene according to SUMO (traci)
        return None, None

    return structure_group, antenna


def place_on_line(origin_array, destination_list, dim_list, space, object,
                  antenna=None, antenna_origin=None):
    """ Place object in a line separated by space

    :param origin_array: (x, y, z) or ((x, y, z),)
    :param destination_list: scalar or list the maximum coordinate of the line
    :param dim_list: 0, 1, 2 for x, y or z (one or list of)
    :param space: function that return the space between `object`
    :param object: a RWI Structure with "origin" in (0, 0, 0) (must have a valid dimension)
    :param antanna_origin: (x, y, z) normally "inside" the object
    :param antenna: VerticeList
    :return: a structure group
    """

    origin_array = np.array(origin_array, ndmin=2)
    n_lines = origin_array.shape[0]
    destination_list = np.array(destination_list, ndmin=1)
    dim_list = np.array(dim_list, ndmin=1)
    # if a list of destination and dim is not provided but a list of origin is,
    # assumes the same destination and dim for all origins
    if len(destination_list) == 1:
        destination_list = np.repeat(destination_list, n_lines)
    if len(dim_list) == 1:
        dim_list = np.repeat(dim_list, n_lines)
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

    obj_i = 0

    for origin, destination, dim in zip(origin_array, destination_list, dim_list):
        # position on `dim` accounting for all `object` and `space` placed
        last_obj_loc = origin[dim]
        while True:
            # no more objects fit (last could be the space)
            if last_obj_loc >= destination:
                break
            # check if object fit
            if object.dimensions[dim] + last_obj_loc >= destination:
                break
            # the object to be added
            new_object = copy.deepcopy(object)
            new_object.name += '{:03d}'.format(obj_i)
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
            obj_i += 1
    if antenna is not None:
        return structure_group, vertice_list
    else:
        return structure_group

if __name__ == '__main__':
    import sys
    print(sys.path)
    import config as c

    with open(os.path.join("example", "SimpleFunciona", "base.object")) as infile:
        obj = objects.ObjectFile.from_file(infile)

    x3d_xml = X3dXmlFile(os.path.join("example", "SimpleFunciona", "model.Study.xml"))

    with open(os.path.join("example", 'SimpleFunciona', 'base.txrx')) as infile:
        txrxFile = txrx.TxRxFile.from_file(infile)
    obj.clear()

    car = objects.RectangularPrism(1.76, 4.54, 1.47, material=0)
    car_structure = objects.Structure(name="car")
    car_structure.add_sub_structures(car)
    car_structure.dimensions = car.dimensions

    city_origin = np.array((648, 456, 0.2))
    antenna_origin = np.array((car.height / 2, car.width / 2, car.height))
    vertice_list = txrxFile['Rx'].location_list[0]

    structure_group, placed_vertice_list = place_on_line(
        city_origin, 531, 1, lambda: np.random.uniform(1, 3), car_structure, vertice_list, antenna_origin)
    obj.add_structure_groups(structure_group)
    obj.write(os.path.join('example', "SimpleFunciona", "random-line.object"))

    x3d_xml.add_vertice_list(placed_vertice_list, c.dst_txrx_xpath)
    x3d_xml.write(os.path.join("example", "SimpleFunciona", 'gen.study.xml'))

    txrxFile['Rx'].location_list[0] = placed_vertice_list
    txrxFile.write(os.path.join('example', 'SimpleFunciona', 'model.txrx'))