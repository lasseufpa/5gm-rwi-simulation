import os

import tensorflow as tf

base_insite_project_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'SimpleFunciona')

# Where to store the results (will create subfolders for each "run")
results_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                           'restuls')

results_base_model_dir = os.path.join(results_dir, 'base')
# InSite project path
path = os.path.join(base_insite_project_path, 'model.setup')
# Where the InSite project will store the results (Study Area name)
project_output_dir = os.path.join(base_insite_project_path, 'study')

object_dst_file_name = os.path.join(base_insite_project_path, "random-line.object")
txrx_dst_file_name = os.path.join(base_insite_project_path, 'model.txrx')

tfrecord_options = tf.python_io.TFRecordOptions(tf.python_io.TFRecordCompressionType.GZIP)
