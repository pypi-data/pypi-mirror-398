#!/usr/bin/env python3

"""Module containing the PreparePDB class and the command line interface."""
from typing import Optional
from biobb_common.generic.biobb_object import BiobbObject
from biobb_common.tools.file_utils import launchlogger


class CmipPreparePDB(BiobbObject):
    """
    | biobb_cmip CmipPreparePDB
    | Class to add CMIP charges and atom types.
    | Add CMIP charges and atom types to a PDB structure using `biobb_structure_checking <https://anaconda.org/bioconda/biobb_structure_checking>`_.

    Args:
        input_pdb_path (str): Input PDB file path. File type: input. `Sample file <https://github.com/bioexcel/biobb_cmip/raw/master/biobb_cmip/test/data/cmip/1aki.pdb>`_. Accepted formats: pdb (edam:format_1476).
        output_cmip_pdb_path (str): Output PDB file path. File type: output. `Sample file <https://github.com/bioexcel/biobb_cmip/raw/master/biobb_cmip/test/reference/cmip/egfr_cmip.pdb>`_. Accepted formats: pdb (edam:format_1476).
        properties (dict - Python dictionary object containing the tool parameters, not input/output files):
            * **remove_water** (*bool*) - (True) Remove Water molecules.
            * **add_hydrogen** (*bool*) - (True) Add Hydrogen atoms to the structure.
            * **keep_hydrogen** (*bool*) - (False) If **add_hydrogen** is True. All hydrogen atoms will be removed before adding the new ones unless this option is set True.
            * **fix_sidechains** (*bool*) - (True) Complete side chains (heavy atoms, protein only).
            * **fix_backbone_atoms** (*bool*) - (True) Add missing O, OXT backbone atoms.
            * **remove_tmp** (*bool*) - (True) [WF property] Remove temporal files.
            * **restart** (*bool*) - (False) [WF property] Do not execute if output files exist.
            * **sandbox_path** (*str*) - ("./") [WF property] Parent path to the sandbox directory.


    Examples:
        This is a use example of how to use the building block from Python::

            from biobb_cmip.cmip.cmip_prepare_pdb import cmip_prepare_pdb
            prop = { 'restart': False }
            cmip_prepare_pdb(input_pdb_path='/path/to/myStructure.pdb',
                        output_cmip_pdb_path='/path/to/newStructure.pdb',
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

    def __init__(self, input_pdb_path: str, output_cmip_pdb_path: str, properties: Optional[dict] = None, **kwargs) -> None:
        properties = properties or {}

        # Call parent class constructor
        super().__init__(properties)
        self.locals_var_dict = locals().copy()

        # Input/Output files
        self.io_dict = {
            "in": {"input_pdb_path": input_pdb_path},
            "out": {"output_cmip_pdb_path": output_cmip_pdb_path}
        }

        # Properties specific for BB
        self.check_structure_path = properties.get('check_structure_path', 'check_structure')
        self.remove_water = properties.get('remove_water', True)
        self.keep_hydrogen = properties.get('keep_hydrogen', False)
        self.fix_sidechains = properties.get('fix_sidechains', True)
        self.fix_backbone_atoms = properties.get('fix_backbone_atoms', True)

        # Check the properties
        self.check_properties(properties)
        self.check_arguments()

    @launchlogger
    def launch(self) -> int:
        """Execute the :class:`PreparePDB <cmip.prepare_pdb.PreparePDB>` object."""

        # Setup Biobb
        if self.check_restart():
            return 0
        self.stage_files()

        command_list = ""
        if self.remove_water:
            command_list += 'water --remove yes; '

        if self.fix_backbone_atoms:
            command_list += 'backbone --add_caps none; '

        if self.fix_sidechains:
            command_list += 'fixside --fix All; '

        command_list += 'add_hydrogen --add_mode auto '
        if self.keep_hydrogen:
            command_list += ' -keep_h '
        command_list += '--add_charges CMIP'

        self.cmd = [self.check_structure_path,
                    '-v',
                    '-i', self.stage_io_dict["in"]["input_pdb_path"],
                    '-o', self.stage_io_dict["out"]["output_cmip_pdb_path"],
                    '--output_format', 'cmip',
                    '--non_interactive',
                    'command_list',
                    '--list', "'"+command_list+"'"]

        # Run Biobb block
        self.run_biobb()

        # Copy files to host
        self.copy_to_host()

        # remove temporary folder(s)
        self.remove_tmp_files()

        self.check_arguments(output_files_created=True, raise_exception=False)

        return self.return_code


def cmip_prepare_pdb(input_pdb_path: str, output_cmip_pdb_path: str, properties: Optional[dict] = None, **kwargs) -> int:
    """Create :class:`PreparePDB <cmip.prepare_pdb.PreparePDB>` class and
    execute the :meth:`launch() <cmip.prepare_pdb.PreparePDB.launch>` method."""
    return CmipPreparePDB(**dict(locals())).launch()


cmip_prepare_pdb.__doc__ = CmipPreparePDB.__doc__
main = CmipPreparePDB.get_main(cmip_prepare_pdb, "Model the missing atoms in the backbone of a PDB structure.")

if __name__ == '__main__':
    main()
