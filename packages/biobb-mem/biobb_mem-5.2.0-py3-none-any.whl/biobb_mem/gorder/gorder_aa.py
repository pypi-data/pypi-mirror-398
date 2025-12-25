#!/usr/bin/env python3

"""Module containing the gorder all atom class and the command line interface."""
from biobb_common.generic.biobb_object import BiobbObject
from biobb_common.tools.file_utils import launchlogger
import gorder


class GorderAA(BiobbObject):
    """
    | biobb_mem GorderAA
    | Wrapper of the gorder atomistic module for computing lipid order parameters per atom for carbon tails.
    | `gorder <https://ladme.github.io/gorder-manual/aaorder_basics.html>`_ uses `GSL <https://ladme.github.io/gsl-guide/>`_ for all its selections.

    Args:
        input_top_path (str): Path to the input structure or topology file. File type: input. `Sample file <https://github.com/bioexcel/biobb_mem/raw/main/biobb_mem/test/data/A01IP/A01IP.tpr>`_. Accepted formats: tpr (edam:format_2333).
        input_traj_path (str): Path to the input trajectory to be processed. File type: input. `Sample file <https://github.com/bioexcel/biobb_mem/raw/main/biobb_mem/test/data/A01IP/A01IP.xtc>`_. Accepted formats: xtc (edam:format_3875), trr (edam:format_3910), gro (edam:format_2033).
        output_order_path (str): Path to results of the order analysis. File type: output. `Sample file <https://github.com/bioexcel/biobb_mem/raw/main/biobb_mem/test/reference/gorder/order_aa.yaml>`_. Accepted formats: yaml (edam:format_3570), xvg (edam:format_2330), csv (edam:format_3752).
        properties (dic - Python dictionary object containing the tool parameters, not input/output files):
            * **heavy_atoms** (*str*) - ("@membrane and name r'C3.+|C2.+'") Selection query specifying the heavy atoms to be used in the analysis (typically carbon atoms in lipid tails).
            * **hydrogens** (*str*) - ("@membrane and element name hydrogen") Selection query specifiying the hydrogen atoms to be used in the analysis (only those bonded to heavy atoms will be considered).
            * **handle_pbc** (*bool*) - (True) If False, ignores periodic boundary conditions (PBC).
            * **remove_tmp** (*bool*) - (True) [WF property] Remove temporal files.
            * **restart** (*bool*) - (False) [WF property] Do not execute if output files exist.
            * **sandbox_path** (*str*) - ("./") [WF property] Parent path to the sandbox directory.

    Examples:
        This is a use example of how to use the building block from Python::

            from biobb_mem.gorder.gorder_aa import gorder_aa
            prop = {
                'handle_pbc': False
            }
            gorder_aa(input_top_path='/path/to/myTopology.tpr',
                      input_traj_path='/path/to/myTrajectory.xtc',
                      output_order_path='/path/to/orderAnalysis.yaml',
                      properties=prop)

    Info:
        * wrapped_software:
            * name: gorder
            * version: 1.1.0
            * license: MIT
        * ontology:
            * name: EDAM
            * schema: http://edamontology.org/EDAM.owl

    """

    def __init__(self,
                 input_top_path,
                 input_traj_path,
                 output_order_path=None,
                 properties=None,
                 **kwargs) -> None:
        properties = properties or {}

        # Call parent class constructor
        super().__init__(properties)
        self.locals_var_dict = locals().copy()

        # Input/Output files
        self.io_dict = {
            "in": {
                "input_top_path": input_top_path,
                "input_traj_path": input_traj_path,
            },
            "out": {
                "output_order_path": output_order_path
            }
        }

        # Properties specific for BB
        self.heavy_atoms = properties.get('heavy_atoms', "@membrane and name r'C3.+|C2.+'")
        self.hydrogens = properties.get('hydrogens', '@membrane and element name hydrogen')
        self.handle_pbc = properties.get('handle_pbc', True)
        self.properties = properties

        # Check the properties
        self.check_properties(properties)
        self.check_arguments()

    @launchlogger
    def launch(self) -> int:
        """Execute the :class:`GorderAA <gorder.gorder_aa.GorderAA>` object."""

        # Setup Biobb
        if self.check_restart():
            return 0
        self.stage_files()

        out = self.stage_io_dict["out"]["output_order_path"]
        # Run Biobb block
        analysis = gorder.Analysis(
            structure=self.stage_io_dict["in"]["input_top_path"],
            trajectory=self.stage_io_dict["in"]["input_traj_path"],
            analysis_type=gorder.analysis_types.AAOrder(self.heavy_atoms, self.hydrogens),
            output_yaml=out if out.endswith('.yaml') else None,
            output_csv=out if out.endswith('.csv') else None,
            output_xvg=out if out.endswith('.xvg') else None,
            handle_pbc=self.handle_pbc,
        )

        results = analysis.run()
        results.write()

        # Copy files to host
        self.copy_to_host()
        self.remove_tmp_files()

        return self.return_code


def gorder_aa(input_top_path: str,
              input_traj_path: str,
              output_order_path: str = None,
              properties: dict = None,
              **kwargs) -> int:
    """Create :class:`GorderAA <gorder.gorder_aa.GorderAA>` class and
    execute :meth:`launch() <gorder.gorder_aa.GorderAA.launch>` method"""
    return GorderAA(**dict(locals())).launch()


gorder_aa.__doc__ = GorderAA.__doc__
main = GorderAA.get_main(gorder_aa, "Compute atomistic lipid order parameters using gorder order tool.")

if __name__ == '__main__':
    main()
