import sys
import os
import shutil
import argparse

import traci

from rwimodeling import insite, objects, txrx, X3dXmlFile

import config as c
from .placement import place_on_line


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--place-only', action='store_true',
                        help='Run only the objects placement')
    parser.add_argument('-c', '--run-calcprop', action='store_true',
                        help='Run using calcprop')
    args = parser.parse_args()

    insite_project = insite.InSiteProject(setup_path=c.setup_path, xml_path=c.dst_x3d_xml_path.replace(' ', '\ '),
                                          output_dir=c.project_output_dir, calcprop_bin=c.calcprop_bin,
                                          wibatch_bin=c.wibatch_bin)

    with open(os.path.join(c.base_insite_project_path, "base.object")) as infile:
        objFile = objects.ObjectFile.from_file(infile)
    with open(os.path.join(c.base_insite_project_path, 'base.txrx')) as infile:
        txrxFile = txrx.TxRxFile.from_file(infile)
    x3d_xml_file = X3dXmlFile(c.base_x3d_xml_path)

    car = objects.RectangularPrism(*c.car_dimensions, material=c.car_material_id)
    car_structure = objects.Structure(name=c.car_structure_name)
    car_structure.add_sub_structures(car)
    car_structure.dimensions = car.dimensions

    antenna = txrxFile[c.antenna_points_name].location_list[0]

    shutil.copytree(c.base_insite_project_path, c.results_base_model_dir, )

    traci.start(c.sumo_cmd)

    for i in c.n_run:
        run_dir = os.path.join(c.results_dir, c.base_run_dir_fn(i))
        os.makedirs(run_dir)
        traci.simulationStep()

        objFile.clear()
        structure_group = objects.StructureGroup()

        for veh in traci.vehicle.getIDList():
            (x, y), angle, length, width, height = [f(veh) for f in [
                traci.vehicle.getPosition,
                traci.vehicle.getAngle,
                traci.vehicle.getWidth,
                traci.vehicle.getLength,
                traci.vehicle.getHeight
            ]]
            car = objects.RectangularPrism(length, width, height, material=c.car_material_id)

            car.translate((-length/2, -width/2, -height/2))
            car.rotate(-angle)
            car.translate((x, y, 0))

            car_structure = objects.Structure(name=veh)
            car_structure.add_sub_structures(car)
            structure_group.add_structures(car_structure)

        objFile.add_structure_groups(structure_group)
        objFile.write(c.dst_object_file_name)

        sys.stdin.readline()
        continue

        structure_group, location = place_on_line(c.line_origin, c.line_destination, c.line_dimension,
              c.car_distances, car_structure, antenna, c.antenna_origin)

        objFile.add_structure_groups(structure_group)
        objFile.write(c.dst_object_file_name)
        shutil.copy(c.dst_object_file_name, run_dir)

        x3d_xml_file.add_vertice_list(location, c.dst_x3d_txrx_xpath)
        x3d_xml_file.write(c.dst_x3d_xml_path)
        shutil.copy(c.dst_x3d_xml_path, run_dir)

        txrxFile[c.antenna_points_name].location_list[0] = location
        txrxFile.write(c.dst_txrx_file_name)
        shutil.copy(c.dst_txrx_file_name, run_dir)

        if not args.place_only:
            insite_project.run_x3d(output_dir=run_dir.replace(' ', '\ '))

        if not args.place_only and args.run_calcprop:
            insite_project.run_calcprop(output_dir=run_dir, delete_temp=True)

    traci.close()

if __name__ == '__main__':
    main()