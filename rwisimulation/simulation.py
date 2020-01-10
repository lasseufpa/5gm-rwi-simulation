'''
This code executes Sumo and InSite repeatedly.
'''
import sys
import os
import platform
import shutil
import argparse
import numpy as np
import logging
import json
import csv
try: #readline does not run on Windows. Use pyreadline instead
  import readline
except ImportError:
  import pyreadline as readline

import traci
from sumo import coord

from rwimodeling import insite, objects, txrx, X3dXmlFile, verticelist

import config as c
from .placement import place_on_line, place_by_sumo #use this option to run from command line
#from placement import place_on_line, place_by_sumo #use this option to run from within IntelliJ IDE and debug
if c.insite_version == '3.3':
    from rwimodeling import  X3dXmlFile3_3


def writeSUMOInfoIntoFile(sumoOutputInfoFileName, episode_i, scene_i, lane_boundary_dict, cars_with_antenna, fixedReceivers, use_pedestrians):
    '''Save as CSV text file some information obtained from SUMO for this specific scene.
    Note that all vehicles on the streets are retrieved from SUMO via traci, and the structure
    cars_with_antenna only helps to identify which are receivers (have antennas). If the simulation
    has fixed receivers, then cars_with_antenna will have at most 1 car.
    '''
    #veh_i = None

    # In Windows, the default 'newline' adds an empty line between each call of
    # csv.writerow, and it causes the other scripts to fail. So, for Windows it
    # is needed to change the default new line.
    if platform.system() == 'Windows':
        newline = ''
    elif platform.system() == 'Linux':
        newline = None

    receiverIndexCounter = 0 #initialize counter to provide unique index for each receiver
    if use_pedestrians:
        with open(sumoOutputInfoFileName[:-4] + 'Ped.txt', 'w', newline=newline) as csv_file:
            w = csv.writer(csv_file)
            # from http://sumo.dlr.de/wiki/TraCI/Person_Value_Retrieval
            header2 = 'episode_i,scene_i,receiverIndex,ped,ped_i,typeID,xinsite,yinsite,x3,y3,' + \
                        'angle,speed,length, width,waitTime,currentTime(ms)=' + \
                        str(traci.simulation.getCurrentTime()) + ',Ts(s)=' + str(c.sampling_interval)
            w.writerow([header2]) #make the string a list otherwise the function will print each character between commas
            for ped_i, ped in enumerate(traci.person.getIDList()):
                (x, y), angle, length, width, speed, typeID, waitTime = [f(ped) for f in [
                    traci.person.getPosition,
                    traci.person.getAngle, #Returns the angle of the named vehicle within the last step [degrees]
                    traci.person.getLength,
                    traci.person.getWidth,
                    traci.person.getSpeed, #Returns the speed of the named person within the last step [m/s]; error value: -1001
                    traci.person.getTypeID, #Returns the id of the type of the named vehicle
                    traci.person.getWaitingTime #Returns the waiting time [s]
                ]]
                xinsite, yinsite = traci.simulation.convertGeo(x, y)
                w.writerow([episode_i,scene_i,'-1',ped,ped_i,typeID,xinsite,yinsite,x,y,angle,speed,length, width ,waitTime])

    with open(sumoOutputInfoFileName, 'w', newline=newline) as csv_file:
        w = csv.writer(csv_file)

        header = 'episode_i,scene_i,receiverIndex,veh,veh_i,typeID,xinsite,yinsite,x3,y3,z3,' + \
                    'lane_id,angle,speed,length, width, height,distance,waitTime,currentTime(ms)=' + \
                    str(traci.simulation.getCurrentTime()) + ',Ts(s)=' + str(c.sampling_interval)

        w.writerow([header]) #make the string a list otherwise the function will print each character between commas

        # Fixed receivers - Marcus' workaround
        if fixedReceivers:
            lane_id = 0
            angle = 0
            speed = 0
            length = 0
            width = 0
            height = 0
            distance = 0
            waitTime = 0

            txrx_file = open(os.path.join(c.base_insite_project_path, 'base.txrx'), 'r')
            counter = 0
            cnt_rx = False
            Rx_info = False
            for line in txrx_file:
                if 'begin_<points> ' + c.insite_rx_name in line:
                    Rx_info = True
                    continue
                if 'nVertices' in line and Rx_info:
                    cnt_rx = int(line.split(' ')[1]) 
                    numOfFixedReceivers = cnt_rx
                    continue
                if cnt_rx:
                    x = line.split(' ')[0]
                    y = line.split(' ')[1]
                    z = line.split(' ')[2].replace('\n', '')
                    w.writerow([episode_i,scene_i,counter,'house'+str(counter), counter,'House',x,y,x,y,z,lane_id,angle,speed,length, width, height,distance,waitTime])
                    counter += 1
                    cnt_rx -= 1

        #from http://sumo.dlr.de/wiki/TraCI/Vehicle_Value_Retrieval
        for veh_i, veh in enumerate(traci.vehicle.getIDList()):
            (x, y), angle, lane_id, length, width, height, speed, (x3,y3,z3), typeID, distance, waitTime = [f(veh) for f in [
                traci.vehicle.getPosition,
                traci.vehicle.getAngle, #Returns the angle of the named vehicle within the last step [degrees]
                traci.vehicle.getLaneID,
                traci.vehicle.getLength,
                traci.vehicle.getWidth,
                traci.vehicle.getHeight,
                traci.vehicle.getSpeed, #Returns the speed of the named vehicle within the last step [m/s]; error value: -1001
                traci.vehicle.getPosition3D, #Returns the 3D-position(three doubles) of the named vehicle (center of the front bumper) within the last step [m,m,m]
                traci.vehicle.getTypeID, #Returns the id of the type of the named vehicle
                traci.vehicle.getDistance, #The distance, the vehicle has already driven [m]); error value: -1001
                traci.vehicle.getWaitingTime #Returns the waiting time [s]
            ]]

            #convert position from SUMO to InSite
            #xinsite, yinsite = coord.convert_distances(lane_id, (x,y), lane_boundary_dict=lane_boundary_dict)
            xinsite, yinsite = traci.simulation.convertGeo(x, y)

            #check if it's a receiver (has antenna) or not. Use -1 to identify it's not a receiver
            receiverIndex=-1
            if cars_with_antenna is None:
                continue
            if veh in cars_with_antenna:
                #to find unique index, I was initially doing
                #receiverIndex = int(np.where(cars_with_antenna == veh)[0])
                #but this is wrong, in fact later the code associates indices according to the order the vehicle
                #shows up in cars_with_antenna. Hence, I am using an auxiliary variable
                if not fixedReceivers: # FixedReceiver
                    receiverIndex = receiverIndexCounter #not -1, but the current Rx counter
                    receiverIndexCounter += 1 #update counter

            if fixedReceivers:
                w.writerow([episode_i,scene_i,receiverIndex,veh,veh_i+numOfFixedReceivers,typeID,xinsite,yinsite,x3,y3,z3,lane_id,angle,speed,length, width, height,distance,waitTime])
            else:
                w.writerow([episode_i,scene_i,receiverIndex,veh,veh_i,typeID,xinsite,yinsite,x3,y3,z3,lane_id,angle,speed,length, width, height,distance,waitTime])


def onlyDronesList(idList):
    for v_id, veh in enumerate(idList[:]):
        if not veh.startswith('dflow'):
            idList.remove(veh)
    return idList

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--place-only', action='store_true',
                        help='Run only the objects placement and save files for ray-tracing')
    parser.add_argument('-j', '--jump', action='store_true',
                        help='Jumping runs that already have results (works only if utilized with the option \'-r\' )')
    parser.add_argument('-r', '--ray-tracing-only', action='store_true',
                        help='Run only ray-tracing with previoulsy generated files')
    parser.add_argument('-c', '--run-calcprop', action='store_true',
                        help='Ray-tracing with InSite calcprop instead of the default wibatch')
    parser.add_argument('-s', '--pause-each-run', action='store_true',
                        help='Interactive run')
    parser.add_argument('-o', '--remove-results-dir', action='store_true',
                        help='ONLY IF YOU KNOW WHAT YOU ARE DOING: it will remove the whole results folder')
    args = parser.parse_args()

    #check consistency of user input
    if c.use_fixed_receivers:
        if c.n_antenna_per_episode != 0:
            print('ERROR: if use_fixed_receivers=True, n_antenna_per_episode must be 0 but it is', c.n_antenna_per_episode)
            raise Exception()

    #setup_path=c.setup_path, xml_path=c.dst_x3d_xml_path.replace(' ', '\ ')
    #AK: now the constructor has fewer parameters
    insite_project = insite.InSiteProject(project_name='model', calcprop_bin=c.calcprop_bin,
                                          wibatch_bin=c.wibatch_bin)

    print('########## Start simulation #############################')
    if args.ray_tracing_only:
        if args.run_calcprop:
            print('Option -r is not compatible with -c')
            exit(-1)
        print('Will run only ray-tracing. I am assuming all files have been placed.')
        for i in c.n_run:
            run_dir = os.path.join(c.results_dir, c.base_run_dir_fn(i))
            #Ray-tracing output folder (where InSite will store the results (Study Area name)).
            #They will be later copied to the corresponding output folder specified by results_dir
            project_output_dir = os.path.join(run_dir, c.insite_study_area_name) #output InSite folder

            p2mpaths_file = os.path.join(project_output_dir, c.insite_setup_name + '.paths.t001_01.r002.p2m')
            if not os.path.exists(p2mpaths_file) or args.remove_results_dir:
                xml_full_path = os.path.join(run_dir, c.dst_x3d_xml_file_name) #input InSite folder
                xml_full_path=xml_full_path.replace(' ', '\ ')
                insite_project.run_x3d(xml_full_path, project_output_dir)
            elif os.path.exists(p2mpaths_file) and args.jump:
                continue
            else: 
                print("ERROR: " + p2mpaths_file + " already exists, aborting simulation!") 
                raise Exception()

        print('Finished running ray-tracing')
        exit(1)

    #copy files from initial (source folder) to results base folder
    try:
        shutil.copytree(c.base_insite_project_path, c.results_base_model_dir, )
    except FileExistsError:
        if args.remove_results_dir:
            shutil.rmtree(c.results_dir)
            print('Removed folder',c.results_dir)
            shutil.copytree(c.base_insite_project_path, c.results_base_model_dir, )
        else:
            print('### ERROR: folder / file exists:',c.results_base_model_dir)
            raise FileExistsError
    print('Copied folder ',c.base_insite_project_path,'into',c.results_base_model_dir)

    #open InSite files that are used as the base to create each new scene / simulation
    with open(c.base_object_file_name) as infile:
        objFile = objects.ObjectFile.from_file(infile)
    print('Opened file with objects:', c.base_object_file_name)
    with open(c.base_txrx_file_name) as infile:
        txrxFile = txrx.TxRxFile.from_file(infile)
    print('Opened file with transmitters and receivers:', c.base_txrx_file_name)
    if c.insite_version == '3.3':
        x3d_xml_file = X3dXmlFile3_3(c.base_x3d_xml_path)
    else:
        x3d_xml_file = X3dXmlFile(c.base_x3d_xml_path)
    print('Opened file with InSite XML:', c.base_x3d_xml_path)

    #AK-TODO document and comment the methods below.
    car = objects.RectangularPrism(*c.car_dimensions, material=c.car_material_id)
    car_structure = objects.Structure(name=c.car_structure_name) #AK-TODO what is the role of c.car_structure_name ?
    car_structure.add_sub_structures(car)
    car_structure.dimensions = car.dimensions

    antenna = txrxFile[c.antenna_points_name].location_list[0]

    if c.use_sumo:
        print('Starting SUMO Traci')
        traci.start(c.sumo_cmd)

    scene_i = None
    episode_i = None

    # Trick to start simulations from a given run as it was started from 0
    if c.n_run[0] != 0:
        tmp_var = 0
        while (tmp_var < int(c.n_run[0])):
            if c.use_sumo:
                # when to start a new episode
                if scene_i is None or scene_i >= c.time_of_episode:
                    #first scene of an episode
                    if episode_i is None:
                        episode_i = 0
                    else:
                        episode_i += 1
                    scene_i = 0
                    # step time_between_episodes from the last one
                    for count in range(c.time_between_episodes):
                        traci.simulationStep()

                    traci_vehicle_IDList = traci.vehicle.getIDList()
                    # Filter list to have only drones
                    if c.drone_simulation: 
                        traci_vehicle_IDList = onlyDronesList(traci.vehicle.getIDList())
                    while len(traci_vehicle_IDList) < c.n_antenna_per_episode:
                        traci_vehicle_IDList = traci.vehicle.getIDList()
                        if c.drone_simulation: 
                            traci_vehicle_IDList = onlyDronesList(traci.vehicle.getIDList())

                        logging.warning('not enough vehicles at time ' + str(traci.simulation.getCurrentTime()) )
                        traci.simulationStep()
                    cars_with_antenna = np.random.choice(traci_vehicle_IDList, c.n_antenna_per_episode, replace=False)
                else:
                    traci.simulationStep()
                scene_i += 1 #update scene counter
            tmp_var += 1
            print('Jump until the step '+ str(c.n_run[0]) + ': '+ str(int((tmp_var/c.n_run[0])* 100))+ '%')

    count_nar = 0 # Number of Runs without cars with antenna while mobile
    for i in c.n_run:

        run_dir = os.path.join(c.results_dir, c.base_run_dir_fn(i - count_nar))
        #Ray-tracing output folder (where InSite will store the results (Study Area name)).
        #They will be later copied to the corresponding output folder specified by results_dir
        project_output_dir = os.path.join(run_dir, c.insite_study_area_name) #output InSite folder

        #Disabled below because the paths will be created later on by shutil.copytree
        #and shutil.copytree does not support folders that already exist
        #if not os.path.exists(run_dir):
        #os.makedirs(run_dir)

        objFile.clear()

        #if it's the beginning of the episode, the code searches for a minimium number of cars. After the
        #episode starts, then it does not do that. But it does not simulate scenarios without vehicles
        if c.use_sumo:
            # when to start a new episode
            if scene_i is None or scene_i >= c.time_of_episode:
                #first scene of an episode
                if episode_i is None:
                    episode_i = 0
                else:
                    episode_i += 1
                scene_i = 0
                # step time_between_episodes from the last one
                for count in range(c.time_between_episodes): #AK-TODO should rename it and avoid calling "time"
                    traci.simulationStep()
                if c.use_fixed_receivers:
                    cars_with_antenna = []
                else:
                    # ensure that there enough cars to place antennas. If use_fixed_receivers, then wait to have at least
                    # one vehicle

                    traci_vehicle_IDList = traci.vehicle.getIDList()
                    # Filter list to have only drones
                    if c.drone_simulation: 
                        traci_vehicle_IDList = onlyDronesList(traci.vehicle.getIDList())
                    while len(traci_vehicle_IDList) < c.n_antenna_per_episode:
                        traci_vehicle_IDList = traci.vehicle.getIDList()
                        if c.drone_simulation: 
                            traci_vehicle_IDList = onlyDronesList(traci.vehicle.getIDList())
                        logging.warning('not enough vehicles at time ' + str(traci.simulation.getCurrentTime()) )
                        traci.simulationStep()
                    cars_with_antenna = np.random.choice(traci_vehicle_IDList, c.n_antenna_per_episode, replace=False)

            else:
                traci.simulationStep()

            structure_group, location, str_vehicles = place_by_sumo(
                antenna, c.car_material_id, lane_boundary_dict=c.lane_boundary_dict,
                cars_with_antenna=cars_with_antenna,
                use_fixed_receivers = c.use_fixed_receivers,
                use_pedestrians = c.use_pedestrians)
            print(traci.simulation.getCurrentTime())

            #if location is None:  #there are not cars with antennas in this episode (all have left)
            #    print('BBBBBBBBBUg')
            # no vehicles in the environment (not only the ones without antennas, but no vehicles at all)
            if traci.vehicle.getIDList() is None:
                logging.warning("No vehicles in scene " + str(scene_i) + " time " + str(traci.simulation.getCurrentTime()))
                os.makedirs(run_dir + '_novehicles') #create an empty folder to "indicate" the situation
                #save SUMO information for this scene as text CSV file
                #sumoOutputInfoFileName = os.path.join(run_dir,'sumoOutputInfoFileName_novehicles.txt')
                #writeSUMOInfoIntoFile(sumoOutputInfoFileName, episode_i, scene_i, c.lane_boundary_dict, cars_with_antenna)
                scene_i += 1 #update scene counter
                continue

            if location is None:  #there are not cars with antennas in this episode (all have left)
                if not c.use_fixed_receivers:
                    count_nar = count_nar + 1
                    #abort, there is not reason to continue given that there will be no receivers along the whole episode
                    logging.warning("No vehicles with antennas in scene " + str(scene_i) + " time " + str(traci.simulation.getCurrentTime()))
                    os.makedirs(run_dir + '_noAntennaVehicles') #create an empty folder to "indicate" the situation
                    scene_i = np.Infinity #update scene counter
                    continue
        else: #in case we should not use SUMO to position vehicles, then get a fixed position
            structure_group, location = place_on_line(c.line_origin, c.line_destination, c.line_dimension,
                  c.car_distances, car_structure, antenna, c.antenna_origin)

        #Prepare the files for the input folder, where InSite will find them to execute the simulation
        #(obs: now InSite is writing directly to the output folder)
        shutil.copytree(c.base_insite_project_path, run_dir)
        print('Copied',c.base_insite_project_path,'into',run_dir)

        #Writing to the final run folder
        objFile.add_structure_groups(structure_group)
        dst_object_full_path = os.path.join(run_dir, c.dst_object_file_name)
        objFile.write(dst_object_full_path)

        #write new model of vehicles to the final folder
        if c.use_vehicles_template:
            dst_new_object_full_path = os.path.join(run_dir, c.insite_vehicles_name_model + '.object')
            f_dst_new_object = open(dst_new_object_full_path,'w')
            f_dst_new_object.write(str_vehicles)
            f_dst_new_object.close()

        #get name of XML
        xml_full_path = os.path.join(run_dir, c.dst_x3d_xml_file_name) #input InSite folder
        xml_full_path=xml_full_path.replace(' ', '\ ')

        if not c.use_fixed_receivers: #Marcus' workaround
            x3d_xml_file.add_vertice_list(location, c.dst_x3d_txrx_xpath)
            x3d_xml_file.write(xml_full_path)

            txrxFile[c.antenna_points_name].location_list[0] = location
            # txrx modified in the RWI project
            dst_txrx_full_path = os.path.join(run_dir, c.dst_txrx_file_name)
            txrxFile.write(dst_txrx_full_path)

        #check if we should run ray-tracing
        if not args.place_only:
            if args.run_calcprop:
                #AK-TODO: Need to fix run_calcprop in insite.py: should not copy unless necessary (need to check)
                insite_project.run_calcprop(output_dir=project_output_dir, delete_temp=True)
            else:
                insite_project.run_x3d(xml_full_path, project_output_dir)

        with open(os.path.join(run_dir, c.simulation_info_file_name), 'w') as infofile:
            #if c.use_fixed_receivers:  #AK-TODO take in account fixed receivers
            #    listToBeSaved = list('only_fixed_receivers')
            #else:
            listToBeSaved = list(cars_with_antenna)
            info_dict = dict(
                    cars_with_antenna=listToBeSaved,
                    scene_i=scene_i,
            )
            json.dump(info_dict, infofile) #write JSON infofile

        #save SUMO information for this scene as text CSV file
        sumoOutputInfoFileName = os.path.join(run_dir,'sumoOutputInfoFileName.txt')
        writeSUMOInfoIntoFile(sumoOutputInfoFileName, episode_i, scene_i, c.lane_boundary_dict, cars_with_antenna, c.use_fixed_receivers, c.use_pedestrians)

        scene_i += 1 #update scene counter

        if args.pause_each_run:
            input('Enter to step')
            sys.stdin.readline()

    traci.close()

if __name__ == '__main__':
    main()
