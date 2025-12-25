"""Base classes for ALFF workflows and remote operations."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

if TYPE_CHECKING:
    from collections.abc import Callable

import asyncio
import time
from abc import ABC, abstractmethod
from pathlib import Path

from alff import ALFF_ROOT
from alff.util.tool import alff_info_shorttext, alff_info_text
from thkit.config import Config
from thkit.io import read_yaml
from thkit.jobman import (
    ConfigRemoteMachines,
    alff_submit_job_multi_remotes,
    change_logfile_dispatcher,
)
from thkit.log import ColorLogger, create_logger
from thkit.markup import TextDecor
from thkit.path import filter_dirs


#####ANCHOR Baseclass for workflow
class Workflow(ABC):
    """Base class for workflows.

    `Workflow` class is the central part of ALFF. Each workflow contains list of stages to be executed.

    Subclass MUST reimplement:
        - `__init__()`: initialize the workflow, need to override these attributes:
            - self.stage_map
            - self.wf_name
        - `run()`: the main function to run the workflow. The default implementation is a loop over stages in `self.stage_map`, just for simple workflow. For complex workflow (e.g. with iteration like active learning), need to reimplement the `.run()` function.

    Example:
    ```python
    class WorkflowExample(Workflow):
        def __init__(self, params_file: str, machines_file: str):
            super().__init__(params_file, machines_file, SCHEMA_EXAMPLE)
            self.stage_map = {
                "stage_name1": stage_function1,
                "stage_name2": stage_function2,
                "stage_name3": stage_function3,
            }
            self.wf_name = "Name of the workflow"
            return
    ```

    Notes:
        - `multi_mdicts` in this class is a dictionary containing multiple remote machines, and will be used `RemoteOperation` class.
        - All `@abtractmethod` must be reimplemented in subclasses.
    """

    def __init__(
        self,
        params_file: str,
        machines_file: str,
        schema_file: str | None = None,
    ):
        self.params_file = params_file
        self.machines_file = machines_file
        self.schema_file = schema_file
        ### Machines config
        config_machine = ConfigRemoteMachines(self.machines_file)
        config_machine.check_connection()
        self.multi_mdicts = config_machine.multi_mdicts
        ### Params config
        self._validate_params_config()
        self.pdict = Config.loadconfig(self.params_file)
        self.stage_list = self._load_stage_list()

        ### Need to define in 'subclass.__init__()'
        self.stage_map: dict[str, Callable]
        self.wf_name: str
        return

    def run(self):
        """The main function to run the workflow. This default implementation works for simple workflow,
        for more complex workflow (e.g. with iteration like active learning), need to reimplement this `.run()` function.
        """
        self._print_intro()
        stage_map = self.stage_map
        stage_list = self.stage_list
        ### main loop
        for i, (stage_name, stage_func) in enumerate(stage_map.items()):
            if stage_name in stage_list:
                logtext = f" stage_{i:{KEY.FMT_STAGE}}: {stage_name} "
                logger.info(TextDecor(logtext).fill_left(margin=20, length=52))
                stage_func(self.pdict, self.multi_mdicts)

        self._print_outro()
        return

    def _load_stage_list(self):
        stage_list = self.pdict.get("stages", [])
        return stage_list

    def _validate_params_config(self):
        """Validate the params config file."""
        Config.validate(config_file=self.params_file, schema_file=self.schema_file)
        return

    def _update_config(self):
        pdict = self.pdict or {}
        multi_mdicts = self.multi_mdicts or {}
        pdict.update(Config.loadconfig(self.params_file))
        multi_mdicts.update(Config.loadconfig(self.machines_file))
        self.pdict = pdict
        self.multi_mdicts = multi_mdicts
        return

    def _print_intro(self):
        print(TextDecor(alff_info_shorttext()).mkcolor("blue"))
        logger.info(f"Start {self.wf_name}")
        logger.info(f"Logfile: {KEY.FILE_LOG_ALFF}")
        return

    def _print_outro(self):
        logger.info("FINISHED !")
        return


#####ANCHOR Baseclass for remote operations
class RemoteOperation(ABC):
    """Base class for operations on remote machines.

    Each `operation` includes atl east 3 methods:
        - prepare
        - run
        - postprocess

    Subclass must reimplement these methods:
        - `__init__()`: initialize the operation, need to override these attributes:
        - `prepare()`: prepare all things needed for the run() method.
        - `postprocess()`: postprocess after the run() method.

    Notes:
        - Before using this class, must prepare a file `work_dir/task_dirs.yml`
        - All paths (`work_dir`, `task_dirs`,...) are in POSIX format, and relative to `run_dir` (not `work_dir`).
        - All `@abtractmethod` must be reimplemented in subclasses.
        - Do not change the `.run()` method unless you know what you are doing.
        - `task_filter` to filter task directories (filter already labelled structures).
        ```python
        self.task_filter = {"has_files": ["file1.txt", "file2.txt"], "no_files": ["file3.txt"]}
        ```
    """

    def __init__(self, work_dir, pdict, multi_mdicts, mdict_prefix=""):
        ### Do not change this part
        self.work_dir = work_dir
        self.pdict = pdict
        self.mdict_list = self._select_machines(multi_mdicts, mdict_prefix)
        self.task_dirs = self._load_task_dirs()

        ### Need to reimplement in subclass.__init__()
        self.op_name: str
        self.task_filter: dict[str, list[str]]
        ### These attributes will be set in `prepare()` method
        self.commandlist_list: list[list[str]]
        self.forward_files: list[str]
        self.backward_files: list[str]
        self.forward_common_files: list[str]
        self.backward_common_files: list[str] = []  # rarely used
        return

    @abstractmethod
    def prepare(self):
        """Prepare all things needed for `run()` method.

        This method need to implement the following attributes:
            - self.commandlist_list: list[list[str]]
            - self.forward_files: list[str]
            - self.backward_files: list[str]
            - self.forward_common_files: list[str]
            - self.backward_common_files: list[str]  # rarely used
        """
        pass

    @abstractmethod
    def postprocess(self) -> None | list:
        """Postprocess after `run()` method."""
        pass

    def run(self):
        """Function to submit jobs to remote machines.

        Note:
            - Orginal `taks_dirs` is relative to `run_dir`, and should not be changed. But the sumbmission function needs `taks_dirs` relative path to `work_dir`, so we make temporary change here.
        """
        logger.info(f"Run remote operation: '{self.op_name}'")

        task_dirs_need_run = self._filter_task_dirs()
        if len(task_dirs_need_run) == 0:
            logger.warning("No tasks found for remote jobs.")
            return
        else:
            logger.info(
                f"Select {len(task_dirs_need_run)}/{len(self.task_dirs)} tasks for remote run."
            )
        rel_task_dirs = [Path(p).relative_to(self.work_dir).as_posix() for p in task_dirs_need_run]

        ### Submit jobs
        asyncio.run(
            alff_submit_job_multi_remotes(
                mdict_list=self.mdict_list,
                commandlist_list=self.commandlist_list,
                work_dir=self.work_dir,
                task_dirs=rel_task_dirs,
                forward_files=self.forward_files,
                backward_files=self.backward_files,
                forward_common_files=self.forward_common_files,
                backward_common_files=self.forward_common_files,
                logger=logger,
            )
        )
        return

    def _load_task_dirs(self) -> list[str]:
        """Load task directories from `work_dir/task_dirs.yml`."""
        task_dirs_file = Path(self.work_dir) / "task_dirs.yml"
        if not task_dirs_file.exists():
            raise FileNotFoundError(f"File {task_dirs_file} not found. Please prepare it first.")
        task_dirs = read_yaml(task_dirs_file)
        return task_dirs

    def _select_machines(self, multi_mdicts: dict, mdict_prefix: str) -> list[dict]:
        ### Refer method `ConfigRemoteMachines.select_machines()`
        """Select machine dicts based on the prefix."""
        mdict_list = [v for k, v in multi_mdicts.items() if k.startswith(mdict_prefix)]
        if len(mdict_list) < 1:
            raise ValueError(f"No machine configs found with prefix: '{mdict_prefix}'")
        return mdict_list

    def _filter_task_dirs(self) -> list[str]:
        """Function to filter already run structures."""
        task_dirs_need_run = filter_dirs(
            self.task_dirs,
            has_files=self.task_filter["has_files"],
            no_files=self.task_filter["no_files"],
        )
        return task_dirs_need_run


#####ANCHOR Support classes/functions
class KEY:
    """A class to hold various constant keys used throughout the ALFF package."""

    #####ANCHOR logging
    time_str = time.strftime("%y%m%d_%H%M%S")  # "%y%b%d" "%Y%m%d"
    DIR_LOG = "log"
    FILE_LOG_ALFF = f"{DIR_LOG}/{time_str}_alff.log"
    # FILE_LOG_DISPATCH = FILE_LOG_ALFF  # FILE_LOG_ALFF.replace("alff", "dispatch")
    FILE_ITERLOG = "_alff.iter"

    ## Some keys are used in multiple processes, so they are defined here for consistency and easy modification.
    #####ANCHOR Keys for active learning
    ### folder names
    DIR_TRAIN = "00_train"
    DIR_MD = "01_md"
    DIR_DFT = "02_dft"
    DIR_DATA = "03_data"
    DIR_TMP = "tmp_dir"
    DIR_CANDIDATE = "md_selected"
    DIR_COLLECTDATA = "collect_data"
    DIR_FWDATA = "fw_data"

    FILE_DATAPATH = "data_paths.yml"
    FILE_CHECKPOINTS = "checkpoints.yml"
    FILE_ARG_TRAIN = "arg_train.yml"

    FILE_TRAJ_MD = "traj_md.extxyz"  # trajectory by MD, no label
    FILE_TRAJ_MD_CANDIDATE = FILE_TRAJ_MD.replace(".extxyz", "_candidate.extxyz")

    FILE_ITER_DATA = "label_data.extxyz"
    FILE_COLLECT_DATA = "collect_label_data.extxyz"

    ### format
    FMT_ITER = "04d"
    FMT_STAGE = "02d"
    FMT_MODEL = "02d"
    FMT_STRUCT = "05d"
    FMT_TASK_MD = "06d"
    FMT_TASK_DFT = "06d"

    ### templates/schema
    RUNFILE_LAMMPS = "cli_lammps.lmp"
    FILE_ARG_LAMMPS = "arg_lammps.yml"
    FILE_ARG_ASE = "arg_ase.yml"

    SCRIPT_ASE_PATH = f"{ALFF_ROOT}/util/script_ase"
    SCHEMA_ASE_RUN = f"{ALFF_ROOT}/util/script_ase/schema_ase_run.yml"
    SCHEMA_LAMMPS = f"{ALFF_ROOT}/util/script_lammps/schema_lammps.yml"

    SCHEMA_ACTIVE_LEARN = f"{ALFF_ROOT}/al/schema_active_learn.yml"
    SCHEMA_FINETUNE = f"{ALFF_ROOT}/al/schema_finetune.yml"

    #####ANCHOR keys for data_generation
    ### folder names
    DIR_MAKE_STRUCT = "00_make_structure"
    DIR_STRAIN = "01_strain"
    DIR_GENDATA = "02_gendata"

    FILE_FRAME_UNLABEL = "conf.extxyz"
    FILE_FRAME_LABEL = "conf_label.extxyz"
    FILE_TRAJ_LABEL = "traj_label.extxyz"  # trajectory by DFT aimd, with label

    ### templates/schema
    SCHEMA_ASE_BUILD = f"{ALFF_ROOT}/util/script_ase/schema_ase_build.yml"
    SCHEMA_GENDATA = f"{ALFF_ROOT}/gdata/schema_gendata.yml"
    SCHEMA_PHONON = f"{ALFF_ROOT}/phonon/schema_phonon.yml"
    SCHEMA_ELASTIC = f"{ALFF_ROOT}/elastic/schema_elastic.yml"
    SCHEMA_PES_SCAN = f"{ALFF_ROOT}/pes/schema_pes_scan.yml"

    #####ANCHOR keys for phonon calculation
    DIR_SUPERCELL = "01_supercell"
    DIR_PHONON = "02_phonon"
    FILE_PHONOPYwFORCES = "phonopy_with_forces.yml"

    #####ANCHOR keys for elastic calculation
    DIR_ELASTIC = "02_elastic"

    #####ANCHOR keys for pes_scan
    DIR_SCAN = "01_scan"
    DIR_PES = "02_pes"
    ######################## END KEY ########################


#####ANCHOR Global logger object
### Create a lazy global logger for importing in other modules. This is to avoid initialization of logger at import time,
_logger = None


def init_alff_logger() -> ColorLogger:
    """Initializing the logger."""
    logfile = KEY.FILE_LOG_ALFF
    if not Path(logfile).parent.exists():
        Path(logfile).parent.mkdir(parents=True, exist_ok=True)

    with open(logfile, "a") as f:
        f.write(alff_info_text())  # print info to logfile

    logger = create_logger("alff", logfile=logfile)
    change_logfile_dispatcher(logfile)
    return logger


def get_logger():
    global _logger
    if _logger is None:  # lazy init only on first use
        _logger = init_alff_logger()
    return _logger


### Proxy logger object for direct import
class _LoggerProxy:
    def __getattr__(self, name):
        return getattr(get_logger(), name)


logger = cast(ColorLogger, _LoggerProxy())  # <--- this is what other modules import
