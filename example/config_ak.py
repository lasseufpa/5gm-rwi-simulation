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
# Current folder (or directory). Some paths are relative to this folder:
working_directory = os.path.dirname(os.path.realpath(__file__)) 
# Directory in which the script will write the base project (the InSite input files
#that will be used to generate all other InSite input files)
base_insite_project_path = os.path.join(working_directory,
                                        '2018_02_04_insiteproject_ita')
# Ray-tracing output folder (where InSite will store the results (Study Area name)).
#The will be later copied to the corresponding output folder (run0000, run0001, etc.)
project_output_dir = os.path.join(base_insite_project_path, 'study')
<<<<<<< HEAD
# Where to store each InSite project and results (will create subfolders for each "run")
#results_dir = os.path.join(working_directory, 'results')
#On Windows: D:\ak\Works\2018-ita-paper\final\raid\pc128\example_working\results
#results_dir = ("/mnt/d/ak/Works/2018_Mimo_Nuria/lice-master-3eca4cb91b9d83bf50540308b01cf123abe30efd/results150m")
results_dir = ("/mnt/d/ak/Works/2018-ita-paper/final/raid/pc128/example_working/restuls")
#Folders and files for InSite and its license. Note 
=======
# Where to store each InSite project and results (will create subfolders run0000, 
#run0001, etc. for each "run")
results_dir = os.path.join(working_directory, 'results')
#Folders and files for InSite and its license. For Windows you may simply inform
#the path to the executable files, not minding about the license file location.
>>>>>>> 516f21472d8de3999e156e44bfb1b76bb47da3a9
#calcprop_bin = r'"C:\Program Files\Remcom\Wireless InSite 3.2.0.3\bin\calc\calcprop"'
#Folders for SUMO and InSite. Use executable sumo-gui if want to see the GUI or sumo otherwise
if socket.gethostname() == 'Pedros-MacBook-Pro.local' or \
    socket.gethostname() == 'pedro-macbook-wifi.psb-home.psbc.com.br': #Pedro's computers
    calcprop_bin = ('REMCOMINC_LICENSE_FILE=/home/psb/insite.lic ' +
                'LD_LIBRARY_PATH=/home/psb/insite/remcom/OpenMPI/1.4.4/Linux-x86_64RHEL6/lib/:' +
                '/home/psb/insite/remcom/WirelessInSite/3.2.0.3/Linux-x86_64RHEL6/bin/ ' +
                '/home/psb/insite/remcom/WirelessInSite/3.2.0.3/Linux-x86_64RHEL6/bin/calcprop_3.2.0.3')
    wibatch_bin = ('REMCOMINC_LICENSE_FILE=/home/psb/insite.lic ' +
               'LD_LIBRARY_PATH=/home/psb/insite/remcom/OpenMPI/1.4.4/Linux-x86_64RHEL6/lib/ ' +
               '/home/psb/insite/remcom/WirelessInSite/3.2.0.3/Linux-x86_64RHEL6/bin/wibatch')
    sumo_bin = '/Users/psb/ownCloud/Projects/DNNWireless/sumo/bin/sumo-gui'
<<<<<<< HEAD
elif socket.gethostname() == 'LAPTOP-8R7EBD20':
    sumo_bin = '/usr/bin/sumo'
    #sumo_bin = r'/mnt/c/Program Files (x86)/DLR/Sumo/bin/sumo-gui.exe' #'/usr/bin/sumo'
    #sumo_cfg = r'D:\linux_gits\rwi-simulation\example\sumo\quickstart.sumocfg'
else:
    sumo_bin = '/usr/bin/sumo'
#SUMO configuration file:
sumo_cfg = os.path.join(working_directory, 'sumo',
                        'quickstart.sumocfg')
                        
print('AK: ', sumo_bin)
print('AK: ', sumo_cfg)
                        
n_run = range(5000) # iterator that determines maximum number of RT simulations
=======
    #sumo_bin = '/usr/bin/sumo' #default if installed on Linux
    sumo_cfg = os.path.join(working_directory, 'sumo', 'quickstart.sumocfg')
elif socket.gethostname() == 'LAPTOP-8R7EBD20': #Aldebaro's computer
    if False: #execute the GUI'
        sumo_bin = r'c:\Program Files (x86)\DLR\Sumo\bin\sumo-gui.exe' 
    else: #command line
        sumo_bin = r'c:\Program Files (x86)\DLR\Sumo\bin\sumo.exe' #on Windows
    #sumo_bin = r'/mnt/c/Program Files (x86)/DLR/Sumo/bin/sumo-gui.exe'
    sumo_cfg = os.path.join(working_directory, 'sumo', 'quickstart.sumocfg')
    #Windows version of InSite command line utility softwares:
    calcprop_bin = r'"C:\Program Files\Remcom\Wireless InSite 3.2.0.3\bin\calc\calcprop"'
    wibatch_bin = r'"C:\Program Files\Remcom\Wireless InSite 3.2.0.3\bin\calc\wibatch"'
else: #general case, assuming Windows    
    sumo_bin = r'"C:\Program Files (x86)\DLR\Sumo\bin\sumo.exe"'
    calcprop_bin = r'"C:\Program Files\Remcom\Wireless InSite 3.2.0.3\bin\calc\calcprop"'
    wibatch_bin = r'"C:\Program Files\Remcom\Wireless InSite 3.2.0.3\bin\calc\wibatch"'
    #SUMO configuration file:
    sumo_cfg = os.path.join(working_directory, 'sumo', 'quickstart.sumocfg')
print('########## Scripts will assume the following files: ##########')
print('SUMO executable: ', sumo_bin)
print('SUMO configuration: ', sumo_cfg)
print('InSite calcprop executable: ', calcprop_bin)
print('InSite wibatch executable: ', wibatch_bin)
n_run = range(10) # iterator that determines maximum number of RT simulations
>>>>>>> 516f21472d8de3999e156e44bfb1b76bb47da3a9
#n_run = itertools.count() # infinite
sampling_interval = 0.1 #time interval between scenes (in seconds)
time_of_episode = int(0.5 / sampling_interval) # in steps (number of scenes per episodes)
time_between_episodes = int(10 / sampling_interval) # time among episodes, in steps
n_antenna_per_episode = 10 #number of receivers per episode
n_paths_to_tfrecord = 25 #number of rays per Tx / Rx pairs
# where to map the received to TFRecords (minx, miny, maxx, maxy)
analysis_area = (729, 453, 666, 666)
analysis_area_resolution = 0.5
antenna_number = 4
frequency = 6e10 # frequency in Hz for the RT simulation

###############################################################
## Part II - Extra information that typically does not need to be modified
###############################################################
##### Folders and files for InSite ####
# File that has the base InSite project:
setup_path = os.path.join(base_insite_project_path, 'model.setup')
setup_path = setup_path.replace(' ', '\ ') #deal with paths with blank spaces
# Ray-tracing (InSite) study area path:
base_x3d_xml_path = os.path.join(base_insite_project_path, 'base.Study.xml')
# Name (basename) of the paths file generated in the simulation
paths_file_name = 'model.paths.t001_01.r002.p2m'
# Name (basename) of the simulation info file
simulation_info_file_name = 'wri-simulation.info'
# Base object file to generate the `object_dst_file_name`
base_object_file_name = os.path.join(base_insite_project_path, "base.object")
# Object which will be modified in the RWI project
dst_object_file_name = os.path.join(base_insite_project_path, "random-line.object")
# Base txrx file to generate the `txrx_dst_file_name`
base_txrx_file_name = os.path.join(base_insite_project_path, "base.object")
# txrx which will be modified in the RWI project
dst_txrx_file_name = os.path.join(base_insite_project_path, 'model.txrx')
dst_x3d_txrx_xpath = ("./Job/Scene/Scene/TxRxSetList/TxRxSetList/TxRxSet/PointSet/OutputID/Integer[@Value='2']" +
                      "/../../ControlPoints/ProjectedPointList")
dst_x3d_xml_path = os.path.join(base_insite_project_path, 'gen.Study.xml')
##### Extra information for InSite ####
# dimensions of the Mobile Objects (MOBJS) which will be placed on `dst_object_file_name`
car_dimensions = (1.76, 4.54, 1.47)
# id of the car material (must be defined on `base_object_file_name`)
car_material_id = 0
car_structure_name = 'car'
# name of the antenna points in `base_txrx_file_name`
antenna_points_name = 'Rx'
# antenna to be placed above the cars
antenna_origin = (car_dimensions[0] / 2, car_dimensions[1] / 2, car_dimensions[2])
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
# Copy of the RWI project used in the simulation
results_base_model_dir = os.path.join(results_dir, 'base')
# TFRecord compression, can be NONE
tfrecord_compression = 'GZIP'
# Generated TFRecord
tfrecord_file_name = os.path.join(results_dir, 'rwi.tfrecord')

# String (len) of then objects file
dtype_of_obj_path = 'U100'

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

seed = 1517605264
np.random.seed(seed)
sumo_cmd = [sumo_bin, '-c', sumo_cfg, '--step-length', str(sampling_interval), '--seed', '{}'.format(seed)]
use_sumo = True

#mapping from SUMO to InSite coordinates
# (take only min and max for x and y and put there:
lane_boundary_dict = {"laneA_0": [[758.5,460], [744.5,660]],
                      "laneB_0": [[658.82,460], [747.5,358.76]],
                      "laneC_0": [[658.82,460], [752.5,675.90]],
                      "laneD_0": [[840.08,460], [755.5,660]]}

#not used anymore
margin_dict = {'H1_0': [0, 0],
               'V1_1': [0, 0],
               'V2_1': [0, 0],}
