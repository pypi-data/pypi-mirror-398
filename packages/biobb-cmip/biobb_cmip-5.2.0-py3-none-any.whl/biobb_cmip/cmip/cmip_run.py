#!/usr/bin/env python3

"""Module containing the Cmip class and the command line interface."""
import os
import json
from typing import Optional
from typing import Any
import shutil
from pathlib import Path
from biobb_common.generic.biobb_object import BiobbObject
from biobb_common.tools import file_utils as fu
from biobb_common.tools.file_utils import launchlogger
from biobb_cmip.cmip.common import create_params_file
from biobb_cmip.cmip.common import params_preset
from biobb_cmip.cmip.common import get_grid


class CmipRun(BiobbObject):
    """
    | biobb_cmip Titration
    | Wrapper class for the CMIP cmip module.
    | The CMIP cmip module. CMIP cmip module compute classical molecular interaction potentials.

    Args:
        input_pdb_path (str): Path to the input PDB file. File type: input. `Sample file <https://raw.githubusercontent.com/bioexcel/biobb_cmip/master/biobb_cmip/test/data/cmip/1kim_h.pdb>`_. Accepted formats: pdb (edam:format_1476).
        input_probe_pdb_path (str): Path to the input probe file in PDB format. File type: input. `Sample file <https://raw.githubusercontent.com/bioexcel/biobb_cmip/master/biobb_cmip/test/data/cmip/RBD-hACE2.RBD.cmip.pdb>`_. Accepted formats: pdb (edam:format_1476).
        output_pdb_path (str) (Optional): Path to the output PDB file. File type: output. `Sample file <https://raw.githubusercontent.com/bioexcel/biobb_cmip/master/biobb_cmip/test/reference/cmip/1kim_neutral.pdb>`_. Accepted formats: pdb (edam:format_1476).
        output_grd_path (str) (Optional): Path to the output grid file in GRD format. File type: output. Accepted formats: grd (edam:format_2330).
        output_cube_path (str) (Optional): Path to the output grid file in cube format. File type: output. Accepted formats: cube (edam:format_2330).
        output_rst_path (str) (Optional): Path to the output restart file. File type: output. Accepted formats: txt (edam:format_2330).
        input_rst_path (str) (Optional): Path to the input restart file. File type: input. Accepted formats: txt (edam:format_2330).
        output_byat_path (str) (Optional): Path to the output atom by atom energy file. File type: output. Accepted formats: txt (edam:format_2330), out (edam:format_2330).
        output_log_path (str) (Optional): Path to the output CMIP log file LOG. File type: output. Accepted formats: log (edam:format_2330).
        input_vdw_params_path (str) (Optional): Path to the CMIP input Van der Waals force parameters, if not provided the CMIP conda installation one is used ("$CONDA_PREFIX/share/cmip/dat/vdwprm"). File type: input. Accepted formats: txt (edam:format_2330).
        input_params_path (str) (Optional): Path to the CMIP input parameters file. File type: input. Accepted formats: txt (edam:format_2330).
        output_json_box_path (str) (Optional): Path to the output CMIP box in JSON format. File type: output. Accepted formats: json (edam:format_3464).
        output_json_external_box_path (str) (Optional): Path to the output external CMIP box in JSON format. File type: output. Accepted formats: json (edam:format_3464).
        input_json_box_path (str) (Optional): Path to the input CMIP box in JSON format. File type: input. Accepted formats: json (edam:format_3464).
        input_json_external_box_path (str) (Optional): Path to the input CMIP box in JSON format. File type: input. Accepted formats: json (edam:format_3464).
        properties (dict - Python dictionary object containing the tool parameters, not input/output files):
            * **execution_type** (*str*) - ("mip_pos") Default options for the params file, each one creates a different params file. Values: check_only (Dry Run of CMIP), mip_pos (MIP O+  Mehler Solmajer dielectric), mip_neg (MIP O-  Mehler Solmajer dielectric), mip_neu (MIP Oxygen Mehler Solmajer dielectric), solvation (Solvation & MEP), pb_interaction_energy (Docking Interaction energy calculation. PB electrostatics), docking (Docking Mehler Solmajer dielectric), docking_rst (Docking from restart file).
            * **params** (*dict*) - ({}) CMIP options specification.
            * **binary_path** (*str*) - ("cmip") Path to the CMIP cmip executable binary.
            * **remove_tmp** (*bool*) - (True) [WF property] Remove temporal files.
            * **restart** (*bool*) - (False) [WF property] Do not execute if output files exist.
            * **sandbox_path** (*str*) - ("./") [WF property] Parent path to the sandbox directory.
            * **container_path** (*str*) - (None)  Path to the binary executable of your container.
            * **container_image** (*str*) - ("cmip/cmip:latest") Container Image identifier.
            * **container_volume_path** (*str*) - ("/data") Path to an internal directory in the container.
            * **container_working_dir** (*str*) - (None) Path to the internal CWD in the container.
            * **container_user_id** (*str*) - (None) User number id to be mapped inside the container.
            * **container_shell_path** (*str*) - ("/bin/bash") Path to the binary executable of the container shell.


    Examples:
        This is a use example of how to use the building block from Python::

            from biobb_cmip.cmip.cmip import cmip
            prop = { 'binary_path': 'cmip' }
            cmip(input_pdb_path='/path/to/myStructure.pdb',
                      output_pdb_path='/path/to/newStructure.pdb',
                      output_log_path='/path/to/newStructureLog.log',
                      properties=prop)

    Info:
        * wrapped_software:
            * name: CMIP cmip
            * version: 2.7.0
            * license: Apache-2.0
        * ontology:
            * name: EDAM
            * schema: http://edamontology.org/EDAM.owl
    """

    def __init__(self, input_pdb_path: str, input_probe_pdb_path: Optional[str] = None, output_pdb_path: Optional[str] = None,
                 output_grd_path: Optional[str] = None, output_cube_path: Optional[str] = None, output_rst_path: Optional[str] = None,
                 input_rst_path: Optional[str] = None, output_byat_path: Optional[str] = None, output_log_path: Optional[str] = None,
                 input_vdw_params_path: Optional[str] = None, input_params_path: Optional[str] = None, output_json_box_path: Optional[str] = None,
                 output_json_external_box_path: Optional[str] = None, input_json_box_path: Optional[str] = None,
                 input_json_external_box_path: Optional[str] = None, properties: Optional[dict] = None, **kwargs) -> None:

        properties = properties or {}

        # Call parent class constructor
        super().__init__(properties)
        self.locals_var_dict = locals().copy()

        # Input/Output files
        self.io_dict = {
            "in": {"input_pdb_path": input_pdb_path, "input_probe_pdb_path": input_probe_pdb_path,
                   "input_vdw_params_path": input_vdw_params_path, "input_params_path": input_params_path,
                   "input_json_box_path": input_json_box_path,
                   "input_json_external_box_path": input_json_external_box_path,
                   "input_rst_path": input_rst_path},
            "out": {"output_pdb_path": output_pdb_path, "output_grd_path": output_grd_path,
                    "output_cube_path": output_cube_path, "output_rst_path": output_rst_path,
                    "output_byat_path": output_byat_path, "output_log_path": output_log_path,
                    "output_json_box_path": output_json_box_path,
                    "output_json_external_box_path": output_json_external_box_path}
        }

        # Properties specific for BB
        self.binary_path = properties.get('binary_path', 'cmip')
        self.execution_type = properties.get('execution_type', 'mip_pos')
        self.params = {k: str(v) for k, v in properties.get('params', dict()).items()}

        if not self.io_dict['in'].get('input_vdw_params_path'):
            self.io_dict['in']['input_vdw_params_path'] = f"{os.environ.get('CONDA_PREFIX')}/share/cmip/dat/vdwprm"
        self.io_dict['in']['combined_params_path'] = properties.get('combined_params_path', 'params')

        # Check the properties
        self.check_properties(properties)
        self.check_arguments()

    @launchlogger
    def launch(self) -> int:
        """Execute the :class:`Cmip <cmip.cmip.Cmip>` object."""

        # Setup Biobb
        if self.check_restart():
            return 0

        # Check if output_pdb_path ends with ".pdb" and does not contain underscores
        if self.io_dict['out']['output_pdb_path']:
            if (not self.io_dict['out']['output_pdb_path'].endswith('.pdb')) or \
               ("_" in str(Path(self.io_dict['out']['output_pdb_path']).name)):
                fu.log(f"ERROR: output_pdb_path ({self.io_dict['out']['output_pdb_path']}) "
                       f"name must end in .pdb and not contain underscores", self.out_log, self.global_log)
                raise ValueError(f"ERROR: output_pdb_path ({self.io_dict['out']['output_pdb_path']})"
                                 f"name must end in .pdb and not contain underscores")

        params_preset_dict: dict[str, Any] = params_preset(execution_type=self.execution_type)
        if self.io_dict['in']["input_json_external_box_path"]:
            params_preset_dict["readgrid0"] = 0
            origin, size, grid_params = get_grid(self.io_dict['in']["input_json_external_box_path"])
            params_preset_dict['grid_int0'] = \
                f"INTX0={grid_params['INT'][0]},INTY0={grid_params['INT'][1]},INTZ0={grid_params['INT'][2]}"
            params_preset_dict['grid_cen0'] = \
                f"CENX0={grid_params['CEN'][0]},CENY0={grid_params['CEN'][1]},CENZ0={grid_params['CEN'][2]}"
            params_preset_dict['grid_dim0'] = \
                f"DIMX0={grid_params['DIM'][0]},DIMY0={grid_params['DIM'][1]},DIMZ0={grid_params['DIM'][2]}"

        if self.io_dict['in']["input_json_box_path"]:
            params_preset_dict["readgrid"] = 0
            origin, size, grid_params = get_grid(self.io_dict['in']["input_json_box_path"])
            params_preset_dict['grid_int'] = \
                f"INTX={grid_params['INT'][0]},INTY={grid_params['INT'][1]},INTZ={grid_params['INT'][2]}"
            params_preset_dict['grid_cen'] = \
                f"CENX={grid_params['CEN'][0]},CENY={grid_params['CEN'][1]},CENZ={grid_params['CEN'][2]}"
            params_preset_dict['grid_dim'] = \
                f"DIMX={grid_params['DIM'][0]},DIMY={grid_params['DIM'][1]},DIMZ={grid_params['DIM'][2]}"

        if self.io_dict['out']['output_json_box_path'] or self.io_dict['out']['output_json_external_box_path']:
            params_preset_dict['WRITELOG'] = 1
            key_value_log_dir = fu.create_unique_dir()
            self.io_dict['out']['key_value_log_path'] = str(Path(key_value_log_dir).joinpath("key_value_cmip_log.log"))
            self.tmp_files.append(key_value_log_dir)

        # Restart OUT
        if self.io_dict["out"].get("output_rst_path"):
            params_preset_dict['FULLRST'] = 1  # type: ignore
            params_preset_dict['OREST'] = 1

        # Restart IN
        if self.io_dict['in']["input_rst_path"]:
            params_preset_dict['IREST'] = 2
            if not self.io_dict["out"].get("output_rst_path"):
                self.io_dict["out"]["output_rst_path"] = fu.create_unique_file_path()
            shutil.copy2(self.io_dict['in']["input_rst_path"], self.io_dict["out"]["output_rst_path"])

        else:
            params_preset_dict['IREST'] = 0

        combined_params_dir = fu.create_unique_dir()
        self.io_dict['in']['combined_params_path'] = create_params_file(
            output_params_path=str(Path(combined_params_dir).joinpath(self.io_dict['in']['combined_params_path'])),
            input_params_path=self.io_dict['in'].get('input_params_path'),
            params_preset_dict=params_preset_dict,
            params_properties_dict=self.params)

        self.stage_files()

        self.cmd = [self.binary_path,
                    '-i', self.stage_io_dict['in']['combined_params_path'],
                    '-vdw', self.stage_io_dict['in']['input_vdw_params_path'],
                    '-hs', self.stage_io_dict['in']['input_pdb_path']]

        if self.stage_io_dict["in"].get("input_probe_pdb_path") and Path(
                self.io_dict["in"].get("input_probe_pdb_path", "")).exists():
            self.cmd.append('-pr')
            self.cmd.append(self.stage_io_dict["in"].get("input_probe_pdb_path"))

        if self.stage_io_dict["out"].get("output_pdb_path"):
            self.cmd.append('-outpdb')
            self.cmd.append(self.stage_io_dict['out']['output_pdb_path'])

        if self.stage_io_dict["out"].get("output_grd_path"):
            self.cmd.append('-grdout')
            self.cmd.append(self.stage_io_dict["out"]["output_grd_path"])

        if self.stage_io_dict["out"].get("output_cube_path"):
            self.cmd.append('-cube')
            self.cmd.append(self.stage_io_dict["out"]["output_cube_path"])

        if self.stage_io_dict["out"].get("output_rst_path"):
            self.cmd.append('-rst')
            self.cmd.append(self.stage_io_dict["out"]["output_rst_path"])

        if self.stage_io_dict["out"].get("output_byat_path"):
            self.cmd.append('-byat')
            self.cmd.append(self.stage_io_dict["out"]["output_byat_path"])

        if self.stage_io_dict["out"].get("output_log_path"):
            self.cmd.append('-o')
            self.cmd.append(self.stage_io_dict["out"]["output_log_path"])

        if self.stage_io_dict['out'].get('output_json_box_path') or self.stage_io_dict['out'].get('output_json_external_box_path'):
            self.cmd.append('-l')
            self.cmd.append(self.stage_io_dict["out"]["key_value_log_path"])

        # Run Biobb block
        self.run_biobb()

        # CMIP removes or adds a .pdb extension from pdb output name
        # manual copy_to_host or unstage
        if self.io_dict['out'].get('output_pdb_path'):
            output_pdb_path = str(Path(self.stage_io_dict["unique_dir"]).joinpath(Path(self.io_dict['out'].get('output_pdb_path', '')).name))
            if Path(output_pdb_path[:-4]).exists():
                shutil.move(output_pdb_path[:-4], self.io_dict['out'].get('output_pdb_path', ''))
            elif Path(output_pdb_path + ".pdb").exists():
                shutil.move(output_pdb_path + ".pdb", self.io_dict['out'].get('output_pdb_path', ''))
            elif not Path(output_pdb_path).exists():
                fu.log(f"WARNING: File not found output_pdb_path: {output_pdb_path}", self.out_log, self.global_log)

        # Replace "ATOMTM" tag for "ATOM  "

        output_pdb_path = self.io_dict['out'].get('output_pdb_path', '')
        if output_pdb_path:
            if Path(output_pdb_path).exists():
                with open(output_pdb_path) as pdb_file:
                    list_pdb_lines = pdb_file.readlines()
                with open(output_pdb_path, 'w') as pdb_file:
                    for line in list_pdb_lines:
                        pdb_file.write(line.replace('ATOMTM', 'ATOM  '))
            else:
                fu.log(f"WARNING: File not found output_pdb_path: {output_pdb_path} Abs Path: {Path(output_pdb_path).resolve()}", self.out_log, self.global_log)

        # Create json_box_path file from CMIP log file
        if self.io_dict['out'].get('output_json_box_path'):
            origin, size, grid_params = get_grid(self.stage_io_dict["out"]["output_log_path"])
            grid_params['DIM'] = (int(grid_params['DIM'][0]),
                                  int(grid_params['DIM'][1]),
                                  int(grid_params['DIM'][2]))
            size_dict = {'x': round(grid_params['DIM'][0] * grid_params['INT'][0], 3),
                         'y': round(grid_params['DIM'][1] * grid_params['INT'][1], 3),
                         'z': round(grid_params['DIM'][2] * grid_params['INT'][2], 3)}
            origin_dict = {'x': round(grid_params['CEN'][0] - size_dict['x'] / 2, 3),
                           'y': round(grid_params['CEN'][1] - size_dict['y'] / 2, 3),
                           'z': round(grid_params['CEN'][0] - size_dict['z'] / 2, 3)}
            grid_dict = {'origin': origin_dict,
                         'size': size_dict,
                         'params': grid_params}
            with open(self.io_dict['out'].get('output_json_box_path', ''), 'w') as json_file:
                json_file.write(json.dumps(grid_dict, indent=4))

        # Create external_json_box_path file from CMIP log file
        if self.io_dict['out'].get('output_json_external_box_path'):
            origin, size, grid_params = get_grid(self.stage_io_dict["out"]["output_log_path"], True)
            grid_params['DIM'] = (int(grid_params['DIM'][0]),
                                  int(grid_params['DIM'][1]),
                                  int(grid_params['DIM'][2]))
            size_dict = {'x': round(grid_params['DIM'][0] * grid_params['INT'][0], 3),
                         'y': round(grid_params['DIM'][1] * grid_params['INT'][1], 3),
                         'z': round(grid_params['DIM'][2] * grid_params['INT'][2], 3)}
            origin_dict = {'x': round(grid_params['CEN'][0] - size_dict['x'] / 2, 3),
                           'y': round(grid_params['CEN'][1] - size_dict['y'] / 2, 3),
                           'z': round(grid_params['CEN'][0] - size_dict['z'] / 2, 3)}
            grid_dict = {'origin': origin_dict,
                         'size': size_dict,
                         'params': grid_params}
            with open(self.io_dict['out'].get('output_json_external_box_path', ''), 'w') as json_file:
                json_file.write(json.dumps(grid_dict, indent=4))

        # Copy files to host
        self.copy_to_host()

        # remove temporary folder(s)
        self.tmp_files.append(combined_params_dir)
        self.remove_tmp_files()

        self.check_arguments(output_files_created=True, raise_exception=False)

        return self.return_code


def cmip_run(input_pdb_path: str, input_probe_pdb_path: Optional[str] = None, output_pdb_path: Optional[str] = None,
             output_grd_path: Optional[str] = None, output_cube_path: Optional[str] = None, output_rst_path: Optional[str] = None,
             output_byat_path: Optional[str] = None, output_log_path: Optional[str] = None,
             input_vdw_params_path: Optional[str] = None, input_params_path: Optional[str] = None, output_json_box_path: Optional[str] = None,
             output_json_external_box_path: Optional[str] = None, input_json_box_path: Optional[str] = None,
             input_json_external_box_path: Optional[str] = None, properties: Optional[dict] = None, **kwargs) -> int:
    """Create :class:`Cmip <cmip.cmip.Cmip>` class and
    execute the :meth:`launch() <cmip.cmip.Cmip.launch>` method."""
    return CmipRun(**dict(locals())).launch()


cmip_run.__doc__ = CmipRun.__doc__
main = CmipRun.get_main(cmip_run, "Wrapper of the CMIP cmip module.")

if __name__ == '__main__':
    main()
