"""Classes and functions for fine-tuning ML models."""

from alff.al.active_learning import _get_mlp_model
from alff.al.mlp.mlp_sevenn import OperAltrainSevennet, pretrain_sevenn
from alff.base import KEY as K
from alff.base import Workflow, logger
from alff.gdata.util_dataset import merge_extxyz_files
from thkit.io import write_yaml
from thkit.path import collect_files, make_dir_ask_backup


#####ANCHOR support functions
def stage_train(pdict, mdict):
    """Stage function for ML training tasks."""
    train_param = pdict["train"]

    ### Create work_dir folder
    work_dir = f"{K.DIR_TRAIN}"
    make_dir_ask_backup(work_dir, logger)

    logger.info("Collecting data files")
    #### Collect data files
    data_files = collect_files(
        train_param["init_data_paths"], patterns=["*.extxyz", "*.xyz"]
    )  # relative to run_dir
    data_files = list(set(data_files))  # remove duplicates
    assert len(data_files) > 0, "No data files found"
    write_yaml(data_files, f"{work_dir}/{K.FILE_DATAPATH}")

    ## Copy data files to tmp-folder: `copied_data/`
    merge_extxyz_files(
        extxyz_files=data_files, outfile=f"{work_dir}/{K.DIR_COLLECTDATA}/{K.FILE_COLLECT_DATA}"
    )

    ### Prepare train args
    mlp_model = _get_mlp_model(pdict)
    if mlp_model in ["sevenn", "sevenn_mliap"]:
        pretrain_sevenn(work_dir, pdict, mdict)
        op = OperAltrainSevennet(work_dir, pdict, mdict, mdict_prefix="train")
        op.prepare()
        op.run()
        op.postprocess()
    return


#####ANCHOR main loop
class WorkflowFinetune(Workflow):
    """Workflow for fine-tuning the existed ML models or train a new ML model.
    Needs to override `self.stage_list` in base class, because the stages are fixed here.
    """

    def __init__(self, params_file: str, machines_file: str):
        super().__init__(params_file, machines_file, K.SCHEMA_FINETUNE)
        self.stage_map = {
            "ml_train": stage_train,
        }
        self.wf_name = "FINE-TUNING"
        self.stage_list = ["ml_train"]  # override the stage_list
        return
