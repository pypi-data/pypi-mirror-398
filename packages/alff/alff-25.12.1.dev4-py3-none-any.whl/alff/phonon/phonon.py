"""Workflow for phonon calculation."""

from __future__ import annotations

from thkit.pkg import check_package

check_package("phonopy", auto_install=True, conda_channel="conda-forge")
check_package("seekpath", auto_install=True, conda_channel="conda-forge")
check_package("spglib", auto_install=True, conda_channel="conda-forge")

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ase import Atoms
    from phonopy.structure.atoms import PhonopyAtoms

from pathlib import Path

import numpy as np
from ase.io import read
from phonopy import Phonopy

from alff.base import KEY as K
from alff.base import Workflow, logger
from alff.gdata.gendata import (
    copy_labeled_structure,
    make_structure,
    strain_x_dim,
    strain_y_dim,
    strain_z_dim,
)
from alff.phonon.libpho_gpaw import (
    OperPhononGpawOptimize,
    OperPhononGpawOptimizeFixbox,
    OperPhononGpawSinglepoint,
)
from alff.phonon.libpho_lammps import (
    OperPhononLammpsOptimize,
    OperPhononLammpsOptimizeFixbox,
    OperPhononLammpsSinglepoint,
)
from alff.phonon.utilpho import (
    convert_ase2phonopy,
    convert_phonopy2ase,
    get_band_structure,
    get_DOS_n_PDOS,
    get_primitive_phonopy,
    get_thermal_properties,
)
from alff.util.tool import check_supported_calculator, mk_struct_dir
from asext.io.readwrite import write_extxyz
from thkit.io import read_yaml, write_yaml
from thkit.path import ask_yesno, make_dir, move_file
from thkit.range import composite_strain_points


#####ANCHOR Stage 1 - build structure
### Use the same function as in alff.gendata.make_structure.py
def make_structure_phonon(pdict, mdict):
    """Make initial structure for phonon calculation. Recommended settings:
    1. Use *supercell size* to build the input structure.
    2. `supercell_matrix` = [n1, n2, n3] # no matter what the input structure is.
    3. Then, use `auto_primitive_cell` to find the primitive cell from the input structure. This works, but sometime gives unstable result. Use with caution.
    """
    pdict["structure"].pop("make_triangular_form", None)  ## Do not accept make_triangular_form
    make_structure(pdict, mdict)
    return


#####ANCHOR Stage 2 - relax initial structure by DFT/MD
def relax_initial_structure(pdict, mdict):
    """Relax the structure by DFT/MD."""
    ### Define work_dir
    struct_startdir = mk_struct_dir(pdict)
    work_dir = f"{struct_startdir}/{K.DIR_MAKE_STRUCT}"
    task_dirs = read_yaml(f"{work_dir}/structure_dirs.yml")
    write_yaml(task_dirs, f"{work_dir}/task_dirs.yml")

    ### Relax structures
    calc_name = pdict["calculator"].get("name")
    check_supported_calculator(calc_name)
    if calc_name == "gpaw":
        op = OperPhononGpawOptimize(work_dir, pdict, mdict, mdict_prefix="gpaw")
        op.prepare()
        op.run()
    elif calc_name == "lammps":
        op = OperPhononLammpsOptimize(work_dir, pdict, mdict, mdict_prefix="lammps")
        op.prepare()
        op.run()
        op.postprocess()
    return


#####ANCHOR Stage 3 - scale and relax
### Improve from the function alff.gendata.strain_perturb_structure.py
def strain_and_relax(pdict, mdict):
    """Scale and relax the structures while fixing box size. Use when want to compute phonon at different volumes."""
    ### Define work_dir
    struct_startdir = mk_struct_dir(pdict)
    work_dir = f"{struct_startdir}/{K.DIR_SUPERCELL}"
    make_dir(work_dir, backup=False)

    ### Copy/symlink files from structure_dirs (unlabeled or labeled)
    structure_dirs = read_yaml(f"{struct_startdir}/{K.DIR_MAKE_STRUCT}/task_dirs.yml")
    structure_files = [
        copy_labeled_structure(p, p.replace(K.DIR_MAKE_STRUCT, K.DIR_SUPERCELL))
        for p in structure_dirs
    ]

    ### Scale the structures
    strain_arg = pdict.get("strain", {})
    if strain_arg:
        logger.info(f"Scaling on the path: {work_dir}")

    strain_x_list = composite_strain_points(strain_arg.get("strain_x", []))
    strain_y_list = composite_strain_points(strain_arg.get("strain_y", []))
    strain_z_list = composite_strain_points(strain_arg.get("strain_z", []))

    structure_files = strain_x_dim(structure_files, strain_x_list)
    structure_files = strain_y_dim(structure_files, strain_y_list)
    structure_files = strain_z_dim(structure_files, strain_z_list)

    ### Save structure_dirs (relative to run_dir)
    strain_structure_dirs = sorted([Path(p).parent.as_posix() for p in structure_files])
    task_dirs = strain_structure_dirs
    write_yaml(task_dirs, f"{work_dir}/task_dirs.yml")

    ### Relax structures
    logger.info("Relax the scaled structures")
    calc_name = pdict["calculator"].get("name")
    check_supported_calculator(calc_name)
    if calc_name == "gpaw":
        op = OperPhononGpawOptimizeFixbox(work_dir, pdict, mdict, mdict_prefix="gpaw")
        op.prepare()
        op.run()
    elif calc_name == "lammps":
        op = OperPhononLammpsOptimizeFixbox(work_dir, pdict, mdict, mdict_prefix="lammps")
        op.prepare()
        op.run()
        op.postprocess()
    elif calc_name == "ase":
        raise NotImplementedError("ASE calculator is not implemented yet.")
    return


#####ANCHOR Stage 4 - compute force by DFT/MD
def compute_force(pdict, mdict):
    """Compute forces for each scale-relaxed-structure by DFT/MD."""
    ### work_dir
    struct_startdir = mk_struct_dir(pdict)
    work_dir = f"{struct_startdir}/{K.DIR_SUPERCELL}"
    task_dirs = read_yaml(f"{work_dir}/task_dirs.yml")

    ### compute forces for each relaxed-structure
    for tdir in task_dirs:
        compute_force_one_scaledstruct(tdir, pdict, mdict)
    return


def compute_force_one_scaledstruct(work_dir: str, pdict, mdict):
    """Run DFT/MD single-point calculations to compute forces for each *relaxed structure*.

    (the previous step generate a list of scaled&relaxed structures. This function works on each of them).
    The function does the following:
    - Initialize the `phonopy` object
    - generate supercell_list with displacements
    - run DFT/MD single-point calculation to compute forces for each supercell
    - assign forces back to phonopy object
    - save the phonopy object to a file for latter post-processing
    """
    pho_arg = pdict.get("phonon", {})
    phonopy_arg = pho_arg.get("phonopy_arg", {})

    ### refine inputs
    supercell_matrix = phonopy_arg.get("supercell_matrix", [1, 1, 1])
    if supercell_matrix is not None:
        m = np.array(supercell_matrix)
        assert m.shape == (3, 3) or m.shape == (3,), "supercell_matrix must be a list 3x3 or 1x3."
        if m.shape == (3,):
            phonopy_arg["supercell_matrix"] = np.eye(3) * m  # [2,2,2] to [[2,0,0],[0,2,0],[0,0,2]]

    ### Read the relaxed structure (and try to find primitive cell if needed)
    struct: Atoms = read(f"{work_dir}/{K.FILE_FRAME_LABEL}", index=-1)  # type: ignore[arg-type]
    auto_primitive_arg = pho_arg.get("auto_primitive_cell", {})
    if auto_primitive_arg:
        prim_struct = get_primitive_phonopy(struct, **auto_primitive_arg)
        build_cell = pdict["structure"].get("from_scratch", {}).get("supercell", [1, 1, 1])
        if not (len(prim_struct) < len(struct)) and any(np.array(build_cell) > 1):
            logger.warning(
                "Primitive cell detection may be inaccurate. Try again with lower value of `auto_primitive_cell.symprec`."
            )
            ans = ask_yesno("Are you sure want to continue?")
            if ans == "no":
                logger.info("User selects stop and exit")
                return
    else:
        prim_struct = struct

    ### Create Phonopy object
    struct_ph = convert_ase2phonopy(prim_struct)
    phonon = Phonopy(struct_ph, **phonopy_arg)
    logger.info(
        f"Created Phonopy object. \n\tInput struct: {len(phonon.unitcell)} atoms. \
        \n\tPrimitive: {len(phonon.primitive)} atoms. \n\tSupercell: {len(phonon.supercell)} atoms.",
    )

    ### Generate supercells with displacements
    displace_arg = pho_arg.get("displacement", {})
    phonon.generate_displacements(**displace_arg)
    supercell_list: list[PhonopyAtoms] = phonon.supercells_with_displacements  # type: ignore[attr-defined]

    ### Save supercells to configuration files
    displace_dirs = []  # relative to run_dir
    for idx, struct_ph in enumerate(supercell_list):
        struct = convert_phonopy2ase(struct_ph)
        write_extxyz(f"{work_dir}/displace_{idx:03d}/{K.FILE_FRAME_UNLABEL}", struct)
        displace_dirs.append(f"{work_dir}/displace_{idx:03d}")

    task_dirs = displace_dirs
    write_yaml(task_dirs, f"{work_dir}/task_dirs.yml")

    ### Run DFT/MD single-point calculation to compute forces
    calc_name = pdict["calculator"].get("name")
    if calc_name == "gpaw":
        op = OperPhononGpawSinglepoint(work_dir, pdict, mdict, mdict_prefix="gpaw")
        op.prepare()
        op.run()
        set_of_forces = op.postprocess()
    elif calc_name == "lammps":
        op = OperPhononLammpsSinglepoint(work_dir, pdict, mdict, mdict_prefix="lammps")
        op.prepare()
        op.run()
        set_of_forces = op.postprocess()

    ### Compute force constants
    phonon.produce_force_constants(forces=set_of_forces)  # type: ignore[unbounded]

    ### Save the phonopy object
    phonon.save(
        filename=f"{work_dir}/{K.FILE_PHONOPYwFORCES}",
        settings={"force_constants": True},
    )
    return


#####ANCHOR Stage 5 - phonon calculation
def compute_phonon(pdict, mdict):
    """Compute phonon properties by `phonopy` functions."""
    ### work_dir
    struct_startdir = mk_struct_dir(pdict)
    work_dir = f"{struct_startdir}/{K.DIR_PHONON}"
    make_dir(work_dir, backup=False)

    ### Copy phonopy_param.yml from the previous stage
    task_dirs = read_yaml(f"{struct_startdir}/{K.DIR_SUPERCELL}/task_dirs.yml")
    phonopy_files = [
        move_file(
            f"{p}/{K.FILE_PHONOPYwFORCES}",
            f"{p}/{K.FILE_PHONOPYwFORCES}".replace(K.DIR_SUPERCELL, K.DIR_PHONON),
        )
        for p in task_dirs
    ]

    compute_arg = pdict["phonon"].get("compute", {})
    ### Compute phonon in each subdir
    for f in phonopy_files:
        tdir = Path(f).parent
        if compute_arg.get("band_structure", None):
            get_band_structure(tdir, pdict)
        if compute_arg.get("dos", False) or compute_arg.get("pdos", False):
            get_DOS_n_PDOS(tdir, pdict)
        if compute_arg.get("thermal_properties", None):
            get_thermal_properties(tdir, pdict)

    logger.info(f"Phonon calculation results are saved in path: {work_dir}.")
    return


#####ANCHOR main loop
class WorkflowPhonon(Workflow):
    """Workflow for phonon calculation."""

    def __init__(self, params_file: str, machines_file: str):
        super().__init__(params_file, machines_file, K.SCHEMA_PHONON)
        self.stage_map = {
            "make_structure": make_structure_phonon,
            "relax_initial_structure": relax_initial_structure,
            "strain_and_relax": strain_and_relax,
            "compute_force": compute_force,
            "compute_phonon": compute_phonon,
        }
        self.wf_name = "PHONON CALCULATION"
        return
