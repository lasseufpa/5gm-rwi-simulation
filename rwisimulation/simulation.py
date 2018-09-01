'''
This code executes Sumo and InSite repeatedly.
'''
import sys
import os
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
from .placement import place_on_line, place_by_sumo
#from placement import place_on_line, place_by_sumo #use this option to run from within IntelliJ IDE


def writeSUMOInfoIntoFile(sumoOutputInfoFileName, episode_i, scene_i, lane_boundary_dict, cars_with_antenna):
    '''Save as CSV text file some information obtained from SUMO for this specific scene'''
    veh_i = None
    receiverIndexCounter = 0 #initialize counter to provide unique index for each receiver
    with open(sumoOutputInfoFileName, 'a') as csv_file:
        w = csv.writer(csv_file)
        header = 'episode_i,scene_i,receiverIndex,veh,veh_i,typeID,xinsite,yinsite,x3,y3,z3,' + \
                    'lane_id,angle,speed,length, width, height,distance,waitTime,currentTime(ms)=' + \
                    str(traci.simulation.getCurrentTime()) + ',Ts(s)=' + str(c.sampling_interval)
        w.writerow([header]) #make the string a list otherwise the function will print each character between commas
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
            xinsite, yinsite = coord.convert_distances(lane_id, (x,y), lane_boundary_dict=lane_boundary_dict)

            #check if it's a receiver (has antenna) or not. Use -1 to identify it's not a receiver
            receiverIndex=-1
            if cars_with_antenna is None:
                continue
            if veh in cars_with_antenna:
                #to find unique index, I was initially doing
                #receiverIndex = int(np.where(cars_with_antenna == veh)[0])
                #but this is wrong, in fact later the code associates indices according to the order the vehicle
                #shows up in cars_with_antenna. Hence, I am using an auxiliary variable
                receiverIndex = receiverIndexCounter #not -1, but the current Rx counter
                receiverIndexCounter += 1 #update counter

            w.writerow([episode_i,scene_i,receiverIndex,veh,veh_i,typeID,xinsite,yinsite,x3,y3,z3,lane_id,angle,speed,length, width, height,distance,waitTime])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--place-only', action='store_true',
                        help='Run only the objects placement')
    parser.add_argument('-c', '--run-calcprop', action='store_true',
                        help='Run using calcprop')
    parser.add_argument('-s', '--pause-each-run', action='store_true',
                        help='Interactive run')
    parser.add_argument('-o', '--remove-results-dir', action='store_true',
                        help='ONLY IF YOU KNOW WHAT YOU ARE DOING')
    args = parser.parse_args()

    insite_project = insite.InSiteProject(setup_path=c.setup_path, xml_path=c.dst_x3d_xml_path.replace(' ', '\ '),
                                          output_dir=c.project_output_dir, calcprop_bin=c.calcprop_bin,
                                          wibatch_bin=c.wibatch_bin)

    with open(c.base_object_file_name) as infile:
        objFile = objects.ObjectFile.from_file(infile)
    with open(c.base_txrx_file_name) as infile:
        txrxFile = txrx.TxRxFile.from_file(infile)
    x3d_xml_file = X3dXmlFile(c.base_x3d_xml_path)

    car = objects.RectangularPrism(*c.car_dimensions, material=c.car_material_id)
    car_structure = objects.Structure(name=c.car_structure_name)
    car_structure.add_sub_structures(car)
    car_structure.dimensions = car.dimensions

    antenna = txrxFile[c.antenna_points_name].location_list[0]

    try:
        shutil.copytree(c.base_insite_project_path, c.results_base_model_dir, )
    except FileExistsError:
        shutil.rmtree(c.results_dir)
        shutil.copytree(c.base_insite_project_path, c.results_base_model_dir, )

    if c.use_sumo:
        traci.start(c.sumo_cmd)

    scene_i = None
    episode_i = None
    for i in c.n_run:
        run_dir = os.path.join(c.results_dir, c.base_run_dir_fn(i))
        #Disabled below because the paths will be created later on by shutil.copytree
        #and shutil.copytree does not support folders that already exist
        #if not os.path.exists(run_dir):
        #os.makedirs(run_dir)

        objFile.clear()

        if c.use_sumo:

            # when to start a new episode
            if scene_i is None or scene_i >= c.time_of_episode:
                if episode_i is None:
                    episode_i = 0
                else:
                    episode_i += 1
                scene_i = 0
                # step time_between_episodes from the last one
                for count in range(c.time_between_episodes):
                    traci.simulationStep()
                # ensure that there enough cars to place antennas
                while len(traci.vehicle.getIDList()) < c.n_antenna_per_episode:
                    logging.error('not enough cars')
                    traci.simulationStep()
                cars_with_antenna = np.random.choice(traci.vehicle.getIDList(), c.n_antenna_per_episode, replace=False)
            else:
                traci.simulationStep()

            structure_group, location = place_by_sumo(
                antenna, c.car_material_id, lane_boundary_dict=c.lane_boundary_dict,
                cars_with_antenna=cars_with_antenna)
            print(traci.simulation.getCurrentTime())
            # no cars in the environment
            if location is None:
                logging.error("all antennas are out of the simulation, aborting episode")
                scene_i = np.inf
                continue

        else:
            structure_group, location = place_on_line(c.line_origin, c.line_destination, c.line_dimension,
                  c.car_distances, car_structure, antenna, c.antenna_origin)

        objFile.add_structure_groups(structure_group)
        objFile.write(c.dst_object_file_name)
        #shutil.copy(c.dst_object_file_name, run_dir)

        x3d_xml_file.add_vertice_list(location, c.dst_x3d_txrx_xpath)
        x3d_xml_file.write(c.dst_x3d_xml_path)
        #shutil.copy(c.dst_x3d_xml_path, run_dir)

        txrxFile[c.antenna_points_name].location_list[0] = location
        txrxFile.write(c.dst_txrx_file_name)
        #shutil.copy(c.dst_txrx_file_name, run_dir)

        if not args.place_only:
            insite_project.run_x3d(output_dir=c.project_output_dir)

        if not args.place_only and args.run_calcprop:
            insite_project.run_calcprop(output_dir=run_dir, delete_temp=True)

        shutil.copytree(c.base_insite_project_path, run_dir)

        with open(os.path.join(run_dir, c.simulation_info_file_name), 'w') as infofile:
            info_dict = dict(
                cars_with_antenna=list(cars_with_antenna),
                scene_i=scene_i,
            )
            json.dump(info_dict, infofile)

        #save SUMO information for this scene as text CSV file
        sumoOutputInfoFileName = os.path.join(run_dir,'sumoOutputInfoFileName.txt')
        writeSUMOInfoIntoFile(sumoOutputInfoFileName, episode_i, scene_i, c.lane_boundary_dict, cars_with_antenna)

        scene_i += 1 #update scene counter

        if args.pause_each_run:
            input('Enter to step')
            sys.stdin.readline()

    traci.close()

if __name__ == '__main__':
    main()