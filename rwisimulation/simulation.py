import os
import shutil
import argparse

from rwimodeling import insite, objects, txrx

import config as c
from .placement import place_on_line


def main(args):
    project = insite.InSiteProject(c.setup_path, c.project_output_dir, c.calcprop_bin)

    with open(os.path.join(c.base_insite_project_path, "base.object")) as infile:
        objFile = objects.ObjectFile.from_file(infile)
    with open(os.path.join(c.base_insite_project_path, 'base.txrx')) as infile:
        txrxFile = txrx.TxRxFile.from_file(infile)

    car = objects.RectangularPrism(*c.car_dimensions, material=c.car_material_id)
    car_structure = objects.Structure(name=c.car_structure_name)
    car_structure.add_sub_structures(car)
    car_structure.dimensions = car.dimensions

    antenna = txrxFile[c.antenna_points_name].location_list[0]

    shutil.copytree(c.base_insite_project_path, c.results_base_model_dir, )
    for i in range(c.n_run):
        run_dir = os.path.join(c.results_dir, c.base_run_dir_fn(i))
        os.makedirs(run_dir)

        objFile.clear()
        structure_group, location = place_on_line(c.line_origin, c.line_destination, c.line_dimension,
              c.car_distances, car_structure, antenna, c.antenna_origin)

        objFile.add_structure_groups(structure_group)
        objFile.write(c.dst_object_file_name)
        shutil.copy(c.dst_object_file_name, run_dir)

        txrxFile[c.antenna_points_name].location_list[0] = location
        txrxFile.write(c.dst_txrx_file_name)
        shutil.copy(c.dst_txrx_file_name, run_dir)

        if not args.place_only:
            project.run(output_dir=run_dir, delete_temp=True)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--place-only', action='store_true',
                        help='Run only the objects placement')
    args = parser.parse_args()
    main(args)