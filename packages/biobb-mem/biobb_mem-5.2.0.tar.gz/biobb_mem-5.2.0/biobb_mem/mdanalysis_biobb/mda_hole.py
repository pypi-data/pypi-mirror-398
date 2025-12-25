#!/usr/bin/env python3

"""Module containing the MDAnalysis HOLE class and the command line interface."""
import re
import os
import numpy as np
import pandas as pd
from biobb_common.generic.biobb_object import BiobbObject
from biobb_common.tools.file_utils import launchlogger
import MDAnalysis as mda
from mdahole2.analysis import HoleAnalysis


class MDAHole(BiobbObject):
    """
    | biobb_mem MDAHole
    | Wrapper of the MDAnalysis HOLE module for analyzing ion channel pores or transporter pathways.
    | MDAnalysis HOLE provides an interface to the HOLE suite of tools to analyze pore dimensions and properties along a channel or transporter pathway. The parameter names and defaults follow the `MDAnalysis HOLE <https://www.mdanalysis.org/mdahole2/api.html>`_  implementation.

    Args:
        input_top_path (str): Path to the input structure or topology file. File type: input. `Sample file <https://github.com/bioexcel/biobb_mem/raw/main/biobb_mem/test/data/A01JD/A01JD.pdb>`_. Accepted formats: crd (edam:3878), gro (edam:2033), mdcrd (edam:3878), mol2 (edam:3816), pdb (edam:1476), pdbqt (edam:1476), prmtop (edam:3881), psf (edam:3882), top (edam:3881), tpr (edam:2333), xml (edam:2332), xyz (edam:3887).
        input_traj_path (str): Path to the input trajectory to be processed. File type: input. `Sample file <https://github.com/bioexcel/biobb_mem/raw/main/biobb_mem/test/data/A01JD/A01JD.xtc>`_. Accepted formats: arc (edam:2333), crd (edam:3878), dcd (edam:3878), ent (edam:1476), gro (edam:2033), inpcrd (edam:3878), mdcrd (edam:3878), mol2 (edam:3816), nc (edam:3650), pdb (edam:1476), pdbqt (edam:1476), restrt (edam:3886), tng (edam:3876), trr (edam:3910), xtc (edam:3875), xyz (edam:3887).
        output_hole_path (str): Path to the output HOLE analysis results. File type: output. `Sample file <https://github.com/bioexcel/biobb_mem/raw/main/biobb_mem/test/reference/mdanalysis_biobb/hole.vmd>`_. Accepted formats: vmd (edam:format_2330).
        output_csv_path (str): Path to the output CSV file containing the radius and coordinates of the pore. File type: output. `Sample file <https://github.com/bioexcel/biobb_mem/raw/main/biobb_mem/test/reference/mdanalysis_biobb/hole_profile.csv>`_. Accepted formats: csv (edam:format_3752).
        properties (dic - Python dictionary object containing the tool parameters, not input/output files):
            * **start** (*int*) - (None) Starting frame for slicing.
            * **stop** (*int*) - (None) Ending frame for slicing.
            * **steps** (*int*) - (None) Step for slicing.
            * **executable** (*str*) - ("hole") Path to the HOLE executable.
            * **select** (*str*) - ("protein") The selection string to create an atom selection that the HOLE analysis is applied to.
            * **cpoint** (*list*) - (None) Coordinates of a point inside the pore (Å). If None, tries to guess based on the geometry.
            * **cvect** (*list*) - (None) Search direction vector. If None, tries to guess based on the geometry.
            * **sample** (*float*) - (0.2) Distance of sample points in Å. This value determines how many points in the pore profile are calculated.
            * **end_radius** (*float*) - (22) Radius in Å, which is considered to be the end of the pore.
            * **dot_density** (*int*) - (15) [5~35] Density of facets for generating a 3D pore representation.
            * **remove_tmp** (*bool*) - (True) [WF property] Remove temporal files.
            * **restart** (*bool*) - (False) [WF property] Do not execute if output files exist.
            * **sandbox_path** (*str*) - ("./") [WF property] Parent path to the sandbox directory.

    Examples:
        This is a use example of how to use the building block from Python::

            from biobb_mem.mdanalysis_biobb.mda_hole import mda_hole
            prop = {
                'select': 'protein',
                'executable': 'hole'
            }
            mda_hole(input_top_path='/path/to/myTopology.pdb',
                    input_traj_path='/path/to/myTrajectory.xtc',
                    output_hole_path='/path/to/hole_analysis.vmd',
                    output_csv_path='/path/to/hole_profile.csv',
                    properties=prop)

    Info:
        * wrapped_software:
            * name: MDAnalysis
            * version: 2.7.0
            * license: GNU
        * ontology:
            * name: EDAM
            * schema: http://edamontology.org/EDAM.owl
    """

    def __init__(self, input_top_path, input_traj_path, output_hole_path, output_csv_path=None,
                 properties=None, **kwargs) -> None:
        properties = properties or {}

        # Call parent class constructor
        super().__init__(properties)
        self.locals_var_dict = locals().copy()

        # Input/Output files
        self.io_dict = {
            "in": {"input_top_path": input_top_path, "input_traj_path": input_traj_path},
            "out": {"output_hole_path": output_hole_path, "output_csv_path": output_csv_path}
        }

        # Properties specific for MDAHole
        self.start = properties.get('start', None)
        self.stop = properties.get('stop', None)
        self.steps = properties.get('steps', None)
        self.executable = properties.get('executable', 'hole')
        self.select = properties.get('select', 'protein')
        self.cpoint = properties.get('cpoint', None)
        self.cvect = properties.get('cvect', None)
        self.sample = properties.get('sample', 0.2)
        self.end_radius = properties.get('end_radius', 22)
        self.dot_density = properties.get('dot_density', 15)
        self.properties = properties

        # Check the properties
        self.check_properties(properties)
        self.check_arguments()

    @launchlogger
    def launch(self) -> int:
        """Execute the :class:`MDAHole <mdanalysis_biobb.mda_hole.MDAHole>` object."""

        # Setup Biobb
        if self.check_restart():
            return 0
        self.stage_files()

        # Load the universe
        u = mda.Universe(self.stage_io_dict["in"]["input_top_path"],
                         self.stage_io_dict["in"]["input_traj_path"])
        # save current directory and move to temporary
        cwd = os.getcwd()
        os.chdir(self.stage_io_dict.get("unique_dir"))
        # Create HoleAnalysis object
        hole = HoleAnalysis(
            universe=u,
            select=self.select,
            cpoint=self.cpoint,
            cvect=self.cvect,
            sample=self.sample,
            executable=self.executable,
            end_radius=self.end_radius
        )
        # Run the analysis with step parameter
        hole.run(
            start=self.start,
            stop=self.stop,
            step=self.steps
        )
        # Save the results to a CSV file
        all_frames = []
        for frame in hole.results.profiles.keys():
            rxn_coord = hole.results.profiles[frame].rxn_coord
            radius = hole.results.profiles[frame].radius
            df_frame = pd.DataFrame({'Frame': frame, 'Pore Coordinate': rxn_coord, 'Radius': radius})
            all_frames.append(df_frame)
        # Concatenate all frames into a single DataFrame
        df_all_frames = pd.concat(all_frames, ignore_index=True)
        df_all_frames.to_csv(self.stage_io_dict["out"]["output_csv_path"], index=False)

        hole.create_vmd_surface(
            self.stage_io_dict["out"]["output_hole_path"],
            dot_density=self.dot_density
        )
        hole.delete_temporary_files()
        # move back to original directory
        os.chdir(cwd)
        # Copy files to host
        self.copy_to_host()
        # remove temporary folder(s)
        self.remove_tmp_files()

        self.check_arguments(output_files_created=True, raise_exception=False)

        return self.return_code


def mda_hole(input_top_path: str,
             input_traj_path: str,
             output_hole_path: str,
             output_csv_path: str,
             properties: dict = None,
             **kwargs) -> int:
    """Execute the :class:`MDAHole <mdanalysis_biobb.mda_hole.MDAHole>` class and
    execute the :meth:`launch() <mdanalysis_biobb.mda_hole.MDAHole.launch>` method."""
    return MDAHole(**dict(locals())).launch()


mda_hole.__doc__ = MDAHole.__doc__
main = MDAHole.get_main(mda_hole, "Analyze ion channel pores or transporter pathways.")


def display_hole(input_top_path: str, input_traj_path: str,
                 output_hole_path: str = 'hole.vmd',
                 frame: int = 0, opacity: float = 0.9):
    """
    Visualize a channel using NGLView from a VMD file.

    Args:
        input_top_path (str): Path to the input topology file.
        output_hole_path (str, optional): Path to the VMD file containing the channel data. Default is 'hole.vmd'.
        frame (int, optional): Frame index to visualize. Default is 0.
        opacity (float, optional): Opacity of the visualization. Default is 0.9.
    Returns:
        nglview.NGLWidget: NGLView widget for visualizing the channel.
    """

    try:
        import nglview as nv
    except ImportError:
        raise ImportError('Please install the nglview package to visualize the channel.')

    # Read the VMD file and parse triangles
    with open(output_hole_path, 'r') as f:
        lines = f.readlines()

    # Find lines with triangle coordinates
    trinorms = []
    for i, line in enumerate(lines):
        if i > 3 and 'set triangle' in line:
            vmd_set = re.sub(r'set triangles\(\d+\)', '', line)  # Remove set triangles(i)
            vmd_set = re.sub(r'\{(\s*-?\d[^\s]*)(\s*-?\d[^\s]*)(\s*-?\d[^}]*)\}', r'[\1,\2,\3]', vmd_set)  # Convert { x y z } to [x,y,z]
            vmd_set = vmd_set.replace('{', '[').replace('}', ']')  # Convert { to [ and } to ]
            vmd_set = re.sub(r'\]\s*\[', '], [', vmd_set)  # Add commas between brackets
            vmd_set = eval(vmd_set.strip())  # Evaluate string as list
            # different hole colors
            trinorms.append(vmd_set)
    # Create a list of positions, colors, and normals
    colors = np.array([[1, 0, 0],   # red
                       [0, 1, 0],   # green
                       [0, 0, 1]])  # blue
    poss, cols, nors = [], [], []
    for i, color in enumerate(colors):
        if len(trinorms[frame][i]) > 0:
            col_dat = np.array(trinorms[frame][i])
            poss.append(col_dat[:, :3, :].flatten())  # 3 first elements are positions
            cols.append((np.zeros(col_dat.shape[0]*18).reshape(-1, 3) + color).flatten())  # 3 colors for each vertex
            nors.append(col_dat[:, 3:, :].flatten())  # 3 last elements are normals
    poss = np.concatenate(poss)
    cols = np.concatenate(cols)
    nors = np.concatenate(nors)
    # Create NGLView widget
    u = mda.Universe(input_top_path, input_traj_path)
    view = nv.show_mdanalysis(u)
    # view.clear_representations()
    mesh = ('mesh', poss, cols)
    view._add_shape([mesh], name='my_shape')
    view.update_representation(component=1, repr_index=0, opacity=opacity)
    return view


if __name__ == '__main__':
    main()
