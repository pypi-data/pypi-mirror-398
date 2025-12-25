from MDAnalysis.transformations.boxdimensions import set_dimensions
from biobb_common.tools import file_utils as fu
import glob
import shutil
import os


def set_box(u):
    # Calculate the dimensions of the box
    positions = u.atoms.positions
    box_dimensions = positions.max(axis=0) - positions.min(axis=0)
    # Set the box dimensions
    u.trajectory.add_transformations(set_dimensions([*box_dimensions, 90, 90, 90]))


def ignore_no_box(u, ignore_no_box, out_log, global_log):
    # FATSLiM ValueError: Box does not correspond to PBC=xyz
    if u.dimensions is None:
        if ignore_no_box:
            fu.log('Setting box dimensions using the minimum and maximum positions of the atoms.',
                   out_log, global_log)
            set_box(u)
        else:
            fu.log('The trajectory does not contain box information. '
                   'Please set the ignore_no_box property to True to ignore this error.',
                   out_log, global_log)
            raise ValueError("Box dimensions are required but not found in the trajectory.")


def move_output_file(file, out_file_path, out_log, global_log):
    # Add a wildcard to support multiples frames output (it adds 0000 suffix)
    base, ext = os.path.splitext(file)
    file_glob = base + '*' + ext
    files_to_move = glob.glob(file_glob)
    if files_to_move:
        fu.log(f"Renaming file {files_to_move[0]} to {out_file_path}", out_log, global_log)
        # Move the file to the output path
        shutil.move(files_to_move[0], out_file_path)
    else:
        fu.log(f"Warning: File {file} not found, FATSLiM calculation might have failed.", out_log, global_log)
