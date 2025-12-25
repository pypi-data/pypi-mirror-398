""" Common functions for package biobb_cmip.cmip """
import os
import re
import json
from pathlib import Path
from typing import Union, Any, Optional
import MDAnalysis as mda  # type: ignore
from MDAnalysis.topology.guessers import guess_atom_element  # type: ignore
import uuid
import logging
import biobb_common.tools.file_utils as fu


def get_grid(cmip_log_path: Union[str, Path], external: bool = False) -> tuple[tuple[float, float, float], tuple[float, float, float], dict[str, tuple[float, float, float]]]:
    with open(cmip_log_path) as log_file:
        first_line = log_file.readline().strip()
    if first_line.startswith("titleParam"):
        return _get_grid_from_key_value(cmip_log_path, external)
    elif first_line.startswith("{"):
        return _get_grid_from_box_file(cmip_log_path)
    return _get_grid_from_text(cmip_log_path, external)


def _get_grid_from_box_file(cmip_box_path: Union[str, Path]) -> tuple[tuple[float, float, float], tuple[float, float, float], dict[str, tuple[float, float, float]]]:
    with open(cmip_box_path) as json_file:
        grid_dict = json.load(json_file)
    origin = grid_dict['origin']['x'], grid_dict['origin']['y'], grid_dict['origin']['z']
    size = grid_dict['size']['x'], grid_dict['size']['y'], grid_dict['size']['z']
    return origin, size, grid_dict['params']


def _get_grid_from_text(cmip_log_path: Union[str, Path], external: bool = False) -> tuple[tuple[float, float, float], tuple[float, float, float], dict[str, tuple[float, float, float]]]:
    origin = None
    size = None
    grid_params: dict[str, Any] = {"CEN": None, "DIM": None, "INT": None}
    grid_locators_list = ["AUTOMATIC GRID", "MANUAL GRID"]
    if external:
        grid_locators_list = ["AUTOMATIC OUTER GRID", "MANUAL OUTER GRID"]

    with open(cmip_log_path) as log_file:
        inside_automatic_grid = False
        for line in log_file:
            if line.strip() in grid_locators_list:
                inside_automatic_grid = True
            if inside_automatic_grid:
                origin_match = re.match(r"Grid origin:\s+([-+]?(?:\d*\.\d+|\d+))\s+([-+]?(?:\d*\.\d+|\d+))\s+([-+]?(?:\d*\.\d+|\d+))", line.strip())
                if origin_match:
                    origin = float(origin_match.group(1)), float(origin_match.group(2)), float(origin_match.group(3))
                size_match = re.match(r"Grid Size:\s+([-+]?(?:\d*\.\d+|\d+))\s+([-+]?(?:\d*\.\d+|\d+))\s+([-+]?(?:\d*\.\d+|\d+))", line.strip())
                if size_match:
                    size = float(size_match.group(1)), float(size_match.group(2)), float(size_match.group(3))
                int_match = re.match(r"Grid units:\s+([-+]?(?:\d*\.\d+|\d+))\s+([-+]?(?:\d*\.\d+|\d+))\s+([-+]?(?:\d*\.\d+|\d+))", line.strip())
                if int_match:
                    grid_params['INT'] = float(int_match.group(1)), float(int_match.group(2)), float(int_match.group(3))
                cen_match = re.match(r"Grid center:\s+([-+]?(?:\d*\.\d+|\d+))\s+([-+]?(?:\d*\.\d+|\d+))\s+([-+]?(?:\d*\.\d+|\d+))", line.strip())
                if cen_match:
                    grid_params['CEN'] = float(cen_match.group(1)), float(cen_match.group(2)), float(cen_match.group(3))
                dim_match = re.match(r"Grid density:\s+([-+]?(?:\d*\.\d+|\d+))\s+([-+]?(?:\d*\.\d+|\d+))\s+([-+]?(?:\d*\.\d+|\d+))", line.strip())
                if dim_match:
                    grid_params['DIM'] = int(dim_match.group(1)), int(dim_match.group(2)), int(dim_match.group(3))
                if origin and size and grid_params['INT'] and grid_params['CEN'] and grid_params['DIM']:
                    break
    return origin, size, grid_params  # type: ignore


def _get_grid_from_key_value(cmip_log_path: Union[str, Path], external: bool = False) -> tuple[tuple[float, float, float], tuple[float, float, float], dict[str, tuple[float, float, float]]]:
    origin = None
    size = None
    grid_params: dict[str, Any] = {"CEN": None, "DIM": None, "INT": None}
    grid_locators_list = ["AUTOMATIC GRID", "MANUAL GRID"]
    if external:
        grid_locators_list = ["AUTOMATIC OUTER GRID", "MANUAL OUTER GRID"]

    with open(cmip_log_path) as log_file:
        inside_automatic_grid = False
        for line in log_file:
            if line.strip() in grid_locators_list:
                inside_automatic_grid = True
            if inside_automatic_grid:
                origin_match = re.match(r"origin=\s+([-+]?(?:\d*\.\d+|\d+))\s*,\s*([-+]?(?:\d*\.\d+|\d+))\s*,\s*([-+]?(?:\d*\.\d+|\d+))", line.strip())
                if origin_match:
                    origin = float(origin_match.group(1)), float(origin_match.group(2)), float(origin_match.group(3))
                size_match = re.match(r"size=\s+([-+]?(?:\d*\.\d+|\d+))\s*,\s*([-+]?(?:\d*\.\d+|\d+))\s*,\s*([-+]?(?:\d*\.\d+|\d+))", line.strip())
                if size_match:
                    size = float(size_match.group(1)), float(size_match.group(2)), float(size_match.group(3))
                int_match = re.match(r"spacing=\s+([-+]?(?:\d*\.\d+|\d+))\s*,\s*([-+]?(?:\d*\.\d+|\d+))\s*,\s*([-+]?(?:\d*\.\d+|\d+))", line.strip())
                if int_match:
                    grid_params['INT'] = float(int_match.group(1)), float(int_match.group(2)), float(int_match.group(3))
                cen_match = re.match(r"center=\s+([-+]?(?:\d*\.\d+|\d+))\s*,\s*([-+]?(?:\d*\.\d+|\d+))\s*,\s*([-+]?(?:\d*\.\d+|\d+))", line.strip())
                if cen_match:
                    grid_params['CEN'] = float(cen_match.group(1)), float(cen_match.group(2)), float(cen_match.group(3))
                dim_match = re.match(r"dim=\s+([-+]?(?:\d*\.\d+|\d+))\s*,\s*([-+]?(?:\d*\.\d+|\d+))\s*,\s*([-+]?(?:\d*\.\d+|\d+))", line.strip())
                if dim_match:
                    grid_params['DIM'] = int(dim_match.group(1)), int(dim_match.group(2)), int(dim_match.group(3))
                if origin and size and grid_params['INT'] and grid_params['CEN'] and grid_params['DIM']:
                    break
    return origin, size, grid_params  # type: ignore


def create_unique_file_path(parent_dir: Optional[Union[str, Path]] = None, extension: Optional[str] = None) -> str:
    if not parent_dir:
        parent_dir = Path.cwd()
    if not extension:
        extension = ''
    while True:
        name = str(uuid.uuid4())+extension
        file_path = Path.joinpath(Path(parent_dir).resolve(), name)
        if not file_path.exists():
            return str(file_path)


def write_cmip_pdb(input_pdb_path, output_pdb_path, charges_list, elements_list):
    with open(input_pdb_path) as inPDB, open(output_pdb_path, 'w') as outPDB:
        index = 0
        for line in inPDB:
            line = line.rstrip()
            if not re.match('^ATOM', line) and not re.match('^HETATM', line):
                continue
            outPDB.write("{}{:8.4f}  {}\n".format(line[:54], charges_list[index], elements_list[index]))
            index += 1


def get_topology_cmip_elements_canonical(input_topology_filename: str) -> list:
    """
    This function also accepts pdb files
    Args:
        input_topology_filename:

    Returns:

    """
    # Remove forcefield itp references from top file.
    if input_topology_filename.lower().endswith('.top'):
        with open(input_topology_filename) as tf:
            top_lines = tf.readlines()
        top_file = create_unique_file_path(parent_dir=Path(input_topology_filename).parent.resolve(), extension='.top')
        with open(top_file, 'w') as nt:
            for line in top_lines:
                if re.search(r"\.ff.*\.itp", line):
                    continue
                nt.write(line)
        u = mda.Universe(top_file, topology_format="ITP")
        os.unlink(top_file)
    else:
        u = mda.Universe(input_topology_filename)
    # mda_charges = [round(val, 4) for val in u.atoms.charges]
    # mda_atom_types = list(guess_types(u.atoms.names))
    mda_atom_types = []
    for atom in u.atoms:  # type: ignore
        atom_element = guess_atom_element(atom.name)
        if atom_element == 'H':
            bonded_atom_element = guess_atom_element(atom.bonded_atoms[0].name)
            if bonded_atom_element == 'O':
                atom_element = 'HO'
            elif bonded_atom_element in ['N', 'S']:
                atom_element = 'HN'
        mda_atom_types.append(atom_element)
    return mda_atom_types


def get_topology_charges(input_topology_filename: str) -> list:
    """ Given a topology which includes charges
    Extract those charges and save them in a list to be returned
    Supported formats (tested): prmtop, top, psf
    """
    # Remove forcefield itp references from top file.
    if input_topology_filename.lower().endswith('.top'):
        with open(input_topology_filename) as tf:
            top_lines = tf.readlines()
        top_file = create_unique_file_path(parent_dir=Path(input_topology_filename).parent.resolve(), extension='.top')

        with open(top_file, 'w') as nt:
            for line in top_lines:
                if re.search(r"\.ff.*\.itp", line):
                    continue
                nt.write(line)
        u = mda.Universe(top_file, topology_format="ITP")
        os.unlink(top_file)
    else:
        u = mda.Universe(input_topology_filename)
    return [round(val, 4) for val in u.atoms.charges]  # type: ignore


class Residue:
    def __init__(self, data):
        self.id = data[0]+':'+data[1]
        self.atType = data[2]
        self.charg = float(data[3])


class ResiduesDataLib:
    def __init__(self, fname):
        self.RData = {}
        with open(fname) as fh:
            for line in fh:
                if line[0] == '#':
                    continue
                data = line.split()
                r = Residue(data)
                self.RData[r.id] = r
            self.nres = len(self.RData)

    def getParams(self, resid, atid):
        if resid+':'+atid in self.RData:
            return self.RData[resid+':'+atid]
        else:
            print("WARNING: atom not found in library (", resid+':'+atid, ')')
            return {}


def get_pdb_charges(input_pdb_filename: str, residue_library_path: Optional[str] = None) -> list:
    if not residue_library_path:
        residue_library_path = str(Path(__file__).parent.joinpath("dat", "aa.lib").resolve())

    aaLib = ResiduesDataLib(residue_library_path)
    print("{} residue/atom pairs loaded from {}".format(aaLib.nres, residue_library_path))

    with open(input_pdb_filename) as inPDB:
        charges_list = []
        residue_num = None
        for line in inPDB:
            line = line.rstrip()
            if not re.match('^ATOM', line) and not re.match('^HETATM', line):
                continue

            nomat = line[12:16]
            if re.match('^[1-9]', nomat):
                nomat = nomat[1:4] + nomat[:1]
            nomat = nomat.replace(' ', '')
            nomr = line[17:21].replace(' ', '')
            # WARNING: Temporal totally uninformed assumption by PA
            if nomr == "HIS":
                nomr = "HID"
                if residue_num != line[23:27]:
                    print(f"WARNING replacing HIS:{line[23:27]} by HID")
                    residue_num = line[23:27]
            # Thats not correct REVIEW this should be done for all the atoms in the residue
            # not just the oxigen
            if nomat == "OXT":
                nomr = nomr + "C"
                print(f"WARNING replacing {nomr[:-1]}:{line[23:27]} by {nomr}")
            ######################################################
            parms = aaLib.getParams(nomr, nomat)
            charges_list.append(parms.charg)  # type: ignore
        return charges_list


def get_pdb_cmip_elements_canonical(input_pdb_filename: str, residue_library_path: Optional[str] = None) -> list:
    if not residue_library_path:
        residue_library_path = str(Path(__file__).parent.joinpath("dat", "aa.lib").resolve())

    aaLib = ResiduesDataLib(residue_library_path)
    print("{} residue/atom pairs loaded from {}".format(aaLib.nres, residue_library_path))

    with open(input_pdb_filename) as inPDB:
        elements_list = []
        residue_num = None
        for line in inPDB:
            line = line.rstrip()
            if not re.match('^ATOM', line) and not re.match('^HETATM', line):
                continue

            nomat = line[12:16]
            if re.match('^[1-9]', nomat):
                nomat = nomat[1:4] + nomat[:1]
            nomat = nomat.replace(' ', '')
            nomr = line[17:21].replace(' ', '')
            # WARNING: Temporal totally uninformed assumption by PA
            if nomr == "HIS":
                nomr = "HID"
                if residue_num != line[23:27]:
                    print(f"WARNING replacing HIS:{line[23:27]} by HID")
                    residue_num = line[23:27]
            # Thats not correct REVIEW this should be done for all the atoms in the residue
            # not just the oxigen
            if nomat == "OXT":
                nomr = nomr + "C"
                print(f"WARNING replacing {nomr[:-1]}:{line[23:27]} by {nomr}")
            ######################################################
            parms = aaLib.getParams(nomr, nomat)
            elements_list.append(parms.atType)  # type: ignore
        return elements_list


def get_pdb_total_charge(pdb_file_path: str) -> float:
    # Biopython 1.9 does not capture charge of atoms in CMIP format
    # Should do it by hand
    total_charge: float = 0.0
    with open(pdb_file_path) as pdb_file:
        for line in pdb_file:
            if line[0:6].strip().upper() in ["ATOM", "HETATM"] and len(line) > 63:
                total_charge += float(line[55:63].strip())
    return total_charge


def probe_params_grid(probe_id: int = 0, readgrid: int = 2, pbfocus: int = 1, perfill: float = 0.6,
                      grid_int: tuple[float, float, float] = (0.5, 0.5, 0.5)) -> dict[str, str]:
    grid_dict = {}
    grid_dict[f"readgrid{probe_id}"] = f"{readgrid}"
    grid_dict[f"perfill{probe_id}"] = f"{perfill}"
    grid_dict['pbfocus'] = f"{pbfocus}"
    grid_dict['grid_int'] = f"INTX{probe_id}={grid_int[0]},INTY{probe_id}={grid_int[1]},INTZ{probe_id}={grid_int[2]}"

    return grid_dict


def params_grid(grid_type: str, readgrid: int = 0, perfill: float = 0.8,
                grid_int: tuple[float, float, float] = (0.5, 0.5, 0.5),
                grid_dim: tuple[float, float, float] = (64, 64, 64),
                grid_cen: tuple[float, float, float] = (0.0, 0.0, 0.0)) -> dict[str, str]:
    # grid_type older readgrid equivalences:
    #     2 proteina dist minima pecentatge, 4 distancia minima prot, 5 distancia al centre de masses
    #     1
    #     interaction = 0 , 3 explicita grid d'entrada
    #     cmip, titration, pbsolvation = 2, >3

    grid_dict = {}
    grid_dict["readgrid"] = f"{readgrid}"

    if grid_type in ['pb_interaction_energy', 'mip_pos', 'mip_neu', 'mip_neg', 'docking']:
        grid_dict['grid_cen'] = f"CENX={grid_cen[0]},CENY={grid_cen[1]},CENZ={grid_cen[2]}"
        grid_dict['grid_dim'] = f"DIMX={grid_dim[0]},DIMY={grid_dim[1]},DIMZ={grid_dim[2]}"
        grid_dict['grid_int'] = f"INTX={grid_int[0]},INTY={grid_int[1]},INTZ={grid_int[2]}"
    elif grid_type in ['solvation', 'titration']:
        grid_dict['perfill'] = f"{perfill}"
        grid_dict['grid_int'] = f"INTX={grid_int[0]},INTY={grid_int[1]},INTZ={grid_int[2]}"

    return grid_dict


def params_preset(execution_type: str) -> dict[str, str]:
    params_dict = {}
    grid_dict = {}
    probe_grid_dict = {}
    execution_type = execution_type.strip()
    if execution_type == 'titration':
        grid_dict = params_grid(grid_type=execution_type, readgrid=2, perfill=0.8, grid_int=(0.5, 0.5, 0.5))
        params_dict = {
            'title': 'Titration',
            'tipcalc': 1,
            'calcgrid': 1,
            'irest': 0,
            'orest': 0,
            'coorfmt': 2,
            'dields': 2,
            'titration': 1, 'inifoc': 2, 'cutfoc': -0.5, 'focus': 1, 'ninter': 10, 'clhost': 1, 'titcut': 20.,
            'titwat': 10, 'titip': 10, 'titim': 10
        }
    elif execution_type == 'mip_pos':
        grid_dict = params_grid(grid_type=execution_type, readgrid=2)
        params_dict = {
            'title': 'MIP positive probe',
            'tipcalc': 0,
            'calcgrid': 1,
            'irest': 0,
            'orest': 0,
            'coorfmt': 2,
            'dields': 2,
            'cubeoutput': 1,
            'fvdw': 0.8,
            'carmip': 1,
            'tipatmip': "'OW'"
        }
    elif execution_type == 'mip_neu':
        grid_dict = params_grid(grid_type=execution_type, readgrid=2)
        params_dict = {
            'title': 'MIP neutral probe',
            'tipcalc': 0,
            'calcgrid': 1,
            'irest': 0,
            'orest': 0,
            'coorfmt': 2,
            'dields': 2,
            'cubeoutput': 1,
            'fvdw': 0.8,
            'carmip': 0,
            'tipatmip': "'OW'"
        }
    elif execution_type == 'mip_neg':
        grid_dict = params_grid(grid_type=execution_type, readgrid=2)
        params_dict = {
            'title': 'MIP negative probe',
            'tipcalc': 0,
            'calcgrid': 1,
            'irest': 0,
            'orest': 0,
            'coorfmt': 2,
            'dields': 2,
            'cubeoutput': 1,
            'fvdw': 0.8,
            'carmip': -1,
            'tipatmip': "'OW'"
        }
    # TODO 'carmip': 1,
    # wat: tipcalc: 1 + titration: 'inifoc': 2, 'cutfoc': -0.5, 'focus': 1, 'ninter': 10,
    elif execution_type == 'solvation':
        grid_dict = params_grid(grid_type=execution_type, readgrid=2, perfill=0.2,
                                grid_int=(0.5, 0.5, 0.5))
        params_dict = {
            'title': 'Solvation & MEP',
            'tipcalc': 0,
            'calcgrid': 1,
            'irest': 0,
            'orest': 0,
            'coorfmt': 2,
            'cubeoutput': 1, 'vdw': 0, 'pbelec': 1,
            'novdwgrid': 1, 'solvenergy': 1, 'dielc': 1, 'dielsol': 80
        }

    elif execution_type == 'pb_interaction_energy':
        grid_dict = params_grid(grid_type=execution_type, readgrid=2)
        probe_grid_dict = probe_params_grid(probe_id=0, readgrid=2, pbfocus=1, perfill=0.6,
                                            grid_int=(1.5, 1.5, 1.5))

        # TODO Check for external box file or parameters
        params_dict = {
            'title': 'Docking Interaction energy calculation. PB electrostatics',
            'tipcalc': 3,
            'calcgrid': 1,
            'irest': 0,
            'orest': 0,
            'coorfmt': 2,
            'fvdw': 0.8, 'pbelec': 1, 'pbinic': 2, 'wgp': 0, 'ebyatom': 1
        }

    elif execution_type == 'docking':
        grid_dict = params_grid(grid_type=execution_type, readgrid=2)

        params_dict = {
            'title': 'Docking Mehler Solmajer dielectric',
            'tipcalc': 2,
            'calcgrid': 1,
            'irest': 0,
            'orest': 1,
            'coorfmt': 2,
            'fvdw': 0.8, 'dields': 2, 'focus': 1, 'cutfoc': 100,
            'tiprot': 5, 'inifoc': 5, 'ninter': 20,
            'clhost': 1, 'minout': 50, 'splitpdb': 0
        }

    elif execution_type == 'docking_rst':
        params_dict = {
            'title': 'Docking from restart file',
            'readgrid': 0,
            'tipcalc': 2,
            'calcgrid': 1,
            'irest': 2,
            'orest': 1,
            'coorfmt': 2,
            'fvdw': 0.8, 'dields': 2, 'focus': 1, 'cutfoc': 100,
            'tiprot': 5, 'inifoc': 5, 'ninter': 20,
            'clhost': 1, 'minout': 50, 'splitpdb': 0, 'cutelec': 10.0
        }
    elif execution_type == 'check_only':
        params_dict = {
            'title': 'Check_only dry run of CMIP',
            'CHECKONLY': 1,
            'readgrid': 2,
            'calcgrid': 1,
            'tipcalc': 0,
            'irest': 0,
            'ebyatom': 1,
            'coorfmt': 2,
            'fvdw': 0.8
        }

    return {**params_dict, **grid_dict, **probe_grid_dict}  # type: ignore


def read_params_file(input_params_path: str) -> dict[str, str]:
    params_dict = {}
    with open(input_params_path) as input_params_file:
        params_dict['title'] = input_params_file.readline()
        for line in input_params_file:
            line = line.replace(' ', '')
            if line.startswith('&'):
                continue
            param_list = line.split(',')
            for param in param_list:
                param_key, param_value = param.split("=")

                # Grid Values
                if len(param_key) > 3 and param_key[:3].startswith('INT'):
                    if params_dict.get('grid_int'):
                        params_dict['grid_int'] += f",{param_key}={param_value}"
                    else:
                        params_dict['grid_int'] = f"{param_key}={param_value}"
                elif len(param_key) > 3 and param_key[:3].startswith('CEN'):
                    if params_dict.get('grid_cen'):
                        params_dict['grid_cen'] += f",{param_key}={param_value}"
                    else:
                        params_dict['grid_cen'] = f"{param_key}={param_value}"
                elif len(param_key) > 3 and param_key[:3].startswith('DIM'):
                    if params_dict.get('grid_dim'):
                        params_dict['grid_dim'] += f",{param_key}={param_value}"
                    else:
                        params_dict['grid_dim'] = f"{param_key}={param_value}"
                # Rest of parameters
                else:
                    params_dict[param_key] = param_value
    return params_dict


def write_params_file(output_params_path: str, params_dict: dict[str, str]) -> str:
    with open(output_params_path, 'w') as output_params_file:
        output_params_file.write(f"{params_dict.pop('title', 'Untitled')}\n")
        output_params_file.write("&cntrl\n")
        for params_key, params_value in params_dict.items():
            if params_key in ['grid_int', 'grid_cen', 'grid_dim', 'grid_int0', 'grid_cen0', 'grid_dim0']:
                output_params_file.write(f" {params_value}\n")
            else:
                output_params_file.write(f" {params_key} = {params_value}\n")
        output_params_file.write("&end\n")
    return output_params_path


def create_params_file(output_params_path: str, input_params_path: Optional[str] = None,
                       params_preset_dict: Optional[dict] = None, params_properties_dict: Optional[dict] = None) -> str:
    """ Gets a params dictionary and a presset and returns the path of the created params file for cmip.

    Args:


    Returns:
        str: params file path.
    """
    params_dict = {}

    if params_preset_dict:
        for k, v in params_preset_dict.items():
            params_dict[k] = v
    if input_params_path:
        input_params_dict = read_params_file(input_params_path)
        for k, v in input_params_dict.items():
            params_dict[k] = v
    if params_properties_dict:
        for k, v in params_properties_dict.items():
            params_dict[k] = v

    return write_params_file(output_params_path, params_dict)


def mark_residues(residue_list: list[str], input_cmip_pdb_path: str, output_cmip_pdb_path: str, out_log: Optional[logging.Logger] = None, global_log: Optional[logging.Logger] = None) -> None:
    """Marks using an "X" before the atom type all the residues in *residue_list* and writes the result in *output_cmip_pdb_path*.

        Args:
            residue_list (list): Residue list in the format "Chain:Resnum" (no spaces between the elements) separated by commas. If empty or none all residues will be marked.
            local_log (:obj:`logging.Logger`): local log object.
            global_log (:obj:`logging.Logger`): global log object.
        """
    if not residue_list:
        fu.log("Empty residue_list all residues will be marked", out_log, global_log)
    else:
        fu.log(f"Residue list: {residue_list}", out_log, global_log)

    with open(input_cmip_pdb_path) as pdb_file_in, open(output_cmip_pdb_path, 'w') as pdb_file_out:
        residue_set_used = set()

        res_counter = 0
        for line in pdb_file_in:
            if _is_atom(line):
                residue_code = _get_residue_code(line)
                used_residue = _get_residue_code_in_list(residue_code, residue_list)
                if not residue_list or used_residue:
                    res_counter += 1
                    residue_set_used.add(used_residue)
                    line = _mark_pdb_atom(line)
            pdb_file_out.write(line)
        fu.log(f"{res_counter} residues have been marked", out_log, global_log)

        if residue_list:
            unused_residues = set(residue_list) - residue_set_used
            if unused_residues:
                fu.log(f"The following residues where present in the residue_list and have not been marked: {unused_residues}", out_log, global_log)


def _mark_pdb_atom(line: str) -> str:
    newline = list(line)
    newline.insert(64, 'X')
    return ''.join(newline)


def _get_residue_code_in_list(input_residue, residue_list):
    if not residue_list:
        return None
    for res_code in residue_list:
        if input_residue == res_code:
            return res_code
        chain_rescode, resnum_rescode = res_code.split(":")
        chain_input, resnum_input = input_residue.split(":")
        if not chain_rescode:
            if resnum_rescode == resnum_input:
                return res_code
        if not resnum_rescode:
            if chain_rescode == chain_input:
                return res_code
    return None


def _get_residue_code(line: str) -> str:
    return _get_chain(line)+":"+_get_resnum(line)


def _get_chain(line: str) -> str:
    return line[21].upper()


def _get_resnum(line: str) -> str:
    return line[22:27].strip()


def _is_atom(line: str) -> bool:
    return line[0:6].strip().upper() in ["ATOM", "HETATM"]
