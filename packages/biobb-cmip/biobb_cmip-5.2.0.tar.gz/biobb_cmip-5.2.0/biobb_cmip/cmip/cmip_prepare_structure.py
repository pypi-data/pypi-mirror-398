#!/usr/bin/env python3

"""Module containing the PrepareStructure class and the command line interface."""
from typing import Optional
import warnings
from pathlib import Path
from biobb_common.generic.biobb_object import BiobbObject
from biobb_common.tools import file_utils as fu
from biobb_common.tools.file_utils import launchlogger

# Write the CMIP PDB
from biobb_cmip.cmip.common import write_cmip_pdb
# Dani's methods using a topology and a PDB file
from biobb_cmip.cmip.common import get_topology_cmip_elements_canonical
from biobb_cmip.cmip.common import get_topology_charges
# JLG methods using just the PDB file
from biobb_cmip.cmip.common import get_pdb_charges
from biobb_cmip.cmip.common import get_pdb_cmip_elements_canonical


class CmipPrepareStructure(BiobbObject):
    """
    | biobb_cmip PrepareStructure
    | Generate a CMIP suitable PDB input.
    | Generate a CMIP suitable PDB input from a common PDB file or a Topology + PDB file.

    Args:
        input_pdb_path (str): Path to the input PDB file. File type: input. `Sample file <https://github.com/bioexcel/biobb_cmip/raw/master/biobb_cmip/test/data/cmip/egfr.pdb>`_. Accepted formats: pdb (edam:format_1476).
        input_topology_path (str) (Optional): Path to the input topology path. File type: input. `Sample file <https://github.com/bioexcel/biobb_cmip/raw/master/biobb_cmip/test/data/cmip/egfr_topology.zip>`_. Accepted formats: zip (edam:format_3987), top (edam:format_3880), psf (edam:format_3882), prmtop (edam:format_3881).
        output_cmip_pdb_path (str): Path to the output PDB file. File type: output. `Sample file <https://github.com/bioexcel/biobb_cmip/raw/master/biobb_cmip/test/reference/cmip/egfr_cmip.pdb>`_. Accepted formats: pdb (edam:format_1476).
        properties (dict - Python dictionary object containing the tool parameters, not input/output files):
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

            from biobb_cmip.cmip.prepare_structure import prepare_structure
            prop = { }
            prepare_structure(input_pdb_path='/path/to/myStructure.pdb',
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

    def __init__(self, input_pdb_path: str, output_cmip_pdb_path: str, input_topology_path: Optional[str] = None, properties: Optional[dict] = None, **kwargs) -> None:
        properties = properties or {}

        # Call parent class constructor
        super().__init__(properties)
        self.locals_var_dict = locals().copy()

        # Input/Output files
        self.io_dict = {
            "in": {"input_pdb_path": input_pdb_path, "input_topology_path": input_topology_path},
            "out": {"output_cmip_pdb_path": output_cmip_pdb_path}
        }

        # Check the properties
        self.check_properties(properties)
        self.check_arguments()

    @launchlogger
    def launch(self) -> int:
        """Execute the :class:`Cmip <cmip.cmip.PrepareStructure>` object."""
        # Setup Biobb
        if self.check_restart():
            return 0

        # Dani's method
        if self.io_dict['in']['input_topology_path']:
            top_file = self.io_dict['in']['input_topology_path']
            if self.io_dict['in']['input_topology_path'].lower().endswith(".zip"):
                # Unzip topology to topology_out
                top_file = fu.unzip_top(zip_file=self.io_dict['in']['input_topology_path'], out_log=self.out_log)
                top_dir = str(Path(top_file).parent)
                self.tmp_files.append(top_dir)

            with warnings.catch_warnings():
                warnings.filterwarnings("ignore", category=UserWarning)
                fu.log(f'Reading: {top_file} to extract charges', self.out_log, self.global_log)
                charges_list = get_topology_charges(top_file)
                fu.log(f'Reading: {top_file} to extract elements', self.out_log, self.global_log)
                elements_list = get_topology_cmip_elements_canonical(top_file)
                two_letter_elements = {"CL": "Cl", "NA": "Na", "ZN": "Zn", "MG": "Mg"}
                elements_list = [two_letter_elements.get(element, element) for element in elements_list]

        # JLG's method
        else:
            charges_list = get_pdb_charges(self.io_dict['in']['input_pdb_path'])
            elements_list = get_pdb_cmip_elements_canonical(self.io_dict['in']['input_pdb_path'])

        write_cmip_pdb(self.io_dict['in']['input_pdb_path'],
                       self.io_dict['out']['output_cmip_pdb_path'],
                       charges_list,
                       elements_list)

        ###################################

        # remove temporary folder(s)
        self.remove_tmp_files()

        self.check_arguments(output_files_created=True, raise_exception=False)

        return 0


def cmip_prepare_structure(input_pdb_path: str, output_cmip_pdb_path: str, input_topology_path: Optional[str] = None,
                           properties: Optional[dict] = None, **kwargs) -> int:
    """Create :class:`Cmip <cmip.cmip.PrepareStructure>` class and
    execute the :meth:`launch() <cmip.cmip.PrepareStructure.launch>` method."""
    return CmipPrepareStructure(**dict(locals())).launch()


cmip_prepare_structure.__doc__ = CmipPrepareStructure.__doc__
main = CmipPrepareStructure.get_main(cmip_prepare_structure, "Wrapper of the cmip prepare_structure module.")

if __name__ == '__main__':
    main()
