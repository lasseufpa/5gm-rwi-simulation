import os
import shutil

import numpy as np

from placement import place_on_line
from rwimodeling import insite, objects, txrx

if __name__ == '__main__':
    base_insite_project_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'SimpleFunciona')

    # Where to store the results (will create subfolders for each "run")
    results_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                               'restuls')
    results_base_model_dir = os.path.join(results_dir, 'base')
    # InSite project path
    path = os.path.join(base_insite_project_path, 'model.setup')
    # Where the InSite project will store the results (Study Area name)
    project_output_dir = os.path.join(base_insite_project_path, 'study')
    project = insite.InSiteProject(path, project_output_dir)

    object_dst_file_name = os.path.join(base_insite_project_path, "random-line.object")
    txrx_dst_file_name = os.path.join(base_insite_project_path, 'model.txrx')

    with open(os.path.join(base_insite_project_path, "base.object")) as infile:
        objFile = objects.ObjectFile.from_file(infile)
    with open(os.path.join(base_insite_project_path, 'base.txrx')) as infile:
        txrxFile = txrx.TxRxFile.from_file(infile)

    car = objects.RectangularPrism(1.76, 4.54, 1.47, material=0)
    car_structure = objects.Structure(name="car")
    car_structure.add_sub_structures(car)
    car_structure.dimensions = car.dimensions

    city_origin = np.array((648, 456, 0.2))
    antenna_origin = np.array((car.height / 2, car.width / 2, car.height))
    antenna = txrxFile['Rx'].location_list[0]

    shutil.copytree(base_insite_project_path, results_base_model_dir, )
    for i in range(2):
        run_dir = os.path.join(results_dir, 'run{:05d}'.format(i))
        os.makedirs(run_dir)

        objFile.clear()
        structure_group, location = place_on_line(
            city_origin, 531, 1, lambda: np.random.uniform(1, 3), car_structure, antenna, antenna_origin)

        objFile.add_structure_groups(structure_group)
        objFile.write(object_dst_file_name)
        shutil.copy(object_dst_file_name, run_dir)


        txrxFile['Rx'].location_list[0] = location
        txrxFile.write(txrx_dst_file_name)
        shutil.copy(txrx_dst_file_name, run_dir)

        project.run(output_dir=run_dir, delete_temp=True)