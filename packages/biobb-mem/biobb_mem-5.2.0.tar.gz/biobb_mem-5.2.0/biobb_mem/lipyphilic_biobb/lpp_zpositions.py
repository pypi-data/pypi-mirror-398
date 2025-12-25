#!/usr/bin/env python3

"""Module containing the Lipyphilic ZPositions class and the command line interface."""

from biobb_common.generic.biobb_object import BiobbObject
from biobb_common.tools.file_utils import launchlogger
import MDAnalysis as mda
from biobb_mem.lipyphilic_biobb.common import ignore_no_box
from lipyphilic.analysis.z_positions import ZPositions
import pandas as pd
import numpy as np


class LPPZPositions(BiobbObject):
    """
    | biobb_mem LPPZPositions
    | Wrapper of the LiPyphilic ZPositions module for calculating the z distance of lipids to the bilayer center.
    | LiPyphilic is a Python package for analyzing MD simulations of lipid bilayers. The parameter names and defaults are the same as the ones in the official `Lipyphilic documentation <https://lipyphilic.readthedocs.io/en/latest/reference/analysis/z_pos.html>`_.

    Args:
        input_top_path (str): Path to the input structure or topology file. File type: input. `Sample file <https://github.com/bioexcel/biobb_mem/raw/main/biobb_mem/test/data/A01JD/A01JD.pdb>`_. Accepted formats: crd (edam:3878), gro (edam:2033), mdcrd (edam:3878), mol2 (edam:3816), pdb (edam:1476), pdbqt (edam:1476), prmtop (edam:3881), psf (edam:3882), top (edam:3881), tpr (edam:2333), xml (edam:2332), xyz (edam:3887).
        input_traj_path (str): Path to the input trajectory to be processed. File type: input. `Sample file <https://github.com/bioexcel/biobb_mem/raw/main/biobb_mem/test/data/A01JD/A01JD.xtc>`_. Accepted formats: arc (edam:2333), crd (edam:3878), dcd (edam:3878), ent (edam:1476), gro (edam:2033), inpcrd (edam:3878), mdcrd (edam:3878), mol2 (edam:3816), nc (edam:3650), pdb (edam:1476), pdbqt (edam:1476), restrt (edam:3886), tng (edam:3876), trr (edam:3910), xtc (edam:3875), xyz (edam:3887).
        output_positions_path (str): Path to the output z positions. File type: output. `Sample file <https://github.com/bioexcel/biobb_mem/raw/main/biobb_mem/test/reference/lipyphilic_biobb/zpositions.csv>`_. Accepted formats: csv (edam:format_3752).
        properties (dic - Python dictionary object containing the tool parameters, not input/output files):
            * **start** (*int*) - (None) Starting frame for slicing.
            * **stop** (*int*) - (None) Ending frame for slicing.
            * **steps** (*int*) - (None) Step for slicing.
            * **lipid_sel** (*str*) - ("all") Selection string for the lipids in a membrane. The selection should cover **all** residues in the membrane, including cholesterol.
            * **height_sel** (*str*) - ("all") Atom selection for the molecules for which the z position will be calculated.
            * **n_bins** (*int*) - (1) Number of bins in *x* and *y* to use to create a grid of membrane patches. Local membrane midpoints are computed for each patch, and lipids assigned a leaflet based on the distance to their local membrane midpoint. The default is `1`, which is equivalent to computing a single global midpoint.
            * **ignore_no_box** (*bool*) - (False) Ignore the absence of box information in the trajectory. If the trajectory does not contain box information, the box will be set to the minimum and maximum positions of the atoms in the trajectory.
            * **remove_tmp** (*bool*) - (True) [WF property] Remove temporal files.
            * **restart** (*bool*) - (False) [WF property] Do not execute if output files exist.
            * **sandbox_path** (*str*) - ("./") [WF property] Parent path to the sandbox directory.

    Examples:
        This is a use example of how to use the building block from Python::

            from biobb_mem.lipyphilic_biobb.lpp_zpositions import lpp_zpositions
            prop = {
                'lipid_sel': 'name GL1 GL2 ROH',
            }
            lpp_zpositions(input_top_path='/path/to/myTopology.tpr',
                                input_traj_path='/path/to/myTrajectory.xtc',
                                output_positions_path='/path/to/zpositions.csv.csv',
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

    def __init__(self, input_top_path, input_traj_path, output_positions_path,
                 properties=None, **kwargs) -> None:
        properties = properties or {}

        # Call parent class constructor
        super().__init__(properties)
        self.locals_var_dict = locals().copy()

        # Input/Output files
        self.io_dict = {
            "in": {"input_top_path": input_top_path, "input_traj_path": input_traj_path},
            "out": {"output_positions_path": output_positions_path}
        }

        self.start = properties.get('start', None)
        self.stop = properties.get('stop', None)
        self.steps = properties.get('steps', None)
        self.lipid_sel = properties.get('lipid_sel', 'all')
        self.height_sel = properties.get('height_sel', 'all')
        self.n_bins = properties.get('n_bins', 1)
        self.ignore_no_box = properties.get('ignore_no_box', False)
        # Properties specific for BB
        self.remove_tmp = properties.get('remove_tmp', True)
        self.restart = properties.get('restart', False)
        self.sandbox_path = properties.get('sandbox_path', "./")

        # Check the properties
        self.check_properties(properties)
        self.check_arguments()

    @launchlogger
    def launch(self) -> int:
        """Execute the :class:`LPPZPositions <lipyphilic_biobb.lpp_zpositions.LPPZPositions>` object."""

        # Setup Biobb
        if self.check_restart():
            return 0
        self.stage_files()

        # Load the trajectory
        u = mda.Universe(self.stage_io_dict["in"]["input_top_path"], self.stage_io_dict["in"]["input_traj_path"])
        ignore_no_box(u, self.ignore_no_box, self.out_log, self.global_log)

        # Create ZPositions object
        positions = ZPositions(
            universe=u,
            lipid_sel=self.lipid_sel,
            height_sel=self.height_sel,
            n_bins=self.n_bins
        )
        # Run the analysis
        positions.run(start=self.start, stop=self.stop, step=self.steps)
        # Save the results
        frames = positions.z_positions.shape[1]
        resnames = np.repeat(positions._height_atoms.resnames, frames)
        resindices = np.tile(positions._height_atoms.resindices, frames)
        frame_numbers = np.repeat(np.arange(frames), positions._height_atoms.n_residues)

        df = pd.DataFrame({
            'resname': resnames,
            'resindex': resindices,
            'frame': frame_numbers,
            'zposition': positions.z_positions.T.flatten()
        })

        # Save the DataFrame to a CSV file
        df.to_csv(self.stage_io_dict["out"]["output_positions_path"], index=False)

        # Copy files to host
        self.copy_to_host()
        self.remove_tmp_files()
        self.check_arguments(output_files_created=True, raise_exception=False)

        return self.return_code


def lpp_zpositions(input_top_path: str, input_traj_path: str, output_positions_path: str = None, properties: dict = None, **kwargs) -> int:
    """Execute the :class:`LPPZPositions <lipyphilic_biobb.lpp_zpositions.LPPZPositions>` class and
    execute the :meth:`launch() <lipyphilic_biobb.lpp_zpositions.LPPZPositions.launch>` method."""
    return LPPZPositions(**dict(locals())).launch()


lpp_zpositions.__doc__ = LPPZPositions.__doc__
main = LPPZPositions.get_main(lpp_zpositions, "Calculate the z distance in of lipids to the bilayer center.")


def frame_df(output_positions_path):
    """
    Processes a CSV file containing z-position data and calculates the mean positive, mean negative,
    thickness, and standard deviation of thickness for each frame.

    Args:
        output_positions_path (str): Path to the CSV file containing z-position data.
    Returns:
        pandas.DataFrame: A DataFrame with the following columns:
            - mean_positive: Mean of positive z-positions for each frame.
            - mean_negative: Mean of negative z-positions for each frame.
            - thickness: Difference between mean_positive and mean_negative for each frame.
            - std_thickness: Standard deviation of the absolute z-positions for each frame.
    """

    df = pd.read_csv(output_positions_path)
    grouped = df.groupby('frame')['zposition'].agg(
        mean_positive=lambda x: x[x > 0].mean(),
        mean_negative=lambda x: x[x < 0].mean(),
        std_positive=lambda x: x[x > 0].std(),
        std_negative=lambda x: x[x < 0].std()
    )
    grouped['thickness'] = grouped['mean_positive'] - grouped['mean_negative']
    grouped['std_thickness'] = df.groupby('frame')['zposition'].apply(lambda x: x.abs().std())
    return grouped


if __name__ == '__main__':
    main()
