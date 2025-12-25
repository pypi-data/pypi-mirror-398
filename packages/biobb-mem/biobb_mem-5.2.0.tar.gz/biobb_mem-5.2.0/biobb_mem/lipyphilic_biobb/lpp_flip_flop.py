#!/usr/bin/env python3

"""Module containing the Lipyphilic FlipFlop class and the command line interface."""
from biobb_common.generic.biobb_object import BiobbObject
from biobb_common.tools.file_utils import launchlogger
import MDAnalysis as mda
from biobb_mem.lipyphilic_biobb.common import ignore_no_box
from lipyphilic.analysis.flip_flop import FlipFlop
import pandas as pd
import numpy as np


class LPPFlipFlop(BiobbObject):
    """
    | biobb_mem LPPFlipFlop
    | Wrapper of the LiPyphilic FlipFlop module for finding flip-flop events in a lipid bilayer.
    | LiPyphilic is a Python package for analyzing MD simulations of lipid bilayers. The parameter names and defaults are the same as the ones in the official `Lipyphilic documentation <https://lipyphilic.readthedocs.io/en/stable/reference/lib/flip_flop.html>`_.

    Args:
        input_top_path (str): Path to the input structure or topology file. File type: input. `Sample file <https://github.com/bioexcel/biobb_mem/raw/main/biobb_mem/test/data/A01JD/A01JD.pdb>`_. Accepted formats: crd (edam:3878), gro (edam:2033), mdcrd (edam:3878), mol2 (edam:3816), pdb (edam:1476), pdbqt (edam:1476), prmtop (edam:3881), psf (edam:3882), top (edam:3881), tpr (edam:2333), xml (edam:2332), xyz (edam:3887).
        input_traj_path (str): Path to the input trajectory to be processed. File type: input. `Sample file <https://github.com/bioexcel/biobb_mem/raw/main/biobb_mem/test/data/A01JD/A01JD.xtc>`_. Accepted formats: arc (edam:2333), crd (edam:3878), dcd (edam:3878), ent (edam:1476), gro (edam:2033), inpcrd (edam:3878), mdcrd (edam:3878), mol2 (edam:3816), nc (edam:3650), pdb (edam:1476), pdbqt (edam:1476), restrt (edam:3886), tng (edam:3876), trr (edam:3910), xtc (edam:3875), xyz (edam:3887).
        input_leaflets_path (str): Path to the input leaflet assignments. File type: input. `Sample file <https://github.com/bioexcel/biobb_mem/raw/main/biobb_mem/test/reference/lipyphilic_biobb/leaflets_data.csv>`_. Accepted formats: csv (edam:format_3752), npy (edam:format_4003).
        output_flip_flop_path (str): Path to the output flip-flop data. File type: output. `Sample file <https://github.com/bioexcel/biobb_mem/raw/main/biobb_mem/test/reference/lipyphilic_biobb/flip_flop.csv>`_. Accepted formats: csv (edam:format_3752).
        properties (dic - Python dictionary object containing the tool parameters, not input/output files):
            * **start** (*int*) - (None) Starting frame for slicing.
            * **stop** (*int*) - (None) Ending frame for slicing.
            * **steps** (*int*) - (None) Step for slicing.
            * **lipid_sel** (*str*) - ("all") Selection string for the lipids in a membrane. The selection should cover **all** residues in the membrane, including cholesterol.
            * **frame_cutoff** (*float*) - (1) To be counted as a successful flip-flop, a molecule must reside in its new leaflet for at least ‘frame_cutoff’ consecutive frames. The default is 1, in which case the molecule only needs to move to the opposing leaflet for a single frame for the flip-flop to be successful.
            * **ignore_no_box** (*bool*) - (False) Ignore the absence of box information in the trajectory. If the trajectory does not contain box information, the box will be set to the minimum and maximum positions of the atoms in the trajectory.
            * **remove_tmp** (*bool*) - (True) [WF property] Remove temporal files.
            * **restart** (*bool*) - (False) [WF property] Do not execute if output files exist.
            * **sandbox_path** (*str*) - ("./") [WF property] Parent path to the sandbox directory.

    Examples:
        This is a use example of how to use the building block from Python::

            from biobb_mem.lipyphilic_biobb.lpp_flip_flop import lpp_flip_flop
            prop = {
                'lipid_sel': 'name GL1 GL2 ROH',
            }
            lpp_flip_flop(input_top_path='/path/to/myTopology.tpr',
                                input_traj_path='/path/to/myTrajectory.xtc',
                                input_leaflets_path='/path/to/leaflets.csv',
                                output_flip_flop_path='/path/to/flip_flops.csv',
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

    def __init__(self, input_top_path, input_traj_path,
                 input_leaflets_path, output_flip_flop_path,
                 properties=None, **kwargs) -> None:
        properties = properties or {}

        # Call parent class constructor
        super().__init__(properties)
        self.locals_var_dict = locals().copy()

        # Input/Output files
        self.io_dict = {
            "in": {"input_top_path": input_top_path,
                   "input_traj_path": input_traj_path,
                   "input_leaflets_path": input_leaflets_path},
            "out": {"output_flip_flop_path": output_flip_flop_path}
        }
        self.start = properties.get('start', None)
        self.stop = properties.get('stop', None)
        self.steps = properties.get('steps', None)
        self.lipid_sel = properties.get('lipid_sel', 'all')
        self.frame_cutoff = properties.get('frame_cutoff', 1)
        # Properties specific for BB
        self.ignore_no_box = properties.get('ignore_no_box', True)
        self.properties = properties

        # Check the properties
        self.check_properties(properties)
        self.check_arguments()

    @launchlogger
    def launch(self) -> int:
        """Execute the :class:`LPPFlipFlop <lipyphilic_biobb.lpp_flip_flop.LPPFlipFlop>` object."""

        # Setup Biobb
        if self.check_restart():
            return 0
        self.stage_files()

        # Load the trajectory
        u = mda.Universe(self.stage_io_dict["in"]["input_top_path"], self.stage_io_dict["in"]["input_traj_path"])
        ignore_no_box(u, self.ignore_no_box, self.out_log, self.global_log)
        # Load the leaflets
        leaflets_path = self.stage_io_dict["in"]["input_leaflets_path"]
        if leaflets_path.endswith('.csv'):
            df = pd.read_csv(leaflets_path)
            n_frames = len(df['frame'].unique())
            n_residues = len(df['resindex'].unique())
            leaflets = df['leaflet_index'].values.reshape(n_frames, n_residues).T
        else:  # .npy file
            leaflets = np.load(leaflets_path)
        # Create FlipFlop object
        flip_flop = FlipFlop(
            universe=u,
            lipid_sel=self.lipid_sel,
            leaflets=leaflets,
            frame_cutoff=self.frame_cutoff,
        )
        # Run the analysis
        flip_flop.run(start=self.start, stop=self.stop, step=self.steps)

        # Save the results
        resnames = []
        if flip_flop.flip_flops.size > 0:
            resnames = u.residues.resnames[flip_flop.flip_flops[:, 0]]
        else:
            print('No flip-flop events found.')

        df = pd.DataFrame({
            'resname': resnames,
            'resindex': flip_flop.flip_flops[:, 0],
            'start_frame': flip_flop.flip_flops[:, 1],
            'end_frame': flip_flop.flip_flops[:, 2],
            'end_leaflet': flip_flop.flip_flops[:, 3]
        })

        # Save the DataFrame to a CSV file
        df.to_csv(self.stage_io_dict["out"]["output_flip_flop_path"], index=False)

        # Copy files to host
        self.copy_to_host()
        self.remove_tmp_files()
        self.check_arguments(output_files_created=True, raise_exception=False)

        return self.return_code


def lpp_flip_flop(input_top_path: str, input_traj_path: str, input_leaflets_path: str = None,
                  output_flip_flop_path: str = None, properties: dict = None, **kwargs) -> int:
    """Execute the :class:`LPPFlipFlop <lipyphilic_biobb.lpp_flip_flop.LPPFlipFlop>` class and
    execute the :meth:`launch() <lipyphilic_biobb.lpp_flip_flop.LPPFlipFlop.launch>` method."""
    return LPPFlipFlop(**dict(locals())).launch()


lpp_flip_flop.__doc__ = LPPFlipFlop.__doc__
main = LPPFlipFlop.get_main(lpp_flip_flop, "Find flip-flop events in a lipid bilayer.")

if __name__ == '__main__':
    main()
