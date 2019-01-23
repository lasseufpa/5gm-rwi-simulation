import copy
import os

import numpy as np

import traci

from rwimodeling import errors, objects, txrx, X3dXmlFile

from sumo import coord

import config as c

if c.use_vehicles_template:
    from Cheetah.Template import Template
    import vehicles_template as vt


#def place_by_sumo(antenna, car_material_id, lane_boundary_dict, cars_with_antenna=None):
def place_by_sumo(antenna, car_material_id, lane_boundary_dict, cars_with_antenna, use_fixed_receivers=False, use_pedestrians=False):
    antenna = copy.deepcopy(antenna)
    antenna.clear()

    structure_group = objects.StructureGroup()
    structure_group.name = 'SUMO cars'

    str_vehicles = ''
    veh_i = None
    c_present = False
    if use_pedestrians:
        for ped_i, ped in enumerate(traci.person.getIDList()):
            (x, y), angle, length, width = [f(ped) for f in [
                traci.person.getPosition,
                traci.person.getAngle, #Returns the angle of the named vehicle within the last step [degrees]
                traci.person.getLength,
                traci.person.getWidth
            ]]
            xinsite, yinsite = traci.simulation.convertGeo(x, y)
            pedestrian = objects.RectangularPrism(length, width, 1.72, material=car_material_id)
            pedestrian.translate((-length/2, -width/2, 0))
            pedestrian.rotate(90-angle) #use 90 degrees - angle to convert from y to x-axis the reference

            thisAngleInRad = np.radians(angle) #*np.pi/180
            deltaX = (length/2.0) * np.sin(thisAngleInRad)
            deltaY = (length/2.0) * np.cos(thisAngleInRad)
            pedestrian.translate((xinsite-deltaX, yinsite-deltaY, 0)) #now can translate

            pedestrian_structure = objects.Structure(name=ped)
            pedestrian_structure.add_sub_structures(pedestrian)
            structure_group.add_structures(pedestrian_structure)

            # 1.72 size of a perdestrian
            if c.use_vehicles_template:
                str_vehicles = get_model(str_vehicles,ped,xinsite-deltaX,yinsite-deltaY,0,90-angle,1.72) 

    for veh_i, veh in enumerate(traci.vehicle.getIDList()):
        (x, y), (x3,y3,z3), angle, lane_id, length, width, height = [f(veh) for f in [
            traci.vehicle.getPosition,
            traci.vehicle.getPosition3D, #Returns the 3D-position(three doubles) of the named vehicle (center of the front bumper) within the last step [m,m,m]
            traci.vehicle.getAngle,
            traci.vehicle.getLaneID,
            traci.vehicle.getLength,
            traci.vehicle.getWidth,
            traci.vehicle.getHeight
        ]]

        #x, y = coord.convert_distances(lane_id, (x,y), lane_boundary_dict=lane_boundary_dict)
        x, y = traci.simulation.convertGeo(x, y)
        #x2, y2 = traci.simulation.convertGeo(lon, lat, fromGeo=True)

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
        car.translate((x-deltaX, y-deltaY, z3)) #now can translate

        car_structure = objects.Structure(name=veh)
        car_structure.add_sub_structures(car)
        structure_group.add_structures(car_structure)

        if c.use_vehicles_template:
            str_vehicles = get_model(str_vehicles,veh,x-deltaX,y-deltaY,z3,90-angle,height,length,width) 

        #antenna_vertice
        if veh in cars_with_antenna:
            c_present = True
            #translate the antenna as the vehicle. Note the antenna is not rotated (we are using isotropic anyways)
            #adding Rx 0.1 above car's height, to ensure that it will not be blocked by the vehicle itself
            antenna.add_vertice((x-deltaX, y-deltaY, z3+height+0.1))


    if c.use_vehicles_template:
        all_vehicles = str(vt.vehicles_template(searchList=[{'a':str_vehicles,'long':c.longitude,'lat':c.latitude}]))
    else:
        all_vehicles = ''
    if use_fixed_receivers:
        return structure_group, None, all_vehicles

    if not c_present: #there are no vehicles with antennas
        return None, None, None

    if veh_i is None: #there are no vehicles in the scene according to SUMO (traci)
        return None, None, None

    return structure_group, antenna, all_vehicles


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

def rotate(vertice, angle):
    """Rotate counterclockwise by a given angle around a given origin.
    The angle should be given in degrees.
    """
    angle = np.radians(angle)

    c = np.cos(angle)
    s = np.sin(angle)
    rot_mat = np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])

    vertice_array = np.matmul(rot_mat, vertice)

    return vertice_array

def get_model(str_vehicles,name,x,y,z,angle,height,length=1,width=1):

    # The height here is utilized as trick to choose which model will be utilized .
    # TODO: Find a new way to classify the models, instead of height.
    if (height == 4.3):
        model_object = open(os.path.join(c.working_directory,'objects/truck.object'), 'r')
    elif (height == 3.2):               
        model_object = open(os.path.join(c.working_directory,'./objects/bus.object'), 'r')
    elif (height == 1.59):              
        model_object = open(os.path.join(c.working_directory,'./objects/car.object'), 'r')
    elif (height == 1.72):              
        model_object = open(os.path.join(c.working_directory,'./objects/pedestrian.object'), 'r')
    elif (height == 0.295): 
        model_object = open(os.path.join(c.working_directory,'./objects/drone.object'), 'r')
    else:
        print('There is no model object ready for this object')
        exit(1)

    cn_points = False
    
    for line in model_object:
        if 'begin_<structure_group>' in line:
            tmp = line.split(' ')
            tmp[1] = str(name+ ' ')
            line = ' '.join(tmp)
            str_vehicles += line + "\n"
            continue
        if 'nVertices' in line:
            cn_points = int(line.split(' ')[1]) 
            str_vehicles += line
            continue
        if cn_points:
            tmp = line.split(' ')
            tmp[0] = float(tmp[0])
            tmp[1] = float(tmp[1])
            tmp[2] = float(tmp[2])
            myarray = np.asarray(tmp)
            rotated_v = list(rotate(myarray,angle))
            rotated_v[0] = str(rotated_v[0] + x)
            rotated_v[1] = str(rotated_v[1] + y)
            rotated_v[2] = str(rotated_v[2] + z) + "\n"
            line = ' '.join(rotated_v)
            cn_points -= 1
        str_vehicles += line

    return str_vehicles

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
