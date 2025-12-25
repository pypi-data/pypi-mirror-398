#!/usr/bin/env python3

"""Module containing the Lipyphilic AssignLeaflets class and the command line interface."""
from biobb_common.generic.biobb_object import BiobbObject
from biobb_common.tools.file_utils import launchlogger
import MDAnalysis as mda
from biobb_mem.lipyphilic_biobb.common import ignore_no_box
from lipyphilic.leaflets.assign_leaflets import AssignLeaflets
import pandas as pd
import numpy as np


class LPPAssignLeaflets(BiobbObject):
    """
    | biobb_mem LPPAssignLeaflets
    | Wrapper of the LiPyphilic AssignLeaflets module for assigning lipids to leaflets in a bilayer.
    | LiPyphilic is a Python package for analyzing MD simulations of lipid bilayers. The parameter names and defaults are the same as the ones in the official `Lipyphilic documentation <https://lipyphilic.readthedocs.io/en/latest/reference/analysis/leaflets.html>`_.

    Args:
        input_top_path (str): Path to the input structure or topology file. File type: input. `Sample file <https://github.com/bioexcel/biobb_mem/raw/main/biobb_mem/test/data/A01JD/A01JD.pdb>`_. Accepted formats: crd (edam:3878), gro (edam:2033), mdcrd (edam:3878), mol2 (edam:3816), pdb (edam:1476), pdbqt (edam:1476), prmtop (edam:3881), psf (edam:3882), top (edam:3881), tpr (edam:2333), xml (edam:2332), xyz (edam:3887).
        input_traj_path (str): Path to the input trajectory to be processed. File type: input. `Sample file <https://github.com/bioexcel/biobb_mem/raw/main/biobb_mem/test/data/A01JD/A01JD.xtc>`_. Accepted formats: arc (edam:2333), crd (edam:3878), dcd (edam:3878), ent (edam:1476), gro (edam:2033), inpcrd (edam:3878), mdcrd (edam:3878), mol2 (edam:3816), nc (edam:3650), pdb (edam:1476), pdbqt (edam:1476), restrt (edam:3886), tng (edam:3876), trr (edam:3910), xtc (edam:3875), xyz (edam:3887).
        output_leaflets_path (str): Path to the output leaflet assignments. File type: output. `Sample file <https://github.com/bioexcel/biobb_mem/raw/main/biobb_mem/test/reference/lipyphilic_biobb/leaflets_data.csv>`_. Accepted formats: csv (edam:format_3752), npy (edam:format_4003).
        properties (dic - Python dictionary object containing the tool parameters, not input/output files):
            * **start** (*int*) - (None) Starting frame for slicing.
            * **stop** (*int*) - (None) Ending frame for slicing.
            * **steps** (*int*) - (None) Step for slicing.
            * **lipid_sel** (*str*) - ("all") Selection string for the lipids in a membrane. The selection should cover **all** residues in the membrane, including cholesterol.
            * **midplane_sel** (*str*) - (None) Selection string for residues that may be midplane. Any residues not in this selection will be assigned to a leaflet regardless of its proximity to the midplane. The default is `None`, in which case all lipids will be assigned to either the upper or lower leaflet.
            * **midplane_cutoff** (*float*) - (0) Minimum distance in *z* an atom must be from the midplane to be assigned to a leaflet rather than the midplane. The default is `0`, in which case all lipids will be assigned to either the upper or lower leaflet. Must be non-negative.
            * **n_bins** (*int*) - (1) Number of bins in *x* and *y* to use to create a grid of membrane patches. Local membrane midpoints are computed for each patch, and lipids assigned a leaflet based on the distance to their local membrane midpoint. The default is `1`, which is equivalent to computing a single global midpoint.
            * **ignore_no_box** (*bool*) - (False) Ignore the absence of box information in the trajectory. If the trajectory does not contain box information, the box will be set to the minimum and maximum positions of the atoms in the trajectory.
            * **remove_tmp** (*bool*) - (True) [WF property] Remove temporal files.
            * **restart** (*bool*) - (False) [WF property] Do not execute if output files exist.
            * **sandbox_path** (*str*) - ("./") [WF property] Parent path to the sandbox directory.

    Examples:
        This is a use example of how to use the building block from Python::

            from biobb_mem.lipyphilic_biobb.lpp_assign_leaflets import lpp_assign_leaflets
            prop = {
                'lipid_sel': 'name GL1 GL2 ROH',
            }
            lpp_assign_leaflets(input_top_path='/path/to/myTopology.tpr',
                                input_traj_path='/path/to/myTrajectory.xtc',
                                output_leaflets_path='/path/to/leaflets.csv',
                                properties=prop)

    Info:
        * wrapped_software:
            * name: LiPyphilic
            * version: 0.11.0
            * license: GPL-2.0
        * ontology:
            * name: EDAM
            * schema: http://edamontology.org/EDAM.owl

    """

    def __init__(self,
                 input_top_path,
                 input_traj_path,
                 output_leaflets_path,
                 properties=None,
                 **kwargs) -> None:
        properties = properties or {}

        # Call parent class constructor
        super().__init__(properties)
        self.locals_var_dict = locals().copy()

        # Input/Output files
        self.io_dict = {
            "in": {"input_top_path": input_top_path, "input_traj_path": input_traj_path},
            "out": {"output_leaflets_path": output_leaflets_path}
        }
        self.start = properties.get('start', None)
        self.stop = properties.get('stop', None)
        self.steps = properties.get('steps', None)
        self.lipid_sel = properties.get('lipid_sel', 'all')
        self.midplane_sel = properties.get('midplane_sel', None)
        self.midplane_cutoff = properties.get('midplane_cutoff', None)
        self.n_bins = properties.get('n_bins', 1)
        # Properties specific for BB
        self.ignore_no_box = properties.get('ignore_no_box', True)
        self.properties = properties

        # Check the properties
        self.check_properties(properties)
        self.check_arguments()

    @launchlogger
    def launch(self) -> int:
        """Execute the :class:`LPPAssignLeaflets <lipyphilic_biobb.lpp_assign_leaflets.LPPAssignLeaflets>` object."""

        # Setup Biobb
        if self.check_restart():
            return 0
        self.stage_files()

        # Load the trajectory
        u = mda.Universe(self.stage_io_dict["in"]["input_top_path"], self.stage_io_dict["in"]["input_traj_path"])
        ignore_no_box(u, self.ignore_no_box, self.out_log, self.global_log)
        # Create AssignLeaflets object
        leaflets = AssignLeaflets(
            universe=u,
            lipid_sel=self.lipid_sel,
            midplane_sel=self.midplane_sel,
            midplane_cutoff=self.midplane_cutoff,
            n_bins=self.n_bins
        )
        # Run the analysis
        leaflets.run(start=self.start, stop=self.stop, step=self.steps)

        out_format = self.stage_io_dict["out"]["output_leaflets_path"].split('.')[-1]
        if out_format == 'csv':
            # Save the results
            frames = leaflets.leaflets.shape[1]
            resnames = np.repeat(leaflets.membrane.resnames, frames)
            resindices = np.tile(leaflets.membrane.resindices, frames)
            frame_numbers = np.repeat(np.arange(frames), leaflets.membrane.n_residues)

            df = pd.DataFrame({
                'resname': resnames,
                'resindex': resindices,
                'frame': frame_numbers,
                'leaflet_index': leaflets.leaflets.T.flatten()
            })

            # Save the DataFrame to a CSV file
            df.to_csv(self.stage_io_dict["out"]["output_leaflets_path"], index=False)
        elif out_format == 'npy':
            np.save(self.stage_io_dict["out"]["output_leaflets_path"], leaflets.leaflets)
        # Copy files to host
        self.copy_to_host()
        self.remove_tmp_files()
        self.check_arguments(output_files_created=True, raise_exception=False)

        return self.return_code


def lpp_assign_leaflets(input_top_path: str,
                        input_traj_path: str,
                        output_leaflets_path: str = None,
                        properties: dict = None,
                        **kwargs) -> int:
    """Execute the :class:`LPPAssignLeaflets <lipyphilic_biobb.lpp_assign_leaflets.LPPAssignLeaflets>` class and
    execute the :meth:`launch() <lipyphilic_biobb.lpp_assign_leaflets.LPPAssignLeaflets.launch>` method."""
    return LPPAssignLeaflets(**dict(locals())).launch()


lpp_assign_leaflets.__doc__ = LPPAssignLeaflets.__doc__
main = LPPAssignLeaflets.get_main(lpp_assign_leaflets, "Assign lipids to leaflets in a bilayer.")


def display_nglview(input_top_path: str, output_leaflets_path: str, frame: int = 0):
    """
    Visualize the leaflets of a membrane using NGLView.

    Args:
        input_top_path (str): Path to the input topology file.
        output_leaflets_path (str): Path to the CSV file containing leaflet assignments.
        frame (int, optional): Frame number to visualize. Default is 0.
    Returns:
        nglview.NGLWidget: An NGLView widget displaying the membrane leaflets.
    """

    try:
        import nglview as nv
    except ImportError:
        raise ImportError('Please install the nglview package to visualize the leaflets.')
    # Read the leaflets DataFrame
    df = pd.read_csv(output_leaflets_path)
    top_idx = df[(df['frame'] == frame) & (df['leaflet_index'] == 1)]['resindex'].values
    bot_idx = df[(df['frame'] == frame) & (df['leaflet_index'] == -1)]['resindex'].values
    # Load the topology and convert the resindices to resnums (nglview uses resnums)
    u = mda.Universe(input_top_path)
    top_resnum = u.residues[top_idx].resnums
    bot_resnum = u.residues[bot_idx].resnums
    # Create the view
    view = nv.show_file(input_top_path)
    view.update_ball_and_stick(selection='all', opacity=0.0)   # delete membrane
    view.add_ball_and_stick(selection=", ".join(map(str, top_resnum)), color='blue')
    view.add_ball_and_stick(selection=", ".join(map(str, bot_resnum)), color='yellow')
    return view


if __name__ == '__main__':
    main()
