#!/usr/bin/env python3

"""Module containing the FATSLiM Area per Lipid class and the command line interface."""
from biobb_common.generic.biobb_object import BiobbObject
from biobb_common.tools.file_utils import launchlogger
from biobb_mem.fatslim.common import ignore_no_box, move_output_file
import MDAnalysis as mda


class FatslimAPL(BiobbObject):
    """
    | biobb_mem FatslimAPL
    | Wrapper of the `FATSLiM area per lipid <https://pythonhosted.org/fatslim/documentation/apl.html>`_ module for area per lipid calculation.
    | FATSLiM is designed to provide efficient and robust analysis of physical parameters from MD trajectories, with a focus on processing large trajectory files quickly.

    Args:
        input_top_path (str): Path to the input topology file. File type: input. `Sample file <https://github.com/bioexcel/biobb_mem/raw/main/biobb_mem/test/data/A01JD/A01JD.pdb>`_. Accepted formats: tpr (edam:format_2333), gro (edam:format_2033), g96 (edam:format_2033), pdb (edam:format_1476), brk (edam:format_2033), ent (edam:format_1476).
        input_traj_path (str) (Optional): Path to the GROMACS trajectory file. File type: input. `Sample file <https://github.com/bioexcel/biobb_mem/raw/main/biobb_mem/test/data/A01JD/A01JD.xtc>`_. Accepted formats: xtc (edam:format_3875), trr (edam:format_3910), cpt (edam:format_2333), gro (edam:format_2033), g96 (edam:format_2033), pdb (edam:format_1476), tng (edam:format_3876).
        input_ndx_path (str) (Optional): Path to the input index NDX file for lipid headgroups and the interacting group. File type: input. `Sample file <https://github.com/bioexcel/biobb_mem/raw/main/biobb_mem/test/data/A01JD/headgroups.ndx>`_. Accepted formats: ndx (edam:format_2033).
        output_csv_path (str): Path to the output CSV file. File type: output. `Sample file <https://github.com/bioexcel/biobb_mem/raw/main/biobb_mem/test/reference/fatslim/apl.csv>`_. Accepted formats: csv (edam:format_3752).
        properties (dic - Python dictionary object containing the tool parameters, not input/output files):
            * **lipid_selection** (*str*) - ("not protein and element P") Headgroups MDAnalysis `selection <https://docs.mdanalysis.org/stable/documentation_pages/selections.html>`_.
            * **protein_selection** (*str*) - ("protein and not element H") Protein selection interacting with the membrane.
            * **cutoff** (*float*) - (3) This option allows user to specify the cutoff distance (in nm) to be used when performing the neighbor search needed by the APL calculation algorithm
            * **limit** (*float*) - (10) This option allows user to specify the upper limit (in nm2) for a valid area per lipid value.
            * **begin_frame** (*int*) - (-1) First frame index to be used for analysis.
            * **end_frame** (*int*) - (-1) Last frame index to be used for analysis.
            * **ignore_no_box** (*bool*) - (False) Ignore the absence of box information in the topology. If the topology does not contain box information, the box will be set to the minimum and maximum positions of the atoms.
            * **return_hydrogen** (*bool*) - (False) Include hydrogen atoms in the output index file.
            * **binary_path** (*str*) - ("fatslim") Path to the fatslim executable binary.
            * **remove_tmp** (*bool*) - (True) [WF property] Remove temporal files.
            * **restart** (*bool*) - (False) [WF property] Do not execute if output files exist.
            * **sandbox_path** (*str*) - ("./") [WF property] Parent path to the sandbox directory.

    Examples:
        This is a use example of how to use the building block from Python::

            from biobb_mem.fatslim.fatslim_apl import fatslim_apl
            prop = {
                'lipid_selection': '(resname DPPC and name P8)',
                'cutoff': 3
            }
            fatslim_apl(input_top_path='/path/to/myTopology.tpr',
                              input_traj_path='/path/to/myTrajectory.xtc',
                              output_csv_path='/path/to/newIndex.ndx',
                              properties=prop)

    Info:
        * wrapped_software:
            * name: FATSLiM
            * version: 0.2.2
            * license: GNU
        * ontology:
            * name: EDAM
            * schema: http://edamontology.org/EDAM.owl

    """

    def __init__(self, input_top_path, output_csv_path, input_traj_path=None, input_ndx_path=None, properties=None, **kwargs) -> None:
        properties = properties or {}

        # Call parent class constructor
        super().__init__(properties)
        self.locals_var_dict = locals().copy()

        # Input/Output files
        self.io_dict = {
            "in": {"input_top_path": input_top_path,
                   "input_traj_path": input_traj_path,
                   "input_ndx_path": input_ndx_path},
            "out": {"output_csv_path": output_csv_path}
        }

        # Properties specific for BB
        self.lipid_selection = properties.get('lipid_selection', "not protein and element P")
        self.protein_selection = properties.get('protein_selection', "protein and not element H")
        self.cutoff = properties.get('cutoff', 3)
        self.limit = properties.get('cutoff', 10)
        self.begin_frame = properties.get('begin_frame', -1)
        self.end_frame = properties.get('end_frame', -1)
        self.ignore_no_box = properties.get('ignore_no_box', False)
        self.binary_path = properties.get('binary_path', 'fatslim')
        self.properties = properties

        # Check the properties
        self.check_properties(properties)
        self.check_arguments()

    @launchlogger
    def launch(self) -> int:
        """Execute the :class:`FatslimAPL <fatslim.fatslim_apl.FatslimAPL>` object."""

        # Setup Biobb
        if self.check_restart():
            return 0
        self.stage_files()

        # Create index file using MDAnalysis
        u = mda.Universe(topology=self.stage_io_dict["in"]["input_top_path"],
                         coordinates=self.stage_io_dict["in"].get("input_traj_path"))
        ignore_no_box(u, self.ignore_no_box, self.out_log, self.global_log)

        # Build the index to select the atoms from the membrane
        if self.stage_io_dict["in"].get('input_ndx_path', None):
            tmp_ndx = self.stage_io_dict["in"]["input_ndx_path"]
        else:
            tmp_ndx = self.create_tmp_file('_apl_inp.ndx')
            with mda.selections.gromacs.SelectionWriter(tmp_ndx, mode='w') as ndx:
                ndx.write(u.select_atoms(self.lipid_selection), name='headgroups')
                ndx.write(u.select_atoms(self.protein_selection), name='protein')

        if self.stage_io_dict["in"]["input_top_path"].endswith('gro'):
            cfg = self.stage_io_dict["in"]["input_top_path"]

        else:
            # Convert topology .gro and add box dimensions if not available in the topology
            cfg = self.create_tmp_file('_output.gro')
            # Save as GRO file with box information
            u.atoms.write(cfg)

        tmp_csv = self.create_tmp_file('_out.csv')
        # Build command
        self.cmd = [
            self.binary_path, "apl",
            "-n", tmp_ndx,
            "-c", cfg,
            "--export-apl-raw", tmp_csv,
            "--apl-cutoff", str(self.cutoff),
            "--apl-limit", str(self.limit),
            "--begin-frame", str(self.begin_frame),
            "--end-frame", str(self.end_frame)
        ]

        # Run Biobb block
        self.run_biobb()
        move_output_file(tmp_csv, self.stage_io_dict["out"]["output_csv_path"],
                         self.out_log, self.global_log)
        # Copy files to host
        self.copy_to_host()
        # Remove temporary files
        self.remove_tmp_files()
        self.check_arguments(output_files_created=True, raise_exception=False)

        return self.return_code


def fatslim_apl(input_top_path: str,
                output_csv_path: str,
                input_traj_path: str = None,
                input_ndx_path: str = None,
                properties: dict = None,
                **kwargs) -> int:
    """Execute the :class:`FatslimAPL <fatslim.fatslim_apl.FatslimAPL>` class and
    execute the :meth:`launch() <fatslim.fatslim_apl.FatslimAPL.launch>` method."""
    return FatslimAPL(**dict(locals())).launch()


fatslim_apl.__doc__ = FatslimAPL.__doc__
main = FatslimAPL.get_main(fatslim_apl, 'Calculate the area per lipid.')

if __name__ == '__main__':
    main()
