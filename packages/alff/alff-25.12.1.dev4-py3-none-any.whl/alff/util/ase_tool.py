"""Utility functions for ASE-related tasks."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ase.atoms import Atoms

from copy import deepcopy

import numpy as np
from ase.build import bulk, graphene, molecule, mx2
from ase.io import read

from alff.base import KEY as K
from asext.struct import set_vacuum
from thkit.config import Config


#####ANCHOR ASE build structure
def build_struct(argdict: dict) -> Atoms:
    """Build atomic configuration, using library [`ase.build`](https://wiki.fysik.dtu.dk/ase/ase/build/build.html#).

    Supported structure types:
    - `bulk`: sc, fcc, bcc, tetragonal, bct, hcp, rhombohedral, orthorhombic, mcl, diamond, zincblende, rocksalt, cesiumchloride, fluorite or wurtzite.
    - `molecule`: molecule
    - `mx2`: MX2
    - `graphene`: graphene

    Args:
        argdict (dict): Parameters dictionary

    Returns:
        struct (Atoms): ASE Atoms object

    Notes:
        - `build.graphene()` does not set the cell c vector along z axis, so we need to modify it manually.
    """
    ### validate input
    Config.validate(config_dict=argdict, schema_file=K.SCHEMA_ASE_BUILD)

    ### Build structure with `ase.build`
    structure_type = argdict["structure_type"]
    ase_build_arg = deepcopy(argdict["ase_build_arg"])
    if structure_type == "bulk":
        ase_build_arg["name"] = argdict["chem_formula"]
        struct = bulk(**ase_build_arg)
    elif structure_type == "molecule":
        struct = molecule(**ase_build_arg)
    elif structure_type == "mx2":
        ase_build_arg["formula"] = argdict["chem_formula"]
        ase_build_arg["size"] = argdict.get("size", [1, 1, 1])
        ase_build_arg["vacuum"] = ase_build_arg.get("vacuum", 0.0)
        struct = mx2(**ase_build_arg)
    elif structure_type == "graphene":
        ase_build_arg["formula"] = argdict.get("chem_formula", "C2")
        ase_build_arg["a"] = ase_build_arg.get("a", 2.46)
        ase_build_arg["size"] = ase_build_arg.get("size", [1, 1, 1])
        ase_build_arg["thickness"] = 0.0
        struct = graphene(**ase_build_arg)
        ### Make the cell c vector along z axis
        real_thickness = argdict["ase_build_arg"].get("thickness", 3.35)
        c = struct.cell
        c[2, 2] = real_thickness
        struct.set_cell(c)
        struct.center()

    elif structure_type == "compound":
        print("not implemented yet")  # see `place_elements()` in dpgen
        ### May generate compound structure separately, and save as extxyz, then use option `from_extxyz` in `pdict`

    ### Make some modification on the built structure
    ## repeat cell
    supercell = argdict.get("supercell", [1, 1, 1])
    struct = struct.repeat(supercell)  # type: ignore[unbound]

    ## pbc
    pbc = argdict.get("pbc", [True, True, True])
    struct.set_pbc(pbc)

    ### Add vacuum padding (total vacuum distance both sides)
    vacuum_dists = argdict.get("set_vacuum", None)
    if vacuum_dists is not None:
        struct = set_vacuum(struct, vacuum_dists)

    # TODO: check ase_build_arg based on each function
    # labels: enhancement
    # use function config.argdict_to_schemadict to get the schema dict for each function
    return struct


#####ANCHOR helper functions for sorting tasks
def sort_task_dirs(task_dirs: list[str], work_dir: str) -> list[str]:
    """Sort the structure paths by its supercell size.
    This helps to chunk the tasks with similar supercell size together (similar supercell size means similar k-point number), which then lead to running DFT calculations in similar time, avoiding the situation that some tasks are finished while others are still running.
    """
    structure_dirs = [f"{work_dir}/{p}/{K.FILE_FRAME_UNLABEL}" for p in task_dirs]
    struct_list = [(read(f, format="extxyz", index=-1)) for f in structure_dirs]

    atom_counts = [len(atoms) for atoms in struct_list]
    periodic_len = [
        sum(length for length, pbc in zip(atoms.cell.lengths(), atoms.pbc) if pbc)  # type: ignore
        for atoms in struct_list
    ]

    ### Convert to NumPy arrays for sorting
    atom_counts_array = np.array(atom_counts)
    periodic_len_array = np.array(periodic_len)

    ### Sort indices first by 'number of atoms', then by 'periodic length'
    sorted_indices = np.lexsort((periodic_len_array, atom_counts_array))
    sorted_task_dirs = [task_dirs[i] for i in sorted_indices]
    return sorted_task_dirs
