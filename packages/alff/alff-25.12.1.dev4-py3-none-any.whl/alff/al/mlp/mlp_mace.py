"""Library for MLP training using MACE."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from alff.util.key import (
        DIR_TRAIN,
        FILE_ARG_TRAIN,
        FILE_DATAPATH,
        FMT_MODEL,
    )
    from alff.util.tool import iter_str
import os
import random
import subprocess
from glob import glob
from pathlib import Path

from alff.base import logger
from alff.gdata.util_dataset import merge_extxyz_files
from thkit.io import list2txt, txt2list, write_yaml
from thkit.path import collect_files, make_dir


def pre_train_mace(iter_idx, pdict, mdict):
    train_param = pdict["train"]

    ### Generate work_dir folders
    iter_name = iter_str(iter_idx)
    work_dir = Path(f"{iter_name}/{DIR_TRAIN}")
    make_dir(work_dir)

    ## link init data
    xyz_files = collect_files(train_param["init_data_paths"], patterns=[".xyz"])
    list2txt(xyz_files, f"{work_dir}/data_init.txt")

    ## link iter data
    for idx in range(iter_idx):
        iter_path = iter_str(idx)
        xyz_files = collect_files(iter_path, patterns=[".xyz"])
        list2txt(xyz_files, f"{work_dir}/data_{iter_path}.txt")

    ### Collect all the extxyz data
    data_files = collect_files(f"{work_dir}", patterns=["data_*.txt"])
    all_extxyz_files = []
    for f in data_files:
        files = txt2list(f)
        all_extxyz_files.extend(files)
    merge_extxyz_files(extxyz_files=all_extxyz_files, outfile=f"{work_dir}/{FILE_DATAPATH}")
    #
    #

    init_data_sys = []
    init_batch_size = []
    # if "init_batch_size" in pdict:
    #     init_batch_size_ = list(pdict["init_batch_size"])
    #     if len(init_data_sys_) > len(init_batch_size_):
    #         warnings.warn(
    #             "The batch sizes are not enough. Assume auto for those not spefified.",
    #         )
    #         init_batch_size.extend(
    #             ["auto" for aa in range(len(init_data_sys_) - len(init_batch_size))],
    #         )
    # else:
    #     init_batch_size_ = ["auto" for aa in range(len(pdict["init_data_sys"]))]
    # if "sys_batch_size" in pdict:
    #     sys_batch_size = pdict["sys_batch_size"]
    # else:
    #     sys_batch_size = ["auto" for aa in range(len(pdict["initial_structures"]))]

    #
    #
    old_range = None
    if iter_idx > 0:
        for ii in range(iter_idx):
            if ii == iter_idx - 1:
                old_range = len(init_data_sys)
            fp_path = os.path.join(iter_str(ii), DIR_FP)
            fp_data_sys = glob.glob(os.path.join(fp_path, "data.*"))

            for jj in fp_data_sys:
                sys_idx = int(jj.split(".")[-1])
                sys_paths = expand_sys_str(jj)
                nframes = 0
                for sys_single in sys_paths:
                    nframes += dpdata.LabeledSystem(
                        sys_single,
                        fmt="deepmd/npy",
                    ).get_nframes()
                if auto_ratio:
                    if ii == iter_idx - 1:
                        number_new_frames += nframes
                    else:
                        number_old_frames += nframes
                if nframes < fp_task_min:
                    log_task(
                        "nframes (%d) in data sys %s is too small, skip" % (nframes, jj),
                    )
                    continue
                for sys_single in sys_paths:
                    init_data_sys.append(
                        Path(
                            os.path.normpath(os.path.join("../data.iters", sys_single)),
                        ).as_posix(),
                    )
                    batch_size = (
                        sys_batch_size[sys_idx] if sys_idx < len(sys_batch_size) else "auto"
                    )
                    init_batch_size.append(detect_batch_size(batch_size, sys_single))

    #
    #
    #
    #

    #

    ### MACE common args for all models
    # mace_args = revise_mace_cli_args(train_param["mace_args"])
    mace_args = train_param["mace_args"]
    mace_args["train_file"] = f"../{FILE_DATAPATH}"  # common file in work_dir
    mace_args["results_dir"] = "logs"

    ### establish tasks (one folder for each training model)
    num_models = train_param["num_models"]
    for model_idx in range(num_models):
        model_path = Path(f"{work_dir}/{FMT_MODEL % model_idx}")
        make_dir(model_path)
        ### Set more args for each model
        mace_args["seed"] = random.randrange(2**16)
        write_yaml(mace_args, f"{model_path}/{FILE_ARG_TRAIN}")

    ### symlink to old models
    if iter_idx > 0:
        prev_iter_name = iter_str(iter_idx - 1)
        prev_work_dir = Path(f"{prev_iter_name}/{DIR_TRAIN}")
        for model_idx in range(num_models):
            prev_model_path = Path(f"{prev_work_dir} / {FMT_MODEL % model_idx}")
            # TODO: modify this part
            # WARNING: Cannot find checkpoint with tag 'water_1k_small_run-123' in './checkpoints'
            # mace try to find the checkpoint in the current work_dir file file name: f"./checkpoints/{name}_run-{seed}"
            # so we need to create a link to the old model file with this name

            old_model_files = glob(os.path.join(prev_model_path, "model.ckpt*"))
            _link_old_models(work_dir, old_model_files, ii)
    else:
        # if isinstance(training_iter0_model, str):
        #     training_iter0_model = [training_iter0_model]
        # iter0_models = []
        # for ii in training_iter0_model:
        #     model_is = glob.glob(ii)
        #     model_is.sort()
        #     iter0_models += [os.path.abspath(ii) for ii in model_is]
        # if training_init_model:
        #     assert num_models == len(iter0_models), (
        #         "training_iter0_model should be provided, and the number of models should be equal to %d"
        #         % num_models
        #     )
        # for ii in range(len(iter0_models)):
        #     old_model_path = os.path.join(iter0_models[ii], "model.ckpt*")
        #     old_model_files = glob.glob(old_model_path)
        #     if not len(old_model_files):
        #         raise FileNotFoundError(f"{old_model_path} not found!")
        #     _link_old_models(work_dir, old_model_files, ii)

        # print("Thang: not implemented")
        #

        #
        pass

    #
    # copied_models = next(
    #     (
    #         item
    #         for item in (training_init_frozen_model, training_finetune_model)
    #         if item is not None
    #     ),
    #     None,
    # )
    # if copied_models is not None:
    #     for ii in range(len(copied_models)):
    #         _link_old_models(
    #             work_dir,
    #             [copied_models[ii]],
    #             ii,
    #             basename=f"init{suffix}",
    #         )

    #


#
#
#
#

#

# Copy user defined forward files
# symlink_user_forward_files(mdict=mdict, task_type="train", work_dir=work_dir)


def _link_old_models(work_dir, old_model_files, ii, basename: str = None):
    """Link the `ii`th old model given by `old_model_files` to
    the `ii`th training task in `work_dir`.
    """
    task_path = os.path.join(work_dir, FMT_MODEL % ii)
    task_old_path = os.path.join(task_path, "old")
    make_dir(task_old_path)
    cwd = os.getcwd()
    for jj in old_model_files:
        absjj = os.path.abspath(jj)
        if basename is None:
            basejj = os.path.basename(jj)
        else:
            basejj = basename
        os.chdir(task_old_path)
        os.symlink(os.path.relpath(absjj), basejj)
        os.chdir(cwd)


def run_train_mace(iter_idx, pdict, mdict):
    train_param = pdict["train"]
    train_mdict = mdict["train"]

    ### Prepare command_list (will be executed in order on the remote machine)
    command_list = []
    # command = f"{{ if [ ! -f model.ckpt{ckpt_suffix} ]; then {command}{init_flag}; else {command} --restart model.ckpt; fi }}"
    # command = f"/bin/sh -c {shlex.quote(command)}"
    # command_list.append(command)

    ## mace_command
    train_command = train_param.get("command", "mace_run_train")
    if train_command == "mace_run_train":
        command_list.append("export MACE_PATH=$(python -c 'import mace; print(mace.__path__[0])')")
        train_command = "python $MACE_PATH/cli/run_train.py"
        ## run MPI
        if "distributed" in train_param["mace_args"]:
            if train_param["mace_args"]["distributed_env"] == "openmpi":
                train_command = f"mpirun -np $NSLOTS {train_command}"
        train_command = f"{train_command} --config={FILE_ARG_TRAIN}"

    command_list.append(train_command)

    ### Prepare tasks
    iter_name = iter_str(iter_idx)
    work_dir = Path(f"{iter_name}/{DIR_TRAIN}").as_posix()
    num_models = train_param["num_models"]
    task_dirs = []
    for model_idx in range(num_models):
        task_dirs.append(FMT_MODEL % model_idx)

    ### Prepare ford & back files
    forward_common_files = [FILE_DATAPATH]  # in work_dir

    forward_files = [FILE_ARG_TRAIN]  # in task_path
    # if training_init_model:
    #     forward_files.append(Path("old/model.ckpt.pt"))
    # elif training_init_frozen_model is not None or training_finetune_model is not None:
    #     forward_files.append(os.path.join(f"old/init.pt"))

    backward_files = [
        "checkpoints/*",
        "logs/*",
        "valid_indices_*.txt",
        "*.model",
    ]

    ### Extra keywords to set more ford & back files
    # forward_files += train_mdict.get("extra_forward_files", [])
    # backward_files += train_mdict.get("extra_backward_files", [])

    ### Submit jobs
    submit_job(
        train_mdict["machine"],
        train_mdict["resources"],
        command_list=command_list,
        work_dir=work_dir,
        task_dirs=task_dirs,
        forward_files=forward_files,
        backward_files=backward_files,
        forward_common_files=forward_common_files,
        outlog="train.log",
        errlog="train.err",
    )


def post_train_mace(iter_idx, pdict, mdict):
    import mace

    train_param = pdict["train"]
    iter_name = iter_str(iter_idx)
    work_dir = Path(f"{iter_name}/{DIR_TRAIN}")

    logger.info(f"Converting MACE model to LAMMPS at: {work_dir.as_posix()}")
    ### Convert MACE model to LAMMPS
    py_path = Path(f"{mace.__path__[0]}/cli/create_lammps_model.py")
    if not py_path.exists():
        raise FileNotFoundError(
            f"{py_path} is not found! Check MACE installation. Note: don't use `-e` in pip install."
        )
    py_command = f"""python {py_path} {train_param["mace_args"]["name"]}.model"""

    num_models = train_param["num_models"]
    for model_idx in range(num_models):
        model_path = Path(f"{work_dir}/{FMT_MODEL % model_idx}")
        subprocess.run(py_command, cwd=model_path, shell=True, check=True)
