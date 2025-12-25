### REF:
# - [1] https://phonopy.github.io/phonopy/
# - [2] https://github.com/abelcarreras/phonolammps
# - [3] https://github.com/lrgresearch/gpaw-tools
# - [4] https://gitlab.com/materials-modeling/calorine/-/blob/master/calorine/tools/phonons.py?ref_type=heads

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from alff.gdata.libgen_gpaw import (
        postgen_gpaw_optimize,
        postgen_gpaw_singlepoint,
        pregen_gpaw_optimize,
        pregen_gpaw_singlepoint,
        rungen_gpaw_optimize,
        rungen_gpaw_singlepoint,
    )
    from alff.phonon.libpho_gpaw import prepho_gpaw_optimize_fixbox
    from alff.phonon.libpho_lammps import (
        prepho_lammps_optimize,
        prepho_lammps_optimize_fixbox,
        prepho_lammps_singlepoint,
        runpho_lammps_optimize,
    )
from pathlib import Path

# from ase import units
from ase.io import read

from alff.base import KEY as K
from alff.base import Workflow, logger
from alff.elastic.lib_elastic import Elasticity
from alff.elastic.libelastic_lammps import (
    postelast_lammps_optimize,
    postelast_lammps_singlepoint,
)
from alff.gdata.gendata import (
    copy_labeled_structure,
    make_structure,
    strain_x_dim,
    strain_y_dim,
    strain_z_dim,
)
from alff.util.tool import mk_struct_dir
from asext.io.readwrite import write_extxyz
from thkit.io import read_yaml, write_yaml
from thkit.path import make_dir, move_file

#####ANCHOR Stage 1 - build structure
### Use the same function as in alff.gendata.make_structure.py


#####ANCHOR Stage 2 - relax initial structure by DFT/MD
### reuse the functions in alff.phono, except for the post_* functions must collect stress tensor
def relax_initial_structure(pdict, mdict):
    """
    Relax the structure by DFT/MD
    """
    ### Define work_dir
    struct_startdir = mk_struct_dir(pdict)
    work_dir = f"{struct_startdir}/{K.DIR_MAKE_STRUCT}"

    calc_name = pdict["calculator"].get("name")
    if calc_name == "gpaw":
        pregen_gpaw_optimize(work_dir, pdict)
        rungen_gpaw_optimize(work_dir, pdict, mdict)
        postgen_gpaw_optimize(work_dir, pdict)
    elif calc_name == "lammps":
        prepho_lammps_optimize(work_dir, pdict)
        runpho_lammps_optimize(work_dir, pdict, mdict)
        postelast_lammps_optimize(work_dir, pdict)
    else:
        raise ValueError(f"Unknown calculator: {calc_name}. Choices: gpaw, lammps")
    return


#####ANCHOR Stage 3 - scale and relax
### Improve from the function alff.phonon.phonon.strain_and_relax
def strain_and_relax(pdict, mdict):
    """
    Scale and relax the structures while fixing box size. Use when want to compute phonon at different volumes.
    """
    ### Define work_dir
    struct_startdir = mk_struct_dir(pdict)
    work_dir = f"{struct_startdir}/{K.DIR_SUPERCELL}"
    make_dir(work_dir, backup=False)

    ### Copy/symlink files from structure_paths (unlabeled or labeled)
    structure_paths = read_yaml(f"{struct_startdir}/{K.DIR_MAKE_STRUCT}/structure_dirs.yml")
    structure_files = [
        copy_labeled_structure(p, p.replace(K.DIR_MAKE_STRUCT, K.DIR_SUPERCELL))
        for p in structure_paths
    ]

    ### Scale the structures
    strain_arg = pdict.get("strain", {})
    if strain_arg:
        logger.info(f"Scaling on the path: {work_dir}")

    strain_x_list = strain_arg.get("strain_x", [])
    strain_y_list = strain_arg.get("strain_y", [])
    strain_z_list = strain_arg.get("strain_z", [])

    structure_files = strain_x_dim(structure_files, strain_x_list)
    structure_files = strain_y_dim(structure_files, strain_y_list)
    structure_files = strain_z_dim(structure_files, strain_z_list)

    ### Save structure_paths (relative to run_dir)
    strain_structure_paths = sorted([Path(p).parent.as_posix() for p in structure_files])
    write_yaml(strain_structure_paths, f"{work_dir}/structure_dirs.yml")

    ### Relax structures
    logger.info("Relax the scaled structures")
    calc_name = pdict["calculator"].get("name")
    if calc_name == "gpaw":
        prepho_gpaw_optimize_fixbox(work_dir, pdict)
        rungen_gpaw_optimize(work_dir, pdict, mdict)
        postgen_gpaw_optimize(work_dir, pdict)
    elif calc_name == "lammps":
        prepho_lammps_optimize_fixbox(work_dir, pdict)
        runpho_lammps_optimize(work_dir, pdict, mdict)
        postelast_lammps_optimize(work_dir, pdict)
    return


#####ANCHOR Stage 4 - compute force by DFT/MD
def compute_stress_strain(pdict, mdict):
    """Compute stress and strain tensors for each scale-relaxed-structure by DFT/MD."""
    ### work_dir
    struct_startdir = mk_struct_dir(pdict)
    work_dir = f"{struct_startdir}/{K.DIR_SUPERCELL}"
    structure_paths = read_yaml(f"{work_dir}/structure_dirs.yml")

    ### compute stress for each relaxed-structure
    for path in structure_paths:
        compute_stress_single_structure(path, pdict, mdict)
        compute_elastic_tensor_single_structure(path, pdict, mdict)
    return


def compute_stress_single_structure(work_dir, pdict, mdict):
    """The function does the following:
    - generate supercells with small deformation and compute corresponding strain tensor
    - run DFT/MD minimize calculation to compute stress tensor for each suppercell.
    - collect stress and strain tensor for each supercell
    """
    elastic_arg = pdict["elastic"]
    symprec = float(elastic_arg.get("symprec", 1e-5))  # covert str to float
    deformation = elastic_arg.get("deformation", 0.01)
    n_deform = elastic_arg.get("n_deform", 5)

    ### Read the reference structure
    ref_crystal = read(f"{work_dir}/{K.FILE_FRAME_LABEL}")
    Elastic = Elasticity(ref_crystal, symprec)

    ### Create supercells with small deformations
    deform_crystals = Elastic.generate_deformations(delta=deformation, n=n_deform)

    ### Save deform_crystals to configuration files
    deform_paths = []  # relative to run_dir
    for idx, atoms in enumerate(deform_crystals):
        write_extxyz(f"{work_dir}/deform_{idx:03d}/{K.FILE_FRAME_UNLABEL}", atoms)
        deform_paths.append(f"{work_dir}/deform_{idx:03d}")
    write_yaml(deform_paths, f"{work_dir}/structure_dirs.yml")

    ### Run DFT/MD single-point calculation to compute forces
    calc_name = pdict["calculator"].get("name")
    if calc_name == "gpaw":
        pregen_gpaw_singlepoint(work_dir, pdict)
        rungen_gpaw_singlepoint(work_dir, pdict, mdict)
        postgen_gpaw_singlepoint(work_dir, pdict)
    elif calc_name == "lammps":
        prepho_lammps_singlepoint(work_dir, pdict)
        runpho_lammps_optimize(work_dir, pdict, mdict)
        postelast_lammps_singlepoint(work_dir, pdict)
    ## use potimize (more cost, and not necessary)
    # if calc_name == "gpaw":
    #     prepho_gpaw_optimize_fixbox(work_dir, pdict)
    #     rungen_gpaw_optimize(work_dir, pdict, mdict)
    #     postgen_gpaw_optimize(work_dir, pdict)
    # elif calc_name == "lammps":
    #     prepho_lammps_optimize_fixbox(work_dir, pdict)
    #     runpho_lammps_optimize(work_dir, pdict, mdict)
    #     postelast_lammps_optimize(work_dir, pdict)
    return


def compute_elastic_tensor_single_structure(work_dir, pdict: dict, mdict: dict):
    """Compute elastic tensor for a single structure.
    - Collect stress and strain tensors from calculations on deformed structures.
    - Compute elastic constants by fitting stress-strain relations.
    """
    elastic_arg = pdict["elastic"]
    symprec = float(elastic_arg.get("symprec", 1e-5))  # covert str to float

    ### Read the reference structure
    ref_crystal = read(f"{work_dir}/{K.FILE_FRAME_LABEL}")
    Elastic = Elasticity(ref_crystal, symprec)

    ### Read the deformed structures
    deform_paths = read_yaml(f"{work_dir}/structure_dirs.yml")
    deform_crystals = [read(f"{p}/{K.FILE_FRAME_LABEL}") for p in deform_paths]

    compute_arg = pdict["elastic"].get("compute", {})
    if compute_arg.get("elastic_tensor", False):
        Elastic.fit_elastic_tensor(deform_crystals)
        Elastic.write_cij(f"{work_dir}/elastic_tensor.txt")
    if compute_arg.get("BM_EOS", False):
        Elastic.fit_BM_EOS(deform_crystals)
        Elastic.write_MB_EOS(f"{work_dir}/BMeos.txt")
        Elastic.write_MB_EOS_pv_data(f"{work_dir}/BMeos_pv_data.txt")
    return


#####ANCHOR Stage 5 - compute elastic constants
def compute_elastic(pdict: dict, mdict: dict):
    """Compute elastic constants from stress-strain tensors."""
    ### work_dir
    struct_startdir = mk_struct_dir(pdict)
    work_dir = f"{struct_startdir}/{K.DIR_ELASTIC}"
    make_dir(work_dir, backup=False)

    compute_arg = pdict["elastic"].get("compute", {})
    ### Copy elastic_tensor.txt
    structure_paths = read_yaml(f"{struct_startdir}/{K.DIR_SUPERCELL}/structure_dirs.yml")

    if compute_arg.get("elastic_tensor", False):
        _ = [
            move_file(
                f"{p}/elastic_tensor.txt",
                f"{p}/elastic_tensor.txt".replace(K.DIR_SUPERCELL, K.DIR_ELASTIC),
            )
            for p in structure_paths
        ]
    if compute_arg.get("BM_EOS", False):
        _ = [
            move_file(
                f"{p}/BMeos.txt",
                f"{p}/BMeos.txt".replace(K.DIR_SUPERCELL, K.DIR_ELASTIC),
            )
            for p in structure_paths
        ]
        _ = [
            move_file(
                f"{p}/BMeos_pv_data.txt",
                f"{p}/BMeos_pv_data.txt".replace(K.DIR_SUPERCELL, K.DIR_ELASTIC),
            )
            for p in structure_paths
        ]

    ### Compute elastic_properties in each subdir
    # for f in elastic_files:
    #     Cij = pl.read_csv(f, separator=" ")

    #     pass

    return


#####ANCHOR main loop of elastic_calculator
class WorkflowElastic(Workflow):
    """Workflow for Elastic tensor calculation."""

    def __init__(self, params_file: str, machines_file: str):
        super().__init__(params_file, machines_file, K.SCHEMA_ELASTIC)
        self.stage_map = {
            "make_structure": make_structure,
            "relax_initial_structure": relax_initial_structure,
            "strain_and_relax": strain_and_relax,
            "compute_stress": compute_stress_strain,
            "compute_elastic": compute_elastic,
        }
        self.wf_name = "ELASTIC CONSTANTS CALCULATION"
        return
