"""Data generation workflow implementation."""

import shutil
from copy import deepcopy
from pathlib import Path

from alff.al.libal_md_ase import temperature_press_mdarg_ase
from alff.base import KEY as K
from alff.base import Workflow, logger
from alff.gdata.libgen_gpaw import (
    OperGendataGpawAIMD,
    OperGendataGpawOptimize,
    # OperGendataGpawSinglepoint,
)
from alff.gdata.util_dataset import merge_extxyz_files, remove_key_in_extxyz
from alff.util.ase_tool import build_struct
from alff.util.tool import mk_struct_dir
from asext.cell import make_triangular_cell_extxyz
from asext.io.readwrite import read_extxyz, write_extxyz
from asext.struct import (
    perturb_struct,
    strain_struct,
)
from thkit.io import read_yaml, write_yaml
from thkit.path import (
    collect_files,
    copy_file,
    list_paths,
    make_dir,
    make_dir_ask_backup,
)
from thkit.range import composite_strain_points


#####ANCHOR Stage 1 - build structure
def make_structure(pdict, mdict):
    """Build structures based on input parameters."""
    ### Define work_dir
    struct_startdir = mk_struct_dir(pdict)
    make_dir_ask_backup(struct_startdir, logger)
    work_dir = f"{struct_startdir}/{K.DIR_MAKE_STRUCT}"

    logger.info(f"Working on the path: {work_dir}")
    write_yaml(pdict, f"{struct_startdir}/param.yml")

    ### Build structures
    struct_args = pdict["structure"]
    from_extxyz = struct_args.get("from_extxyz", False)
    if from_extxyz:
        ### will generate a list of configurations from all frames in all extxyz files)
        logger.info(f"Use structures from extxyz files: {from_extxyz}")
        extxyz_files = collect_files(from_extxyz, patterns=["*.extxyz"])
        merge_extxyz_files(extxyz_files=extxyz_files, outfile=f"{work_dir}/tmp_structs_from_extxyz")
        struct_list = read_extxyz(f"{work_dir}/tmp_structs_from_extxyz", index=":")
        for i, struct in enumerate(struct_list):
            write_extxyz(f"{work_dir}/struct_{i:{K.FMT_STRUCT}}/{K.FILE_FRAME_UNLABEL}", struct)
        Path(f"{work_dir}/tmp_structs_from_extxyz").unlink()  # clean
    else:
        logger.info("Build structures from scratch")
        struct_args = pdict["structure"].get("from_scratch")
        struct = build_struct(struct_args)
        write_extxyz(f"{work_dir}/struct_{0:{K.FMT_STRUCT}}/{K.FILE_FRAME_UNLABEL}", struct)

    ### Save structure_dirs (relative to run_dir)
    structure_dirs = list_paths(work_dir, patterns=["struct_*/"])
    write_yaml(structure_dirs, f"{work_dir}/structure_dirs.yml")

    ### Normalize the cell to upper/lower triangular form
    triangular_form = pdict["structure"].get("make_triangular_form", None)
    if triangular_form is not None:
        logger.info(f"Normalize the cell to '{triangular_form}' triangular form")
        for d in structure_dirs:
            extxyz_files = collect_files(d, patterns=[K.FILE_FRAME_UNLABEL, K.FILE_FRAME_LABEL])
            _ = [
                make_triangular_cell_extxyz(extxyz_file, form=triangular_form)
                for extxyz_file in extxyz_files
            ]
    return


#####ANCHOR Stage 2 - DFT optimize
def optimize_structure(pdict, mdict):
    """Optimize the structures."""
    logger.info("Optimize the structures")
    ### Define work_dir
    struct_startdir = mk_struct_dir(pdict)
    work_dir = f"{struct_startdir}/{K.DIR_MAKE_STRUCT}"
    _ = copy_file(f"{work_dir}/structure_dirs.yml", f"{work_dir}/task_dirs.yml")

    op = OperGendataGpawOptimize(work_dir, pdict, mdict, mdict_prefix="gpaw")
    op.prepare()
    op.run()
    op.postprocess()
    return


#####SECTION Stage 3 - Explore sampling space
def sampling_space(pdict, mdict):
    """Explore the sampling space.

    Sampling space includes:
    - Range of strains (in x, y, z directions) + range of temperatures
    - Range of temperatures + range of stresses

    Notes
        - Structure paths are save into 2 lists: original and sampling structure paths
    """
    ### Define work_dir
    struct_startdir = mk_struct_dir(pdict)
    work_dir = f"{struct_startdir}/{K.DIR_STRAIN}"
    make_dir(work_dir, backup=False)

    ### Copy/symlink files from structure_paths (unlabeled or labeled)
    origin_structure_dirs = read_yaml(f"{struct_startdir}/{K.DIR_MAKE_STRUCT}/structure_dirs.yml")
    structure_files = [
        copy_labeled_structure(p, p.replace(f"{K.DIR_MAKE_STRUCT}", f"{K.DIR_STRAIN}"))
        for p in origin_structure_dirs
    ]
    structure_dirs = [Path(p).parent.as_posix() for p in structure_files]
    write_yaml(structure_dirs, f"{work_dir}/structure_dirs.yml")

    ##### Explore sampling space
    space_args = pdict.get("sampling_space", {})
    if space_args:
        logger.info(f"Explore sampling spaces on the path: {work_dir}")

    ### Prepare ASE_arg for ranges of temperature and stress
    ase_args = deepcopy(pdict.get("dft"))  # deepcopy to avoid modifying `pdict`
    ase_args.pop("optimize", None)  # remove key optimize

    #####ANCHOR Sampling by strains + temperatures
    # TODO: use a class to handle strain/temperature sampling
    task_dirs1 = []
    strain_args = space_args.get("strain", {})
    if strain_args:
        strain_x_list = composite_strain_points(strain_args.get("strain_x", []))
        strain_y_list = composite_strain_points(strain_args.get("strain_y", []))
        strain_z_list = composite_strain_points(strain_args.get("strain_z", []))

        strain_structure_files = strain_x_dim(structure_files, strain_x_list)
        strain_structure_files = strain_y_dim(strain_structure_files, strain_y_list)
        strain_structure_files = strain_z_dim(strain_structure_files, strain_z_list)

        ### perturb (removed)
        # perturb_num = strain_args.get("perturb_num", 0)
        # perturb_disp = strain_args.get("perturb_disp", 0.001)
        # structure_files = perturb_structure(structure_files, perturb_num, perturb_disp)

        ### Save structure_paths (relative to run_dir)
        strain_structure_dirs = sorted([Path(p).parent.as_posix() for p in strain_structure_files])
        write_yaml(strain_structure_dirs, f"{work_dir}/strain_structure_dirs.yml")

        ### explore temperature range
        temperature_list1 = strain_args.get("temps", [])
        task_dirs1 = temperature_press_mdarg_ase(
            strain_structure_dirs, temperature_list1, [], ase_args
        )
    #####ANCHOR Sampling by strains + temperatures
    ### Prepare task paths for un-strained structures -> generate from the optimized structures (labelled), so need to copy to unlabelled ones.
    ## normlize the cell to avoid error in NPT run
    task_dirs2 = []
    temp_press_args = space_args.get("temp_press", {})
    if temp_press_args:
        temperature_list2 = temp_press_args.get("temps", [])
        press_list = temp_press_args.get("pressures", [])
        press_struct_files = [
            copy_file(f"{p}/{K.FILE_FRAME_LABEL}", f"{p}_press/{K.FILE_FRAME_UNLABEL}")
            if Path(f"{p}/{K.FILE_FRAME_LABEL}").is_file()
            else copy_file(f"{p}/{K.FILE_FRAME_UNLABEL}", f"{p}_tp/{K.FILE_FRAME_UNLABEL}")
            for p in structure_dirs
        ]
        press_structure_dirs = [Path(f).parent for f in press_struct_files]
        # _ = [make_triangular_cell_extxyz(f"{p}/{FILE_FRAME_UNLABEL}") for p in press_structure_dirs]
        task_dirs2 = temperature_press_mdarg_ase(
            press_structure_dirs, temperature_list2, press_list, ase_args
        )

    task_dirs = task_dirs1 + task_dirs2
    write_yaml(set(task_dirs), f"{work_dir}/task_dirs.yml")  # type: ignore
    return


#####ANCHOR Stage 4 - run DFTsinglepoint/AIMD
def run_dft(pdict, mdict):
    """Run DFT calculations."""
    logger.info("Run AIMD calculations")
    ### Define work_dir
    struct_startdir = mk_struct_dir(pdict)
    work_dir = f"{struct_startdir}/{K.DIR_STRAIN}"

    op = OperGendataGpawAIMD(work_dir, pdict, mdict, mdict_prefix="gpaw")
    op.prepare()
    op.run()
    op.postprocess()
    return


#####ANCHOR Stage 5 - Collect data
def collect_data(pdict, mdict):
    """Collect data from DFT simulations."""
    ### Define work_dir
    struct_startdir = mk_struct_dir(pdict)
    work_dir = f"{struct_startdir}/{K.DIR_GENDATA}"
    make_dir(work_dir, backup=False)
    logger.info(f"Collect data on the path: {work_dir}")

    ### Collect data
    data_files = collect_files(
        f"{struct_startdir}/{K.DIR_STRAIN}", patterns=[K.FILE_FRAME_LABEL, K.FILE_TRAJ_LABEL]
    )
    if len(data_files) > 0:
        merge_extxyz_files(
            extxyz_files=data_files,
            outfile=f"{work_dir}/{K.FILE_ITER_DATA}",
            sort_natoms=True,
            sort_pbc_len=True,
        )
        ### Remove unwanted keys
        remove_key_in_extxyz(f"{work_dir}/{K.FILE_ITER_DATA}", key_list=["timestep", "momenta"])
    return


#####ANCHOR main loop
class WorkflowGendata(Workflow):
    """Workflow for generate initial data for training ML models."""

    def __init__(self, params_file: str, machines_file: str):
        super().__init__(params_file, machines_file, K.SCHEMA_GENDATA)
        self.stage_map = {
            "make_structure": make_structure,
            "optimize_structure": optimize_structure,
            "sampling_space": sampling_space,
            "run_dft": run_dft,
            "collect_data": collect_data,
        }
        self.wf_name = "DATA GENERATION"
        return


#####ANCHOR Helper functions
def copy_labeled_structure(src_dir: str, dest_dir: str):
    """Copy labeled structures
    - First, try copy labeled structure if it exists.
    - If there is no labeled structure, copy the unlabeled structure.
    """
    Path(dest_dir).mkdir(parents=True, exist_ok=True)
    if Path(f"{src_dir}/{K.FILE_FRAME_LABEL}").is_file():
        new_path = shutil.copy2(
            f"{src_dir}/{K.FILE_FRAME_LABEL}", f"{dest_dir}/{K.FILE_FRAME_LABEL}"
        )
    elif Path(f"{src_dir}/{K.FILE_FRAME_UNLABEL}").is_file():
        new_path = shutil.copy2(
            f"{src_dir}/{K.FILE_FRAME_UNLABEL}", f"{dest_dir}/{K.FILE_FRAME_UNLABEL}"
        )
    return new_path  # type: ignore[unbounded]


def strain_x_dim(struct_files: list[str], strain_x_list: list[float]):
    """Scale the x dimension of the structures."""
    new_struct_files = struct_files.copy()
    for strain_x in strain_x_list:
        for struct_file in struct_files:
            struct_list = read_extxyz(struct_file)
            struct_list_scaled = [
                strain_struct(atoms, strains=[strain_x, 1, 1]) for atoms in struct_list
            ]
            new_filename = f"{Path(struct_file).parent}_x{strain_x}/{K.FILE_FRAME_UNLABEL}"
            write_extxyz(new_filename, struct_list_scaled)
            new_struct_files.append(new_filename)
    return new_struct_files


def strain_y_dim(struct_files: list[str], strain_y_list: list[float]):
    """Scale the y dimension of the structures."""
    new_struct_files = struct_files.copy()
    for strain_y in strain_y_list:
        for struct_file in struct_files:
            struct_list = read_extxyz(struct_file)
            struct_list_scaled = [
                strain_struct(atoms, strains=[1, strain_y, 1]) for atoms in struct_list
            ]
            new_filename = f"{Path(struct_file).parent}_y{strain_y}/{K.FILE_FRAME_UNLABEL}"
            write_extxyz(new_filename, struct_list_scaled)
            new_struct_files.append(new_filename)
    return new_struct_files


def strain_z_dim(struct_files: list[str], strain_z_list: list[float]):
    """Scale the z dimension of the structures."""
    new_struct_files = struct_files.copy()
    for strain_z in strain_z_list:
        for struct_file in struct_files:
            struct_list = read_extxyz(struct_file)
            struct_list_scaled = [
                strain_struct(atoms, strains=[1, 1, strain_z]) for atoms in struct_list
            ]
            new_filename = f"{Path(struct_file).parent}_z{strain_z}/{K.FILE_FRAME_UNLABEL}"
            write_extxyz(new_filename, struct_list_scaled)
            new_struct_files.append(new_filename)
    return new_struct_files


def perturb_structure(struct_files: list, perturb_num: int, perturb_disp: float):
    """Perturb the structures."""
    new_struct_files = struct_files.copy()
    for idx in range(perturb_num):
        for struct_file in struct_files:
            struct_list = read_extxyz(struct_file)
            struct_list_perturbed = [
                perturb_struct(atoms, std_disp=perturb_disp) for atoms in struct_list
            ]
            new_filename = f"{Path(struct_file).parent}_p{idx:03d}/{K.FILE_FRAME_UNLABEL}"
            write_extxyz(new_filename, struct_list_perturbed)
            new_struct_files.append(new_filename)
    return new_struct_files


def _total_struct_num(pdict: dict):
    space_arg = pdict.get("sampling_space", {})
    len_x = len(space_arg.get("strain_x", []))
    len_y = len(space_arg.get("strain_y", []))
    len_z = len(space_arg.get("strain_z", []))
    len_temp = len(space_arg.get("temperature", []))
    len_stress = len(space_arg.get("stress", []))

    total_confs = (len_temp * len_stress) * (
        (len_x * len_y * len_z)
        + (len_x * len_y)
        + (len_x * len_z)
        + (len_y * len_z)
        + len_x
        + len_y
        + len_z
        + 1
    )
    return total_confs
