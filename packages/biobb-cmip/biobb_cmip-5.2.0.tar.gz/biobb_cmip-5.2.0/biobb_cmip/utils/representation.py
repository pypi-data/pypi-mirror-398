""" Representation functions for package biobb_cmip.cmip """
from biobb_cmip.cmip.common import get_grid
from pathlib import Path
from MDAnalysis.lib.util import inverse_aa_codes  # type: ignore
from typing import Union


def get_energies_byat(cmip_energies_byat_out: Union[str, Path], cutoff: float = 100.0) -> tuple[list[str], dict[str, list[float]]]:

    with open(cmip_energies_byat_out, 'r') as energies_file:
        atom_list = []
        energy_dict: dict[str, list] = {"ES": [], "VDW": [], "ES&VDW": []}
        for line in energies_file:
            atom_list.append(line[6:12].strip())
            vdw = float(line[42:53]) if float(line[42:53]) < cutoff else 0.0
            es = float(line[57:68]) if float(line[57:68]) < cutoff else 0.0
            both = float(line[72:83]) if float(line[72:83]) < cutoff else 0.0

            energy_dict["ES"].append(es)
            energy_dict["VDW"].append(vdw)
            energy_dict["ES&VDW"].append(both)

    return atom_list, energy_dict


def get_energies_byres(cmip_energies_byat_out: Union[str, Path], cutoff: float = 100.0) -> tuple[list[str], dict[str, list[float]]]:
    residues: list = []
    energy_dict: dict[str, list] = {"ES": [], "VDW": [], "ES&VDW": []}
    with open(cmip_energies_byat_out, 'r') as energies_file:
        for line in energies_file:
            chain = line[21:22].strip()
            residue_id = line[22:28].strip()
#            residue_id = str(int(residue_id) + 697)
#            if (int(residue_id) > 746):
#                residue_id = str(int(residue_id) + 9)
#            if (int(residue_id) > 749):
#                residue_id = str(int(residue_id) + 4)
#            if (int(residue_id) > 867):
#                residue_id = str(int(residue_id) + 8)
#            if (int(residue_id) > 987):
#                residue_id = str(int(residue_id) + 7)
#            if (int(residue_id) > 1004):
#                residue_id = str(int(residue_id) + 5)
            resname = inverse_aa_codes.get(line[17:21].strip().upper(), "X")
            residue = resname+' '+chain+residue_id
            vdw = float(line[42:53]) if float(line[42:53]) < cutoff else 0.0
            es = float(line[57:68]) if float(line[57:68]) < cutoff else 0.0
            both = float(line[72:83]) if float(line[72:83]) < cutoff else 0.0

            if residue in residues:
                index = residues.index(residue)
                energy_dict["ES"][index] += es
                energy_dict["VDW"][index] += vdw
                energy_dict["ES&VDW"][index] += both
            else:
                residues.append(residue)
                # residues.append(int(residue_id)+696)
                energy_dict["ES"].append(es)
                energy_dict["VDW"].append(vdw)
                energy_dict["ES&VDW"].append(both)

        return residues, energy_dict


def create_box_representation(cmip_log_path: Union[str, Path], cmip_pdb_path: Union[str, Path]) -> tuple[str, list[list[str]]]:
    return _create_box_representation_file(cmip_log_path, cmip_pdb_path), _get_atom_pair()


def _create_box_representation_file(cmip_log_path: Union[str, Path], cmip_pdb_path: Union[str, Path]) -> str:
    vertex_list = _get_vertex_list(cmip_log_path)

    cmip_pdb_path = Path(cmip_pdb_path).resolve()
    boxed_pdb_path = cmip_pdb_path.parent.joinpath("boxed_"+str(cmip_pdb_path.name))
    with open(cmip_pdb_path) as cmip_pdb_file:
        pdb_lines = cmip_pdb_file.readlines()
        if pdb_lines[-1].strip().upper() == "END":
            pdb_lines = pdb_lines[:-1]
    with open(boxed_pdb_path, 'w') as boxed_pdb_file:
        for pdb_line in pdb_lines:
            boxed_pdb_file.write(pdb_line)
        for i, v in enumerate(vertex_list):
            boxed_pdb_file.write('HETATM10000 ZN' + str(i) + '   ZN Z9999    ' + v + '  1.00 50.00          ZN\n')
        boxed_pdb_file.write("END")
    return str(boxed_pdb_path)


def _get_vertex_list(cmip_log_path: Union[str, Path]) -> list[str]:
    origin, size, _ = get_grid(cmip_log_path)
    return [
        _pdb_coord_formatter(origin[0]) + _pdb_coord_formatter(origin[1]) + _pdb_coord_formatter(origin[2]),
        _pdb_coord_formatter(origin[0] + size[0]) + _pdb_coord_formatter(origin[1]) + _pdb_coord_formatter(origin[2]),
        _pdb_coord_formatter(origin[0]) + _pdb_coord_formatter(origin[1] + size[1]) + _pdb_coord_formatter(origin[2]),
        _pdb_coord_formatter(origin[0]) + _pdb_coord_formatter(origin[1]) + _pdb_coord_formatter(origin[2] + size[2]),
        _pdb_coord_formatter(origin[0] + size[0]) + _pdb_coord_formatter(origin[1] + size[1]) + _pdb_coord_formatter(origin[2]),
        _pdb_coord_formatter(origin[0] + size[0]) + _pdb_coord_formatter(origin[1]) + _pdb_coord_formatter(origin[2] + size[2]),
        _pdb_coord_formatter(origin[0]) + _pdb_coord_formatter(origin[1] + size[1]) + _pdb_coord_formatter(origin[2] + size[2]),
        _pdb_coord_formatter(origin[0] + size[0]) + _pdb_coord_formatter(origin[1] + size[1]) + _pdb_coord_formatter(origin[2] + size[2]),
    ]


def _pdb_coord_formatter(coordinate: float) -> str:
    return str(round(coordinate, 3)).rjust(8)


def _get_atom_pair() -> list[list[str]]:
    return [["9999:Z.ZN0", "9999:Z.ZN1"],
            ["9999:Z.ZN0", "9999:Z.ZN2"],
            ["9999:Z.ZN0", "9999:Z.ZN3"],
            ["9999:Z.ZN1", "9999:Z.ZN4"],
            ["9999:Z.ZN1", "9999:Z.ZN5"],

            ["9999:Z.ZN2", "9999:Z.ZN4"],
            ["9999:Z.ZN2", "9999:Z.ZN6"],

            ["9999:Z.ZN3", "9999:Z.ZN5"],
            ["9999:Z.ZN3", "9999:Z.ZN6"],

            ["9999:Z.ZN4", "9999:Z.ZN7"],
            ["9999:Z.ZN5", "9999:Z.ZN7"],
            ["9999:Z.ZN6", "9999:Z.ZN7"]]

# AUTOMATIC OUTER GRID / titleGrid0=Automatic Outer Grid
#
# INT:
#     spacing=   1.50000000     ,   1.50000000     ,   1.50000000
#     Grid units:      1.500   1.500   1.500
# CEN:
#     center=   71.6100006     ,   67.7550049     ,   56.3150024
#     Grid center:    71.610  67.755  56.315
# DIM:
#     dim=          64 ,          92 ,          72
#     Grid density:    64   92   72
#
# To create graphic representations:
# Size:
#     Grid Size:      96.000 138.000 108.000  90.000  90.000  90.000
#     size=   96.0000000     ,   138.000000     ,   108.000000
#
# Origin:
#     Grid origin:    23.610  -1.245   2.315
#     origin=   23.6100006     ,  -1.24499512     ,   2.31500244
