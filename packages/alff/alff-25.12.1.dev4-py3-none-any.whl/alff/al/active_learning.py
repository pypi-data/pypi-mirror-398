"""Active Learning workflow implementation."""

from pathlib import Path

from natsort import natsorted

from alff.al.libal_md_ase import OperAlmdAseSevennet, premd_ase_sevenn
from alff.al.libal_md_lammps import OperAlmdLammpsSevennet, premd_lammps_sevenn
from alff.al.mlp.mlp_sevenn import OperAltrainSevennet, pretrain_sevenn
from alff.base import KEY as K
from alff.base import Workflow, logger
from alff.gdata.libgen_gpaw import OperAlGpawSinglepoint
from alff.gdata.util_dataset import (
    merge_extxyz_files,
    remove_duplicate_structs_hash,
    remove_key_in_extxyz,
)
from asext.io.readwrite import read_extxyz, write_extxyz
from asext.struct import check_bad_box
from thkit.io import read_yaml, write_yaml
from thkit.markup import TextDecor
from thkit.path import collect_files, make_dir, make_dir_ask_backup


#####ANCHOR Stage training
def stage_train(iter_idx, pdict, mdict):
    """Stage function for ML training tasks.

    This function includes: preparing training data and args, running training, and postprocessing.
    - collect data files
    - prepare training args based on MLP engine
    """
    pdict_train = pdict["train"]

    ### Create work_dir folder
    work_dir = f"{iter_str(iter_idx)}/{K.DIR_TRAIN}"
    make_dir_ask_backup(work_dir, logger)

    logger.info("Collect and prepare dataset")
    ### Collect initial data files: dict[list[str]] = {"init": [], "iter_0": [], ...}
    datadict = {}  # relative to run_dir
    datadict["init"] = natsorted(
        collect_files(pdict_train["init_data_paths"], patterns=["*.extxyz"])
    )

    ### Collect data from previous iterations
    previous_dirs = [f"{iter_str(i)}/{K.DIR_DATA}" for i in range(iter_idx)]
    datadict["iteration"] = collect_files(previous_dirs, patterns=["*.extxyz"])
    write_yaml(datadict, f"{work_dir}/{K.FILE_DATAPATH}")

    ### Copy data files to tmp_folder: `copied_data/`
    data_files: list[str] = [f for value in datadict.values() for f in value]
    data_files = list(set(data_files))  # remove duplicates
    assert len(data_files) > 0, "No data files found"
    merge_extxyz_files(
        extxyz_files=data_files, outfile=f"{work_dir}/{K.DIR_COLLECTDATA}/{K.FILE_COLLECT_DATA}"
    )

    ### Setup to continue previous train
    continue_train = pdict_train.get("continue_train", True)
    if (iter_idx > 0) and continue_train:
        previous_iter = iter_str(iter_idx - 1)
        checkpoints = read_yaml(f"{previous_iter}/{K.DIR_TRAIN}/{K.FILE_CHECKPOINTS}")
        pdict["train"]["init_checkpoints"] = checkpoints  # relative to run_dir -> change pdict

    ### Prepare train args
    mlp_model = _get_mlp_model(pdict)
    if mlp_model in ["sevenn", "sevenn_mliap"]:
        pretrain_sevenn(work_dir, pdict, mdict)
        op = OperAltrainSevennet(work_dir, pdict, mdict, mdict_prefix="train")
        op.prepare()
        op.run()
        op.postprocess()
    return


#####ANCHOR Stage MD
def stage_md(iter_idx, pdict, mdict):
    """Stage function for MD exploration tasks.

    Including: pre, run, post MD.
    - Collect initial configurations
    - Prepare MD args
    - Submit MD jobs to remote machines
    - Postprocess MD results
    """
    work_dir = f"{iter_str(iter_idx)}/{K.DIR_MD}"
    make_dir_ask_backup(work_dir, logger)

    ### Sampling spaces
    sampling_spaces = pdict["md"]["sampling_spaces"]  # list[dict]
    current_space = sampling_spaces[iter_idx]  # dict
    write_yaml(current_space, f"{work_dir}/current_space.yml")

    logger.info("Prepare MD args")
    ### Prepare MD args and run MD
    mlp_model, md_calculator = _get_mlp_model(pdict), _get_md_calculator(pdict)
    if mlp_model in ["sevenn", "sevenn_mliap"]:
        if md_calculator == "ase":
            premd_ase_sevenn(work_dir, pdict, mdict)
            op = OperAlmdAseSevennet(work_dir, pdict, mdict, mdict_prefix="ase")
            op.prepare()
            op.run()
            op.postprocess()
        elif md_calculator == "lammps":
            premd_lammps_sevenn(work_dir, pdict, mdict)
            op = OperAlmdLammpsSevennet(work_dir, pdict, mdict, mdict_prefix="lammps")
            op.prepare()
            op.run()
            op.postprocess()
    # elif mlp_model == "mace":
    #     pre_md_mace(iter_idx, pdict, mdict)

    ### Collect MD candidate structures
    outfile = f"{Path(work_dir) / K.DIR_CANDIDATE}/ md_candidates.extxyz"
    _collect_md_candidates(work_dir, outfile)
    return


def _collect_md_candidates(work_dir: str, outfile: str) -> None:
    """Collect MD candidate structures for DFT labeling."""
    # can add more custom `*extxyz`` files to folder `K.DIR_CANDIDATE/`. These files will also be collected for DFT labeling.
    md_task_dirs: list[str] = read_yaml(f"{work_dir}/task_dirs.yml")
    extxyz_files = collect_files(md_task_dirs, patterns=[K.FILE_TRAJ_MD_CANDIDATE])
    merge_extxyz_files(extxyz_files, outfile=f"{work_dir}/{outfile}")
    return


#####ANCHOR Stage DFT
def stage_dft(iter_idx, pdict, mdict):
    """Stage function for DFT labeling tasks.
    Including: pre, run, post DFT.
    """
    work_dir = f"{iter_str(iter_idx)}/{K.DIR_DFT}"
    make_dir_ask_backup(work_dir, logger)

    logger.info("Collect candidate structures")
    ### Copy candidate extxyz from previous MD
    candidate_dir = f"{iter_str(iter_idx)} / {K.DIR_MD} / {K.DIR_CANDIDATE}"
    candidate_files = collect_files([candidate_dir], patterns=["*.extxyz"])

    candidate_extxyz = f"{work_dir}/candidates.extxyz"
    merge_extxyz_files(
        extxyz_files=candidate_files,
        outfile=candidate_extxyz,
        sort_natoms=True,
        sort_pbc_len=True,
    )
    remove_duplicate_structs_hash(extxyz_file=candidate_extxyz, tol=1e-6, backup=False)

    logger.info("Prepare DFT tasks")
    ### Create dft task_dirs
    struct_list = read_extxyz(candidate_extxyz, index=":")
    dft_task_dirs: list = [None] * len(struct_list)
    bad_box_list: list = [None] * len(struct_list)
    for i, struct in enumerate(struct_list):
        is_bad = check_bad_box(
            struct, criteria={"length_ratio": 20, "wrap_ratio": 0.6, "tilt_ratio": 0.6}
        )
        if not is_bad:
            new_dir = f"{work_dir}/dft_{i:{K.FMT_TASK_DFT}}"  # relative to run_dir
            make_dir(new_dir, backup=False)
            struct.write(f"{new_dir}/{K.FILE_FRAME_UNLABEL}", format="extxyz")
            dft_task_dirs[i] = new_dir
        else:
            bad_box_list[i] = struct

    dft_task_dirs = [d for d in dft_task_dirs if d is not None]
    task_dirs = dft_task_dirs
    write_yaml(task_dirs, f"{work_dir}/task_dirs.yml")

    ### Write bad box struct
    bad_box_list = [a for a in bad_box_list if a is not None]
    if len(bad_box_list) > 0:
        filename = f"{work_dir}/found_{len(bad_box_list)}_badbox_struct.extxyz"
        write_extxyz(filename, bad_box_list)
        logger.warning(f"Found {len(bad_box_list)} bad-box struct, see file:\n\t'{filename}'")

    ### Submit remote jobs
    op = OperAlGpawSinglepoint(work_dir, pdict, mdict, mdict_prefix="gpaw")
    op.prepare()
    op.run()
    op.postprocess()

    ### Collect DFT labeled data
    data_outfile = f"{Path(work_dir).parent / K.DIR_DATA}/{K.FILE_ITER_DATA}"
    logger.info(f"Collect DFT labeled data: {data_outfile}")
    _collect_dft_label_data(dft_task_dirs, data_outfile)
    return


def _collect_dft_label_data(dft_task_dirs: list[str], data_outfile: str):
    """Collect DFT labeled data from `dft_task_dirs` to file `work_dir/DIR_DATA/FILE_ITER_DATA`.

    Args:
        dft_task_dirs (list[str]): List of structure directories to collect data from.
        data_outfile (str): The working directory to store collected data.

    Raises:
        RuntimeError: If no data is generated in this iteration.
    """
    extxyz_files = collect_files(dft_task_dirs, patterns=[K.FILE_FRAME_LABEL])
    if len(extxyz_files) > 0:
        merge_extxyz_files(
            extxyz_files,
            outfile=data_outfile,
            sort_natoms=True,
            sort_pbc_len=True,
        )
        ### Remove unwanted keys
        remove_key_in_extxyz(
            data_outfile,
            key_list=["free_energy", "magmom", "magmoms", "dipole", "momenta", "timestep"],
        )
    else:
        raise RuntimeError(
            "No data generated in this iteration. Check the preceding MD/DFT stages."
        )
    return


#####ANCHOR Active Learning loop
class WorkflowActiveLearning(Workflow):
    """Workflow for active learning.
    Note: Need to redefine `.run()` method, since the Active Learning workflow is different from the base class.
    """

    def __init__(self, params_file: str, machines_file: str):
        super().__init__(params_file, machines_file, K.SCHEMA_ACTIVE_LEARN)
        self.stage_map = {
            "ml_train": stage_train,
            "md_explore": stage_md,
            "dft_label": stage_dft,
        }
        self.wf_name = "ACTIVE LEARNING"
        return

    def run(self):
        self._print_intro()
        pdict = self.pdict
        multi_mdicts = self.multi_mdicts
        stage_map = self.stage_map

        ### main loop
        iter_log = read_iterlog()  # check iter_record
        if iter_log[1] > -1:
            logger.info(
                f"continue from iter_{iter_log[0]:{K.FMT_ITER}} stage_{iter_log[1]:{K.FMT_STAGE}}"
            )

        sampling_spaces = pdict["md"].get("sampling_spaces", [])
        for iter_idx in range(len(sampling_spaces)):
            if iter_idx < iter_log[0]:  # skip recoded iter
                continue

            logger.info(breakline_iter(iter_idx))
            for stage_idx, (stage_name, stage_func) in enumerate(stage_map.items()):
                if stage_idx <= iter_log[1]:  # skip recoded stage, only 1 time
                    continue
                self._update_config()  # update if config changes
                logger.info(breakline_stage(iter_idx, stage_idx, stage_name))
                stage_func(iter_idx, pdict, multi_mdicts)
                write_iterlog(iter_idx, stage_idx, stage_name)
            iter_log[1] = -1  # reset stage_idx

        ### Training the last data
        if iter_idx == range(len(sampling_spaces))[-1]:  # continue from last iter # type: ignore
            iter_idx += 1  # type: ignore
            stage_list = ["ml_train"]
            for stage_idx, stage_name in enumerate(stage_list):
                if stage_idx <= iter_log[1]:  # skip recoded stage, only 1 time
                    continue
                logger.info(breakline_stage(iter_idx, stage_idx, f"{stage_name} (last train)"))
                stage_func = stage_map[stage_name]
                stage_func(iter_idx, pdict, multi_mdicts)
                write_iterlog(iter_idx, stage_idx, f"{stage_name} (last train)")

        self._print_outro()
        return


#####ANCHOR Helper functions
def _get_mlp_model(pdict) -> str:
    mlp_model = pdict.get("train", {}).get("mlp_model", "sevenn_mliap")
    avail_mlp_models = ["sevenn", "sevenn_mliap"]
    if mlp_model not in avail_mlp_models:
        raise ValueError(
            f"Unknown mlp_model '{mlp_model}'. Supported models are: {avail_mlp_models}"
        )
    return mlp_model


def _get_md_calculator(pdict) -> str:
    md_calculator = pdict.get("md", {}).get("md_calculator", "ase")
    avail_md_calculators = ["ase", "lammps"]
    if md_calculator not in avail_md_calculators:
        raise ValueError(
            f"Unknown md_calculator '{md_calculator}'. Supported calculators are: {avail_md_calculators}"
        )
    return md_calculator


def write_iterlog(iter_idx: int, stage_idx: int, stage_name: str, last_iter: bool = True) -> None:
    """Write the current iteration and stage to the iter log file.
    If `last_iter` is True, only the last iteration is saved.
    """
    header = "## 1st-column is the iteration index \n## 2nd-column is the stage index: \n\t# 0 ml_train \n\t# 1 md_explore \n\t# 2 dft_label \n\n"
    Path(K.FILE_ITERLOG).parent.mkdir(parents=True, exist_ok=True)  # Ensure directory exists
    if last_iter:
        with open(K.FILE_ITERLOG, "w") as f:
            f.write(f"{header}")
            f.write(f"{iter_idx:d} {stage_idx:d} \t# {stage_name}\n")
    else:
        with open(K.FILE_ITERLOG, "a") as f:
            f.write(f"{iter_idx:d} {stage_idx:d} \t# {stage_name}\n")
    return


def read_iterlog() -> list[int]:
    """Read the iter log file."""
    iter_log = [0, -1]
    if Path(K.FILE_ITERLOG).is_file():
        with open(K.FILE_ITERLOG) as f:
            lines = f.readlines()
        lines = [line.partition("#")[0].strip() for line in lines if line.partition("#")[0]]
        if len(lines) > 0:
            iter_log = [int(x) for x in lines[-1].split()]
    return iter_log


def iter_str(iter_idx: int) -> str:
    return f"iter_{iter_idx:{K.FMT_ITER}}"


def breakline_iter(iter_idx: int) -> str:
    text = f" {iter_str(iter_idx)} "
    return TextDecor(text).fill_left(margin=20, fill_left="=", length=52)


def breakline_stage(iter_idx: int, stage_idx: int, stage_name: str) -> str:
    text = f" {iter_str(iter_idx)} stage_{stage_idx:{K.FMT_STAGE}} {stage_name} "
    return TextDecor(text).fill_left(margin=20, fill_left="-", length=52)
