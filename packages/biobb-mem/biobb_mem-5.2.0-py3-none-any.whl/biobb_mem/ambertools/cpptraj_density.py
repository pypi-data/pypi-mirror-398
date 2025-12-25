#!/usr/bin/env python3

"""Module containing the Cpptraj Density class and the command line interface."""
from pathlib import PurePath
from biobb_common.generic.biobb_object import BiobbObject
from biobb_common.tools.file_utils import launchlogger


class CpptrajDensity(BiobbObject):
    """
    | biobb_mem CpptrajDensity
    | Wrapper of the Ambertools Cpptraj module for calculating density profile along an axis of a given cpptraj compatible trajectory.
    | Cpptraj (the successor to ptraj) is the main program in Ambertools for processing coordinate trajectories and data files. The parameter names and defaults are the same as the ones in the official `Cpptraj manual <https://raw.githubusercontent.com/Amber-MD/cpptraj/master/doc/CpptrajManual.pdf>`_.

    Args:
        input_top_path (str): Path to the input structure or topology file. File type: input. `Sample file <https://github.com/bioexcel/biobb_mem/raw/main/biobb_mem/test/data/ambertools/topology.pdb>`_. Accepted formats: top (edam:format_3881), pdb (edam:format_1476), prmtop (edam:format_3881), parmtop (edam:format_3881), zip (edam:format_3987).
        input_traj_path (str): Path to the input trajectory to be processed. File type: input. `Sample file <https://github.com/bioexcel/biobb_mem/raw/main/biobb_mem/test/data/ambertools/trajectory.xtc>`_. Accepted formats: mdcrd (edam:format_3878), crd (edam:format_3878), cdf (edam:format_3650), netcdf (edam:format_3650), nc (edam:format_3650), restart (edam:format_3886), ncrestart (edam:format_3886), restartnc (edam:format_3886), dcd (edam:format_3878), charmm (edam:format_3887), cor (edam:format_2033), pdb (edam:format_1476), mol2 (edam:format_3816), trr (edam:format_3910), gro (edam:format_2033), binpos (edam:format_3885), xtc (edam:format_3875), cif (edam:format_1477), arc (edam:format_2333), sqm (edam:format_2033), sdf (edam:format_3814), conflib (edam:format_2033).
        output_cpptraj_path (str): Path to the output processed density analysis. File type: output. `Sample file <https://github.com/bioexcel/biobb_mem/raw/main/biobb_mem/test/reference/ambertools/density_default.dat>`_. Accepted formats: dat (edam:format_1637), agr (edam:format_2033), xmgr (edam:format_2033), gnu (edam:format_2033).
        output_traj_path (str) (Optional): Path to the output processed trajectory. File type: output. `Sample file <https://github.com/bioexcel/biobb_mem/raw/main/biobb_mem/test/reference/ambertools/trajectory_out.dcd>`_. Accepted formats: mdcrd (edam:format_3878), crd (edam:format_3878), cdf (edam:format_3650), netcdf (edam:format_3650), nc (edam:format_3650), restart (edam:format_3886), ncrestart (edam:format_3886), restartnc (edam:format_3886), dcd (edam:format_3878), charmm (edam:format_3887), cor (edam:format_2033), pdb (edam:format_1476), mol2 (edam:format_3816), trr (edam:format_3910), gro (edam:format_2033), binpos (edam:format_3885), xtc (edam:format_3875), cif (edam:format_1477), arc (edam:format_2333), sqm (edam:format_2033), sdf (edam:format_3814), conflib (edam:format_2033).
        properties (dic - Python dictionary object containing the tool parameters, not input/output files):
            * **start** (*int*) - (1) [1~100000|1] Starting frame for slicing
            * **end** (*int*) - (-1) [-1~100000|1] Ending frame for slicing
            * **steps** (*int*) - (1) [1~100000|1] Step for slicing
            * **density_type** (*str*) - ("number") Number, mass, partial charge (q) or electron (Ne - q) density. Electron density will be converted to e-/Å3 by dividing the average area spanned by the other two dimensions.
            * **mask** (*str*) - ("*") Arbitrary number of masks for atom selection; a dataset is created and the output will contain entries for each mask.. Default: all atoms.
            * **delta** (*float*) - (0.25) Resolution, i.e. determines number of slices (i.e. histogram bins).
            * **axis** (*str*) - ("z") Coordinate (axis) for density calculation. Vales: x, y, z.
            * **bintype** (*str*) - ("bincenter") Determine whether histogram bin coordinates will be based on bin center (default) or bin edges. Values: bicenter, binedge.
            * **restrict** (*str*) - (None) If specified, only calculate the density within a cylinder or square shape from the specified axis as defined by a distance cutoff. Values: cylinder, square.
            * **cutoff** (*float*) - (None) The distance cutoff for 'restrict'. Required if 'restrict' is specified.
            * **binary_path** (*str*) - ("cpptraj") Path to the cpptraj executable binary.
            * **remove_tmp** (*bool*) - (True) [WF property] Remove temporal files.
            * **restart** (*bool*) - (False) [WF property] Do not execute if output files exist.
            * **sandbox_path** (*str*) - ("./") [WF property] Parent path to the sandbox directory.

    Examples:
        This is a use example of how to use the building block from Python::

            from biobb_mem.ambertools.cpptraj_density import cpptraj_density
            prop = {
                'density_type': 'number'
            }
            cpptraj_density(input_top_path='/path/to/myTopology.top',
                        input_traj_path='/path/to/myTrajectory.xtc',
                        output_cpptraj_path='/path/to/newAnalysis.dat',
                        properties=prop)

    Info:
        * wrapped_software:
            * name: Ambertools Cpptraj
            * version: >=22.5
            * license: GNU
        * ontology:
            * name: EDAM
            * schema: http://edamontology.org/EDAM.owl

    """

    def __init__(self, input_top_path, input_traj_path, output_cpptraj_path,
                 output_traj_path=None, properties=None, **kwargs) -> None:
        properties = properties or {}

        # Call parent class constructor
        super().__init__(properties)
        self.locals_var_dict = locals().copy()

        # Input/Output files
        self.io_dict = {
            "in": {"input_top_path": input_top_path, "input_traj_path": input_traj_path},
            "out": {"output_cpptraj_path": output_cpptraj_path, "output_traj_path": output_traj_path}
        }

        # Properties specific for BB
        self.instructions_file = 'instructions.in'
        self.start = properties.get('start', 1)
        self.end = properties.get('end', -1)
        self.steps = properties.get('steps', 1)
        self.slice = f' {self.start} {self.end} {self.steps}'
        self.density_type = properties.get('density_type', 'number')
        self.mask = properties.get('mask', '*')
        self.delta = properties.get('delta', 0.25)
        self.axis = properties.get('axis', 'z')
        self.bintype = properties.get('bintype', 'bincenter')
        self.restrict = properties.get('restrict', None)
        self.cutoff = properties.get('cutoff', None)
        self.binary_path = properties.get('binary_path', 'cpptraj')
        self.properties = properties

        # Check the properties
        self.check_properties(properties)
        self.check_arguments()

    def create_instructions_file(self, stage_io_dict, out_log, err_log):
        """Creates an input file using the properties file settings."""
        instructions_list = []
        # Different path if container execution or not
        if self.container_path:
            self.instructions_file = str(PurePath(self.container_volume_path).joinpath(self.instructions_file))
        else:
            self.instructions_file = self.create_tmp_file(self.instructions_file)
        instructions_list.append('parm ' + stage_io_dict["in"]["input_top_path"])
        instructions_list.append('trajin ' + stage_io_dict["in"]["input_traj_path"] + self.slice)
        density_command = f'density {self.density_type} out {stage_io_dict["out"]["output_cpptraj_path"]} {self.mask} delta {self.delta} {self.axis} {self.bintype}'
        if self.restrict:
            density_command += f' restrict {self.restrict}'
            if self.cutoff:
                density_command += f' cutoff {self.cutoff}'
        instructions_list.append(density_command)

        # trajout
        if ("output_traj_path" in stage_io_dict["out"]):
            instructions_list.append('trajout ' + stage_io_dict["out"]["output_traj_path"])

        # Create .in file
        with open(self.instructions_file, 'w') as mdp:
            for line in instructions_list:
                mdp.write(line.strip() + '\n')

        return self.instructions_file

    @launchlogger
    def launch(self) -> int:
        """Execute the :class:`CpptrajDensity <ambertools.cpptraj_density.CpptrajDensity>` object."""

        # Setup Biobb
        if self.check_restart():
            return 0
        self.stage_files()

        # create instructions file
        self.create_instructions_file(self.stage_io_dict, self.out_log, self.err_log)
        # create cmd and launch execution
        self.cmd = [self.binary_path, '-i', self.instructions_file]
        # Run Biobb block
        self.run_biobb()
        # Copy files to host
        self.copy_to_host()
        # remove temporary folder(s)
        self.remove_tmp_files()
        self.check_arguments(output_files_created=True, raise_exception=False)
        return self.return_code


def cpptraj_density(input_top_path: str,
                    input_traj_path: str,
                    output_cpptraj_path: str,
                    output_traj_path: str = None,
                    properties: dict = None,
                    **kwargs) -> int:
    """Execute the :class:`CpptrajDensity <ambertools.cpptraj_density.CpptrajDensity>` class and
    execute the :meth:`launch() <ambertools.cpptraj_density.CpptrajDensity.launch>` method."""
    return CpptrajDensity(**dict(locals())).launch()


cpptraj_density.__doc__ = CpptrajDensity.__doc__
main = CpptrajDensity.get_main(cpptraj_density, "Calculates the density along an axis of a given cpptraj compatible trajectory.")

if __name__ == '__main__':
    main()
