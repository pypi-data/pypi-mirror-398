"""Library for MLP training using SEVENNET."""

from thkit.pkg import check_package

check_package("sevenn", auto_install=False)

import random
import shutil
from pathlib import Path

from ase.io import read
from natsort import natsorted

from alff.al.mlp.util_mlp import Xyz2GraphData, suggest_num_epochs
from alff.base import KEY as K
from alff.base import RemoteOperation, logger
from alff.gdata.util_dataset import split_extxyz_dataset
from thkit.io import write_yaml
from thkit.path import copy_file, list_paths, make_dir


#####ANCHOR Active-learning: Training using SEVENNET
def pretrain_sevenn(work_dir, pdict, mdict):
    """Prepare arguments and data for ML training.

    Includes:
    - split dataset into train/valid sets
    - build graph_data using SEVENN graph_build
    - prepare SEVENN args
    - establish train tasks (one folder for each training model)
    - Save all common_files in DIR_FWDATA for convenience in transferring files

    Notes:
        - DIR_COLLECTDATA: is `tmp` directory containing collected extxyz data
        - DIR_FWDATA: directory containing `common_files` to forward to remote machines
    """
    pdict_train = pdict["train"]

    logger.info("Split dataset")
    ### Split extxyz dataset
    graphbuild_args = pdict_train.get("preprocess_data", {})
    train_ratio = graphbuild_args.get("trainset_ratio", 0.9)
    valid_ratio = graphbuild_args.get("validset_ratio", 0.1)
    split_extxyz_dataset(
        extxyz_files=[f"{work_dir}/{K.DIR_COLLECTDATA}/{K.FILE_COLLECT_DATA}"],
        train_ratio=train_ratio,
        valid_ratio=valid_ratio,
        outfile_prefix=f"{work_dir}/{K.DIR_COLLECTDATA}/data",  # will be: data_trainset.extxyz, data_validset.extxyz
    )

    ### Build graph_data (sevenn graph_build): for trainset and validset
    ## ref: https://github.com/MDIL-SNU/SevenNet/blob/main/sevenn/main/sevenn_graph_build.py
    logger.info("Build graph data")
    if Path(f"{work_dir}/{K.DIR_FWDATA}/sevenn_data").exists():
        shutil.rmtree(f"{work_dir}/{K.DIR_FWDATA}/sevenn_data")

    num_cores = graphbuild_args.get("num_cores", 1)
    ase_kwargs = graphbuild_args.get("ase_kwargs", {})

    sevenn_args = pdict_train["sevenn_args"]
    cutoff = sevenn_args["model"].get("cutoff")

    Xyz2GraphData.build_graph_sevenn(
        files=[f"{work_dir}/{K.DIR_COLLECTDATA}/data_trainset.extxyz"],
        outdir=f"{work_dir}/{K.DIR_FWDATA}",
        outfile="graph_trainset.pt",
        num_cores=num_cores,
        cutoff=cutoff,
        **ase_kwargs,
    )
    if valid_ratio > 0:
        Xyz2GraphData.build_graph_sevenn(
            files=[f"{work_dir}/{K.DIR_COLLECTDATA}/data_validset.extxyz"],
            outdir=f"{work_dir}/{K.DIR_FWDATA}",
            outfile="graph_validset.pt",
            num_cores=num_cores,
            cutoff=cutoff,
            **ase_kwargs,
        )

    logger.info("Prepare training args")
    ### SEVENN args (note: use preprocess-data, see run section below)
    sevenn_args["data"]["load_trainset_path"] = [f"../{K.DIR_FWDATA}/sevenn_data/graph_trainset.pt"]
    if valid_ratio > 0:
        sevenn_args["data"]["load_validset_path"] = [
            f"../{K.DIR_FWDATA}/sevenn_data/graph_validset.pt"
        ]

    ### Guess num_epochs
    num_grad_updates = pdict_train.get("num_grad_updates", None)
    if num_grad_updates:
        list_atoms = read(
            f"{work_dir}/{K.DIR_COLLECTDATA}/data_trainset.extxyz",
            format="extxyz",
            index=":",
        )
        dataset_size = len(list_atoms)
        batch_size = sevenn_args["data"]["batch_size"]
        num_epochs = suggest_num_epochs(dataset_size, batch_size, num_grad_updates)
        sevenn_args["train"]["epoch"] = num_epochs
        if sevenn_args["train"].get("scheduler", None) == "linearlr":
            sevenn_args["train"]["scheduler_param"]["total_iters"] = num_epochs

    ### Copy init_checkpoints to DIR_FWDATA
    init_checkpoints = natsorted(pdict_train.get("init_checkpoints", []))
    if init_checkpoints:
        _ = [
            copy_file(fi, f"{work_dir}/{K.DIR_FWDATA}/init_checkpoint_{i}.pth")
            for i, fi in enumerate(init_checkpoints)
        ]

    logger.info("Prepare train tasks")
    ### Prepare train tasks (one folder for each training model)
    num_models = pdict_train["num_models"]
    task_dirs = [None] * num_models
    for i in range(num_models):
        model_path = Path(f"{work_dir}/model_{i:{K.FMT_MODEL}}")
        make_dir(model_path, backup=False)
        ### Set more args privately for each model
        sevenn_args["train"]["random_seed"] = random.randrange(2**16)
        if (
            init_checkpoints and Path(f"{work_dir}/{K.DIR_FWDATA}/init_checkpoint_{i}.pth").exists()
        ):  # continue training
            tmp_dict = {
                "reset_optimizer": True,
                "reset_scheduler": True,
                "checkpoint": f"../{K.DIR_FWDATA}/init_checkpoint_{i}.pth",
                "reset_epoch": True,
            }
            sevenn_args["train"]["continue"] = tmp_dict

        write_yaml(sevenn_args, f"{model_path}/{K.FILE_ARG_TRAIN}")
        task_dirs[i] = model_path.as_posix()
    ### save task_dirs (relative to run_dir)
    write_yaml(task_dirs, f"{work_dir}/task_dirs.yml")

    ### Clean up
    Path(f"{work_dir}/{K.DIR_COLLECTDATA}/{K.FILE_COLLECT_DATA}").unlink()  # delete
    return


class OperAltrainSevennet(RemoteOperation):
    def __init__(self, work_dir, pdict, multi_mdict, mdict_prefix="train"):
        super().__init__(work_dir, pdict, multi_mdict, mdict_prefix)
        self.op_name = "Training"
        self.task_filter = {
            "has_files": [K.FILE_ARG_TRAIN],
            "no_files": ["checkpoint_best.pth"],
        }
        return

    def prepare(self):
        """Prepare for remote training operation.

        Includes:
        - Prepare the task_list
        - Prepare forward & backward files
        - Prepare commandlist_list for multi-remote submission
        """
        pdict = self.pdict
        ### Prepare forward & backward files
        self.forward_common_files = [K.DIR_FWDATA]
        self.forward_files = [K.FILE_ARG_TRAIN]  # all files in task_path
        self.backward_files = [
            "checkpoint_*.pth",  # "checkpoint_*.pth",  "checkpoint_best.pth"
            "log*.sevenn",
            "lc.csv",
        ]
        ### Prepare commandlist_list for multi-remote submission
        mdict_list = self.mdict_list
        commandlist_list = []
        for mdict in mdict_list:
            command_list = []
            train_command = mdict.get("command", "sevenn")
            if train_command == "sevenn":
                # train_command = f"{train_command} {FILE_ARG_TRAIN} --enable_cueq"
                train_command = f"{train_command} {K.FILE_ARG_TRAIN}"
                distributed_args = pdict["train"].get("distributed", None)
                if distributed_args:  ## run distributed training (MPI)
                    cluster_type = distributed_args.get("cluster_type", "slurm")  # SLURM or SGE
                    if cluster_type == "slurm":
                        gpu_per_node = mdict["resources"].get("gpu_per_node", 0)
                        command_list.extend(
                            [
                                "export WORLD_SIZE=$SLURM_NTASKS",
                                "export RANK=$SLURM_PROCID",
                                "export LOCAL_RANK=$SLURM_LOCALID",
                            ]
                        )
                        if distributed_args["distributed_backend"] == "nccl":
                            train_command = f"torchrun --standalone --nproc_per_node {gpu_per_node} --no_python {train_command} --distributed --distributed_backend='nccl'"

                    elif cluster_type == "sge":
                        gpu_per_node = distributed_args.get("gpu_per_node", 0)
                        if distributed_args["distributed_backend"] == "mpi":
                            train_command = f"mpirun -np $NSLOTS {train_command} --distributed --distributed_backend='mpi'"
                        elif distributed_args["distributed_backend"] == "nccl":
                            train_command = f"torchrun --standalone --nnodes $NSLOTS --nproc_per_node {gpu_per_node} --no_python {train_command} --distributed --distributed_backend='nccl'"
                        elif distributed_args["distributed_backend"] == "gloo":
                            # command_list.append("export WORLD_SIZE=$NSLOTS \nexport RANK=-1")
                            train_command = f"torchrun --standalone --nnodes $NSLOTS --nproc_per_node cpu --no_python {train_command} --distributed --distributed_backend='gloo'"
                    else:
                        command_list.extend(
                            [
                                "export WORLD_SIZE=$(DPDISPATCHER_NUMBER_NODE*DPDISPATCHER_CPU_PER_NODE)",
                                "export RANK=$SLURM_PROCID",
                                "export LOCAL_RANK=$SLURM_LOCALID",
                            ]
                        )
                        train_command = f"torchrun --standalone --nproc_per_node $DPDISPATCHER_GPU_PER_NODE --no_python {train_command} --distributed --distributed_backend='nccl'"
            command_list.append(train_command)
            commandlist_list.append(command_list)
        self.commandlist_list = commandlist_list
        return

    def postprocess(self):
        """Collect the best checkpoint files and save them in FILE_CHECKPOINTS."""
        work_dir = self.work_dir
        task_dirs = self.task_dirs

        ### find the latest checkpoint file
        best_checkpoint_files: list = [None] * len(task_dirs)
        for i, task_dir in enumerate(task_dirs):
            checkpoint_files = list_paths(task_dir, patterns=["checkpoint_*.pth"])
            checkpoint_files = natsorted(checkpoint_files)
            best_checkpoint_files[i] = checkpoint_files[-1]
            _ = [Path(f).unlink() for f in checkpoint_files[:-1]]  # remove old checkpoints

        write_yaml(best_checkpoint_files, f"{work_dir}/{K.FILE_CHECKPOINTS}")
        return


#####ANCHOR fine-tuning
### reuse pretrain_sevenn() and OperAltrainSevennet


#####ANCHOR Support functions
