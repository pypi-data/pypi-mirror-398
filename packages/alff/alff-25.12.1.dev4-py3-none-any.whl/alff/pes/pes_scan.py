"""Implementation of 2d PES scanning.
- Idea is to incrementally change the relative positions between 2 groups of atoms while calculating the energy of the system.
"""

from pathlib import Path

import polars as pl

from alff.base import KEY as K
from alff.base import Workflow, logger
from alff.gdata.gendata import copy_labeled_structure, make_structure
from alff.pes.libpes_gpaw import OperPESGpawOptimize, OperPESGpawOptimizeFixatom
from alff.pes.libpes_lammps import OperPESLammpsOptimize, OperPESLammpsOptimizeFixatom
from alff.pes.utilpes import (
    _extract_dxdydz,
    _extract_interlayer_distance,
    _filter_atoms,
    interp_pes_xy,
    interp_pes_z,
    plot_pes_xy,
    plot_pes_z,
    scan_x_dim,
    scan_y_dim,
    scan_z_dim,
)
from alff.util.tool import check_supported_calculator, mk_struct_dir
from asext.io.readwrite import read_extxyz
from thkit.io import read_yaml, write_yaml
from thkit.path import ask_yesno, make_dir
from thkit.range import composite_strain_points

#####SECTION stage funcs
#####ANCHOR Stage 1 - build structure
### Use the same function as in alff.gendata.make_structure.py


#####ANCHOR Stage 2 - relax initial structure by DFT/MD
### Refer the functions in alff.phonon.phonon.py
def relax_initial_structure(pdict, mdict):
    """Relax the structure by DFT/MD."""
    ### Define work_dir
    struct_startdir = mk_struct_dir(pdict)
    work_dir = f"{struct_startdir}/{K.DIR_MAKE_STRUCT}"
    structure_dirs = read_yaml(f"{work_dir}/structure_dirs.yml")
    write_yaml(structure_dirs, f"{work_dir}/task_dirs.yml")

    calc_name = pdict["calculator"].get("name")
    check_supported_calculator(calc_name)
    if calc_name == "gpaw":
        op = OperPESGpawOptimize(work_dir, pdict, mdict, mdict_prefix="gpaw")
        op.prepare()
        op.run()
    elif calc_name == "lammps":
        op = OperPESLammpsOptimize(work_dir, pdict, mdict, mdict_prefix="lammps")
        op.prepare()
        op.run()
        op.postprocess()
    return


#####ANCHOR Stage 3 - scanning space
def scanning_space(pdict, mdict):
    """Displace a group of atoms in a structure to generate a series of structures.

    - Save 2 lists of paths: original and scaled structure paths
    """
    ### Define work_dir
    struct_startdir = mk_struct_dir(pdict)
    work_dir = f"{struct_startdir}/{K.DIR_SCAN}"
    make_dir(work_dir, backup=False)

    ### Copy/symlink files from structure_paths (unlabeled or labeled)
    structure_paths = read_yaml(f"{struct_startdir}/{K.DIR_MAKE_STRUCT}/structure_dirs.yml")
    structure_files = [
        copy_labeled_structure(p, p.replace(f"{K.DIR_MAKE_STRUCT}", f"{K.DIR_SCAN}"))
        for p in structure_paths
    ]
    assert len(structure_files) == 1, "Only one structure file is expected in the scanning space."

    ### Contraint atoms
    constraint_arg = pdict.get("constraint", {})
    fix_arg = constraint_arg.get("fix_atoms", {})
    fix_idxs = fix_arg.get("idxs", [])
    if not fix_idxs:
        filters = fix_arg.get("filters", {})
        struct = read_extxyz(structure_files[0])[-1]
        fix_idxs = _filter_atoms(struct, filters)
    write_yaml(fix_idxs, f"{work_dir}/fix_idxs.yml")

    displace_arg = constraint_arg.get("displace_atoms", {})
    disp_idxs = displace_arg.get("idxs", [])
    if not disp_idxs:
        filters = displace_arg.get("filters", {})
        struct = read_extxyz(structure_files[0])[-1]
        disp_idxs = _filter_atoms(struct, filters)
    write_yaml(disp_idxs, f"{work_dir}/displace_idxs.yml")

    ### Scanning space
    scan_arg = pdict.get("scanning_space", {})
    scan_dx_list = composite_strain_points(scan_arg.get("scan_x", []))
    scan_dy_list = composite_strain_points(scan_arg.get("scan_y", []))
    scan_dz_list = composite_strain_points(scan_arg.get("scan_z", []))

    if scan_arg.get("scan_x", []) and scan_arg.get("scan_y", []) and scan_arg.get("scan_x", []):
        logger.warning(
            "Scanning in all three dimensions is extremely time-consuming. \
            It is recommended to scan xy-plane or z-direction only."
        )
        ans = ask_yesno("Are you sure want to continue?")
        if ans == "no":
            logger.info("User aborted.")
            return

    scan_structure_files = scan_x_dim(structure_files, disp_idxs, scan_dx_list)
    scan_structure_files = scan_y_dim(scan_structure_files, disp_idxs, scan_dy_list)
    scan_structure_files = scan_z_dim(scan_structure_files, disp_idxs, scan_dz_list)

    ### Save structure_paths (relative to run_dir)
    scan_structure_dirs = sorted([Path(p).parent.as_posix() for p in scan_structure_files])
    write_yaml(scan_structure_dirs, f"{work_dir}/task_dirs.yml")

    structure_dirs = [Path(p).parent.as_posix() for p in structure_files]
    write_yaml(structure_dirs, f"{work_dir}/structure_dirs.yml")
    return


#####ANCHOR Stage 4 - compute energy by DFT/MD
def compute_energy(pdict, mdict):
    """Compute energy for each scan-structure by DFT/MD.
    Using `conditional optimization`: fix atoms and optimize the rest.
    """
    ### work_dir
    struct_startdir = mk_struct_dir(pdict)
    work_dir = f"{struct_startdir}/{K.DIR_SCAN}"

    calc_name = pdict["calculator"].get("name")
    check_supported_calculator(calc_name)
    if calc_name == "gpaw":
        op = OperPESGpawOptimizeFixatom(work_dir, pdict, mdict, mdict_prefix="gpaw")
        op.prepare()
        op.run()
    elif calc_name == "lammps":
        op = OperPESLammpsOptimizeFixatom(work_dir, pdict, mdict, mdict_prefix="lammps")
        op.prepare()
        op.run()
        op.postprocess()
    return


#####ANCHOR Stage 5 - compute PES
def compute_pes(pdict, mdict):
    """Collect energies computed in the previous stage and do some post-processing."""
    ### work_dir
    struct_startdir = mk_struct_dir(pdict)
    work_dir = f"{struct_startdir}/{K.DIR_PES}"
    make_dir(work_dir, backup=False)

    ### Collect energy files
    task_dirs = read_yaml(f"{struct_startdir}/{K.DIR_SCAN}/task_dirs.yml")
    rawdata: list = [None] * len(task_dirs)
    for i, tdir in enumerate(task_dirs):
        struct = read_extxyz(f"{tdir}/{K.FILE_FRAME_LABEL}")[-1]
        energy = struct.calc.results.get("energy", None)  # type: ignore
        stress = struct.calc.results.get("stress", None)  # type: ignore
        dx, dy, dz = _extract_dxdydz(mystring=Path(tdir).name)
        rawdata[i] = [dx, dy, dz, energy]
        rawdata[i].extend(stress)  # type: ignore
        write_yaml({"dx": dx, "dy": dy, "dz": dz}, f"{tdir}/dxdydz.yml")

    ### Output pes_raw_data np.array(rawdata).astype(float)
    df = pl.DataFrame(
        rawdata,
        schema=["dx", "dy", "dz", "energy", "pxx", "pyy", "pzz", "pyz", "pxz", "pxy"],
        orient="row",
    )
    df = df.sort(["dx", "dy", "dz"])

    # rawdata = np.array(rawdata, dtype=float)
    # sorted_idx = np.lexsort((rawdata[:, 2], rawdata[:, 1], rawdata[:, 0]))  # sort by dx, dy, dz
    # rawdata = rawdata[sorted_idx]
    # header = "dx dy dz energy pxx pyy pzz pyz pxz pxy"
    # np.savetxt(f"{work_dir}/rawdata.txt", rawdata, fmt="%6f", header=header, comments="")

    ### natoms
    struct0 = read_extxyz(f"{task_dirs[0]}/{K.FILE_FRAME_LABEL}")[-1]
    n_atoms = len(struct0)
    df = df.with_columns((pl.col("energy") / n_atoms).alias("energy/atom"))
    df.write_csv(f"{work_dir}/rawdata.csv", float_precision=6)

    ### Interpolate PES
    grid_size = pdict.get("pes", {}).get("grid_size", 0.05)
    scan_arg = pdict.get("scanning_space", {})
    if pdict.get("pes", {}).get("interp_pes_xy", False):
        if not scan_arg.get("scan_x", {}) and not scan_arg.get("scan_y", {}):
            raise ValueError(
                "The interpolation of PES in xy plane, must be used with sampling spaces: scan_x and scan_y."
            )
        df_xy = interp_pes_xy(df, grid_size)
        df_xy.write_csv(f"{work_dir}/grid_pes_xy.csv", float_precision=6)
        plot_pes_xy(file_pes_grid=f"{work_dir}/grid_pes_xy.csv")
        ### Estimate delta_e_barrier
        barrier = df_xy.select(pl.max("delta_e")).item()
        tmp_dict = {"delta_e_barrier": float(barrier)}
        write_yaml(tmp_dict, f"{work_dir}/delta_e_barrier.yml")

    if pdict.get("pes", {}).get("interp_pes_z", False):
        if not scan_arg.get("scan_z", {}):
            raise ValueError(
                "The interpolation of PES along z direction, must be used with sampling space: scan_z."
            )
        df_z = interp_pes_z(df, grid_size)
        df_z.write_csv(f"{work_dir}/grid_pes_z.csv", float_precision=6)
        plot_pes_z(
            file_pes_grid=f"{work_dir}/grid_pes_z.csv", file_pes_raw=f"{work_dir}/rawdata.csv"
        )
        ## Estimate minimum position
        min_values = (
            df_z.filter(pl.col("delta_e") == pl.col("delta_e").min())
            .select(["grid_z", "delta_e"])
            .to_numpy()
        )
        tmp_dict = {"min_z": float(min_values[0][0]), "min_delta_e": float(min_values[0][1])}
        write_yaml(tmp_dict, f"{work_dir}/min_z.yml")

    ### Extract interlayer distance
    fix_idxs = read_yaml(f"{struct_startdir}/{K.DIR_SCAN}/fix_idxs.yml")
    distance = _extract_interlayer_distance(struct0, fix_idxs)
    tmp_dict = {"interlayer_distance": float(distance)}
    write_yaml(tmp_dict, f"{work_dir}/interlayer_distance.yml")
    return


#####!SECTION


#####ANCHOR main loop of pes_scan
class WorkflowPes(Workflow):
    """Workflow for PES scanning calculation."""

    def __init__(self, params_file: str, machines_file: str):
        super().__init__(params_file, machines_file, K.SCHEMA_PES_SCAN)
        self.stage_map = {
            "make_structure": make_structure,
            "relax_initial_structure": relax_initial_structure,
            "scanning_space": scanning_space,
            "compute_energy": compute_energy,
            "compute_pes": compute_pes,
        }
        self.wf_name = "PES SCANNING CALCULATION"
        return
