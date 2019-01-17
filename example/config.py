'''
Several simulation parameters are defined here.
'''
import os
import itertools
import numpy as np
import socket
try:
    import tensorflow as tf
except ImportError:
    tf = None
try:
    from rwisimulation.positionmatrix import position_matrix_per_object_shape
except ImportError:
    position_matrix_per_object_shape = None
import logging
logging.basicConfig(level=logging.DEBUG)

def get_lat_long(base_insite_project_path):
    txrx_file = open(os.path.join(base_insite_project_path, 'base.txrx'), 'r')
    latitude = False
    longitude = False
    for line in txrx_file:
        if 'latitude' in line:
            latitude = line.split(' ')[1].replace('\n','') 
        if 'longitude' in line:
            longitude = line.split(' ')[1].replace('\n','') 
        if latitude and longitude:
            return latitude,longitude


###############################################################
## Most information in this configuration file is used in the Stage 1 of 
## the three stages below. But some are also used in the other stages.
## Stage 1: Running the ray-tracing (RT) and traffic simulators
## Stage 2: Organizing raw data into a 5GMdata database
## Stage 3: Converting the database into a file suitable to machine learning packages such as Keras
## This file is split into two parts. In most cases Part II is not modified.
###############################################################

###############################################################
## Part I - Basic information that typically needs to be modified / checked
###############################################################
use_fixed_receivers = True #set to False if only vehicles are receivers
use_pedestrians = True
use_vehicles_template = True # set True to use pre-made vehicle ( not boxes )
# Current folder (or directory). Some paths are relative to this folder:
working_directory = os.path.dirname(os.path.realpath(__file__)) 
# InSite will look for input files in this folder. These files will be used to generate all simulations
if False:
    base_insite_project_path = 'D:/insitedata/insite_new_simuls/'
else:
    base_insite_project_path = os.path.join(working_directory,'bases_insite_3_2_0/longtan/2.8GHz')
#Folder to store each InSite project and its results (will create subfolders for each "run", run0000, run0001, etc.)
results_dir = os.path.join(working_directory, 'simulations/longtan2')
#Folders and files for InSite and its license. For Windows you may simply inform
#the path to the executable files, not minding about the license file location.
#Folders for SUMO and InSite. Use executable sumo-gui if want to see the GUI or sumo otherwise


insite_version = '3.2'
if insite_version == '3.3':
    sumo_bin = '/usr/bin/sumo'
    calcprop_bin = ('REMCOMINC_LICENSE_FILE=2508@200.239.93.26 ' +
                    'LD_LIBRARY_PATH=/home/psb/insite/remcom/OpenMPI/1.4.4/Linux-x86_64RHEL6/lib/:' +
                    '/home/psb/insite/remcom/WirelessInSite/3.3.0.4/Linux-x86_64RHEL6/bin/ ' +
                    '/home/psb/insite/remcom/WirelessInSite/3.3.0.4/Linux-x86_64RHEL6/bin/calcprop_3.3.0.4')
    wibatch_bin = ('REMCOMINC_LICENSE_FILE=2508@200.239.93.26 ' +
               'LD_LIBRARY_PATH=/home/psb/insite/remcom/OpenMPI/1.4.4/Linux-x86_64RHEL6/lib/ ' +
               '/home/psb/insite/remcom/WirelessInSite/3.3.0.4/Linux-x86_64RHEL6/bin/wibatch')
elif insite_version == '3.2': #general case, assuming Windows    
    sumo_bin = '/usr/bin/sumo'
    calcprop_bin = ('REMCOMINC_LICENSE_FILE=2508@200.239.93.26 ' +
                    'LD_LIBRARY_PATH=/home/psb/insite/remcom/OpenMPI/1.4.4/Linux-x86_64RHEL6/lib/:' +
                    '/home/psb/insite/remcom/WirelessInSite/3.2.0.3/Linux-x86_64RHEL6/bin/ ' +
                    '/home/psb/insite/remcom/WirelessInSite/3.2.0.3/Linux-x86_64RHEL6/bin/calcprop_3.2.0.3')
    wibatch_bin = ('REMCOMINC_LICENSE_FILE=2508@200.239.93.26 ' +
               'LD_LIBRARY_PATH=/home/psb/insite/remcom/OpenMPI/1.4.4/Linux-x86_64RHEL6/lib/ ' +
               '/home/psb/insite/remcom/WirelessInSite/3.2.0.3/Linux-x86_64RHEL6/bin/wibatch')
    #SUMO configuration file:

#sumo_cfg = os.path.join(working_directory, 'sumo', 'seasonal.sumocfg')
#sumo_cfg = os.path.join(working_directory, 'sumo', 'quickstart.sumocfg')
#sumo_cfg = os.path.join(working_directory, 'sumo', 'San.sumocfg')
#sumo_cfg = os.path.join(working_directory, 'sumo_drone', 'drone.sumocfg')
sumo_cfg = os.path.join(working_directory, 'longtan_sumo', 'longtan.sumocfg')

print('########## Scripts will assume the following files: ##########')
print('SUMO executable: ', sumo_bin)
print('SUMO configuration: ', sumo_cfg)
print('InSite calcprop executable: ', calcprop_bin)
print('InSite wibatch executable: ', wibatch_bin)
print('Working folder (base for several folders): ', working_directory)
print('InSite input files folder: ', base_insite_project_path)
#print('InSite temporary output folder: ', project_output_dir)
print('Final output parent folder: ', results_dir)

latitude, longitude = get_lat_long((base_insite_project_path))
n_run = range(0,300,1) # iterator that determines maximum number of RT simulations

sampling_interval = 0.5 #time interval between scenes (in seconds)
time_of_episode = 30 #Number of scenes of each episode | int(0.5 / sampling_interval) # in steps (number of scenes per episodes)
time_between_episodes = int(1 / sampling_interval) # time among episodes, in steps (if you specify x/Ts, then x is in seconds)
if use_fixed_receivers: #set to False if only vehicles are receivers
    n_antenna_per_episode = 0 #number of receivers per episode
else:
    n_antenna_per_episode = 5 #number of receivers per episode
# where to map the received to TFRecords (minx, miny, maxx, maxy)
analysis_area = (729, 453, 666, 666)
analysis_area_resolution = 0.5
antenna_number = 4
frequency = 60e9 # frequency in Hz for the RT simulation

###############################################################
## Part II - Extra information that typically does not need to be modified
## unless you changed the InSite model (using the GUI, for example)
###############################################################
##### Folders and files for InSite ####
# Copy of the RWI project used in the simulation
#AK-TODO instead of "base" it should match the name InSite gives, to facilitate porting
results_base_model_dir = os.path.join(results_dir, 'base')
results_base_model_dir.replace('\\', '/')
#Input files, which are read by the Python scripts
# File that has the base InSite project:
setup_path = os.path.join(base_insite_project_path, 'model.setup')
setup_path = setup_path.replace(' ', '\ ') #deal with paths with blank spaces
# XML that has information about the simulations
#base_x3d_xml_path = os.path.join(base_insite_project_path, 'base.Study.xml')
base_x3d_xml_path = os.path.join(base_insite_project_path, 'base.study.xml')
# Name (basename) of the paths file generated in the simulation
paths_file_name = 'model.paths.t001_01.r002.p2m'
# Base object file to generate the `object_dst_file_name`
base_object_file_name = os.path.join(base_insite_project_path, "base.object")
# Base txrx file to generate the `txrx_dst_file_name`
#base_txrx_file_name = os.path.join(base_insite_project_path, "base.object")
base_txrx_file_name = os.path.join(base_insite_project_path, "base.txrx")

#Output files, which are written by the Python scripts
#Provide here only the names. The full paths will be created by simulation.py (using the run folder)
# Name (basename) of the JSON output simulation info file
simulation_info_file_name = 'wri-simulation.info'
# Object which will be modified in the RWI project
dst_object_file_name = 'random-line.object' #file with vehicles provided by SUMO
# txrx which will be modified in the RWI project
dst_txrx_file_name = 'model.txrx' #file with Tx and Rx's
# XML project that will be executed by InSite command line tools (its path will be the run folder):
dst_x3d_xml_file_name = 'model.study.xml' #configuration file for wibatch

print('Output JSON file: ', simulation_info_file_name)
print('Reference InSite model: ', base_x3d_xml_path)
print('Generated InSite model that will be used (in run folder): ', dst_x3d_xml_file_name)
print('Reference .object file: ', base_object_file_name)
print('Generated .object file that will be used: ', dst_object_file_name)
print('Reference .txrx file: ', base_txrx_file_name)
print('Generated .txrx file that will be used: ', dst_txrx_file_name)

#the (misterious) information below is added in simulation.py into a XML file
if insite_version == '3.3':
    dst_x3d_txrx_xpath = ("./remcom__rxapi__Job/Scene/remcom__rxapi__Scene/TxRxSetList/remcom__rxapi__TxRxSetList/TxRxSet/remcom__rxapi__PointSet/OutputID/remcom__rxapi__Integer[@Value='2']" +
                      "/../../ControlPoints/remcom__rxapi__ProjectedPointList")
else:
    dst_x3d_txrx_xpath = ("./Job/Scene/Scene/TxRxSetList/TxRxSetList/TxRxSet/PointSet/OutputID/Integer[@Value='2']" +
                      "/../../ControlPoints/ProjectedPointList")

use_sumo = True

# dimensions of the Mobile Objects (MOBJS) which will be placed on `dst_object_file_name`
#car_dimensions = (1.76, 4.54, 1.47)
car_dimensions = (2, 6, 1.47) #I guess this needs to match the one specified in SUMO's route file
# antenna to be placed above the cars
antenna_origin = (car_dimensions[0] / 2, car_dimensions[1] / 2, car_dimensions[2])
# id of the car material (must be defined on `base_object_file_name`) and it is processed by simulation.py
car_material_id = 0
car_structure_name = 'car'
# name of the antenna points in `base_txrx_file_name`
antenna_points_name = 'Rx'

if use_sumo == True:
    seed = 250 #Original's ITA paper seed = 1517605264
    np.random.seed(seed)
    sumo_cmd = [sumo_bin, '-c', sumo_cfg, '--step-length', str(sampling_interval), '--seed', '{}'.format(seed)]
    #mapping from SUMO to InSite coordinates
    # (take only min and max for x and y and put there:
    lane_boundary_dict = {"laneA_0": [[758.5,460], [744.5,660]],
                          "laneB_0": [[658.82,460], [747.5,358.76]],
                          "laneC_0": [[658.82,460], [752.5,675.90]],
                          "laneD_0": [[840.08,460], [755.5,660]]}
else: #not sure if this is ancient code used for debugging with use_sumo = False:
    # origin and destination of the line to place the cars
    line_origin = ((755.25, 470, 0.2),
                   (755.25 + 5, 470, 0.2),
                   )
    line_destination = 645
    # dimension `line_destination` is indicating to
    line_dimension = 1

    # distance between cars
    def car_distances():
        return np.random.uniform(1.5, 6)

def base_run_dir_fn(i): #the folders will be run00001, run00002, etc.
    """returns the `run_dir` for run `i`"""
    return "run{:05d}".format(i)

use_tfrecord = False

if use_tfrecord == True: #enable only if want to generate tfrecord (we have not been using it)
    n_paths_to_tfrecord = 25 #number of rays per Tx / Rx pairs
    # TFRecord compression, can be NONE
    tfrecord_compression = 'GZIP'
    # Generated TFRecord
    tfrecord_file_name = os.path.join(results_dir, 'rwi.tfrecord')

    # String (len) of then objects file
    #AK: I will move this defition to tfrecord
    #dtype_of_obj_path = 'U100'

    tfrecord_options = tf.python_io.TFRecordOptions(
        eval('tf.python_io.TFRecordCompressionType.{}'.format(tfrecord_compression))
    ) \
        if tf is not None else None

    position_matrix_shape = position_matrix_per_object_shape(analysis_area, analysis_area_resolution) \
        if position_matrix_per_object_shape is not None else None
    best_tx_rx_shape = (2,)

    #tfrecord_file_name = '/Users/psb/ownCloud/Projects/DNN Wireless/rwi-simulation/rwi.tfrecord'
    #tfrecord_file_name = '/Users/psb/ownCloud/Projects/DNN Wireless/tempmm/rwi-simulation/rwi.tfrecord'
    tfrecord_file_name = os.path.join(results_dir, 'rwi.tfrecord')
