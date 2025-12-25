from copy import deepcopy

# from pathlib import Path
from alff.base import KEY as K
from alff.base import RemoteOperation
from alff.gdata.util_dataset import remove_key_in_extxyz
from thkit.config import Config
from thkit.io import write_yaml
from thkit.path import collect_files, copy_file, filter_dirs, remove_files_in_paths

"""Note:
- work_dir is a folder relative to the run_dir
- task_dirs are folders relative to the work_dir
"""


#####SECTION Classes for GPAW data generation
#####ANCHOR Stage 1 - GPAW optimize initial structure
class OperGendataGpawOptimize(RemoteOperation):
    """This class does GPAW optimization for a list of structures in `task_dirs`."""

    def __init__(self, work_dir, pdict, multi_mdict, mdict_prefix="gpaw"):
        super().__init__(work_dir, pdict, multi_mdict, mdict_prefix)
        # self.calc_name = "gpaw"
        self.op_name = "GPAW optimize"
        self.task_filter = {
            "has_files": [K.FILE_FRAME_UNLABEL],
            "no_files": [K.FILE_FRAME_LABEL],
        }
        return

    def prepare(self):
        """Prepare the operation.

        Includes:
        - Prepare ase_args for GPAW and gpaw_run_file. Note: Must define `pdict.dft.calc_args.gpaw{}` for this function.
        - Prepare the task_list
        - Prepare forward & backward files
        - Prepare commandlist_list for multi-remote submission
        """
        work_dir = self.work_dir
        pdict = self.pdict

        # calc_args = self.calc_info["calc_args"]
        # optimize_args = self.calc_info["optimize_args"]

        ### Prepare ase_args
        ase_args = deepcopy(pdict.get("dft"))
        ase_args.pop("md", None)  # remove the MD key
        ase_args.setdefault("structure", {})["from_extxyz"] = f"{K.FILE_FRAME_UNLABEL}"
        # for p in dft_task_dirs:
        #     write_yaml(ase_args, f"{p}/{FILE_ARG_ASE}")
        Config.validate(config_dict=ase_args, schema_file=K.SCHEMA_ASE_RUN)
        write_yaml(ase_args, f"{work_dir}/{K.FILE_ARG_ASE}")

        ### GPAW_runfile
        self.RUNFILE_GPAW = "cli_gpaw_optimize.py"
        self._prepare_runfile_gpaw()
        return

    def _prepare_runfile_gpaw(self):
        work_dir = self.work_dir
        ### GPAW_runfile
        RUNFILE_GPAW = self.RUNFILE_GPAW
        _ = copy_file(
            f"{K.SCRIPT_ASE_PATH}/{RUNFILE_GPAW}",
            f"{work_dir}/{RUNFILE_GPAW}",
        )

        ### Prepare forward & backward files
        self.forward_common_files = [RUNFILE_GPAW, K.FILE_ARG_ASE]  # in work_dir
        self.forward_files = [K.FILE_FRAME_UNLABEL]  # files in task_path
        self.backward_files = [K.FILE_FRAME_LABEL, "calc*.txt"]

        ### Prepare commandlist_list for multi-remote submission
        mdict_list = self.mdict_list
        commandlist_list = []
        for mdict in mdict_list:
            command_list = []
            dft_cmd = mdict.get("command", "gpaw python")
            dft_cmd = f"{dft_cmd} ../{RUNFILE_GPAW} ../{K.FILE_ARG_ASE}"  # `../` to run file in common directory
            command_list.append(dft_cmd)
            commandlist_list.append(command_list)
        self.commandlist_list = commandlist_list
        return

    def postprocess(self):
        """This function does:
        - Remove unlabeled .extxyz files, just keep the labeled ones.
        """
        task_dirs = self.task_dirs
        ### Remove unlabeled extxyz files
        unlabel_paths = filter_dirs(task_dirs, has_files=[K.FILE_FRAME_UNLABEL, K.FILE_FRAME_LABEL])
        remove_files_in_paths(files=[K.FILE_FRAME_UNLABEL], paths=unlabel_paths)
        ### Remove unwanted keys in extxyz files
        extxyz_dirs = filter_dirs(task_dirs, has_files=[K.FILE_FRAME_LABEL])
        extxyz_files = [f"{d}/{K.FILE_FRAME_LABEL}" for d in extxyz_dirs]
        _ = [
            remove_key_in_extxyz(f, ["free_energy", "magmom", "magmoms", "dipole", "momenta"])
            for f in extxyz_files
        ]
        return


#####ANCHOR Stage 3 - run DFT singlepoint
class OperGendataGpawSinglepoint(OperGendataGpawOptimize):
    def __init__(self, work_dir, pdict, multi_mdict, mdict_prefix="gpaw"):
        super().__init__(work_dir, pdict, multi_mdict, mdict_prefix)
        self.op_name = "GPAW singlepoint"
        return

    def prepare(self):
        work_dir = self.work_dir
        pdict = self.pdict

        ### Prepare ase_args
        ase_args = deepcopy(pdict.get("dft"))
        ase_args.pop("md", None)  # remove the MD key
        ase_args.setdefault("structure", {})["from_extxyz"] = f"{K.FILE_FRAME_UNLABEL}"
        write_yaml(ase_args, f"{work_dir}/{K.FILE_ARG_ASE}")
        Config.validate(config_dict=ase_args, schema_file=K.SCHEMA_ASE_RUN)

        ### GPAW_runfile
        self.RUNFILE_GPAW = "cli_gpaw_singlepoint.py"
        self._prepare_runfile_gpaw()
        return


#####ANCHOR Stage 3 - run AIMD
class OperGendataGpawAIMD(RemoteOperation):
    """See class OperGendataGpawOptimize for more details."""

    def __init__(self, work_dir, pdict, multi_mdict, mdict_prefix="gpaw"):
        super().__init__(work_dir, pdict, multi_mdict, mdict_prefix)
        self.op_name = "GPAW aimd"
        self.task_filter = {
            "has_files": [K.FILE_FRAME_UNLABEL],
            "no_files": [K.FILE_TRAJ_LABEL],
        }
        return

    def prepare(self):
        """Refer to the `pregen_gpaw_optimize()` function.

        Note:
        - This function differs from `OperGendataGpawOptimize.prepare()` in the aspects that `ase_args` now in `task_dirs` (not in `work_dir`). So, the forward files and commandlist_list are different.
        - structure_dirs: contains the optimized structures without scaling.
        - strain_structure_dirs: contains the scaled structures.

        """
        ### GPAW_runfile
        self.RUNFILE_GPAW = "cli_gpaw_aimd.py"
        self._prepare_runfile_gpaw()
        return

    def _prepare_runfile_gpaw(self):
        work_dir = self.work_dir
        ### GPAW_runfile
        RUNFILE_GPAW = self.RUNFILE_GPAW
        _ = copy_file(
            f"{K.SCRIPT_ASE_PATH}/{RUNFILE_GPAW}",
            f"{work_dir}/{RUNFILE_GPAW}",
        )

        ### Prepare forward & backward files
        self.forward_common_files = [RUNFILE_GPAW]  # in work_dir
        self.forward_files = [K.FILE_FRAME_UNLABEL, K.FILE_ARG_ASE]  # files in task_path
        self.backward_files = [K.FILE_TRAJ_LABEL, "calc*.txt"]

        ### Prepare commandlist_list for multi-remote submission
        mdict_list = self.mdict_list
        commandlist_list = []
        for mdict in mdict_list:
            command_list = []
            dft_cmd = mdict.get("command", "python")
            dft_cmd = f"{dft_cmd} ../{RUNFILE_GPAW} {K.FILE_ARG_ASE}"  # `../` to run file in common directory
            command_list.append(dft_cmd)
            commandlist_list.append(command_list)
        self.commandlist_list = commandlist_list
        return

    def postprocess(self):
        """Refer to the `postgen_gpaw_optimize()` function."""
        task_dirs = self.task_dirs
        ### Remove unlabeled extxyz files
        # unwant_files = collect_files(task_dirs, patterns=[K.FILE_FRAME_UNLABEL])
        # _ = [Path(f).unlink() for f in unwant_files]
        ### Remove unwanted keys in extxyz files
        extxyz_files = collect_files(task_dirs, patterns=[K.FILE_TRAJ_LABEL])
        _ = [
            remove_key_in_extxyz(f, ["free_energy", "magmom", "magmoms", "dipole", "momenta"])
            for f in extxyz_files
        ]
        return


#####SECTION Classes for GPAW active learning
class OperAlGpawSinglepoint(OperGendataGpawOptimize):
    def __init__(self, work_dir, pdict, multi_mdict, mdict_prefix="gpaw"):
        super().__init__(work_dir, pdict, multi_mdict, mdict_prefix)
        self.op_name = "GPAW singlepoint"
        return

    def prepare(self):
        work_dir = self.work_dir
        pdict = self.pdict

        ### Prepare ase_args
        ase_args = deepcopy(pdict.get("dft"))
        ase_args.pop("md", None)  # remove the MD key
        ase_args.setdefault("structure", {})["from_extxyz"] = f"{K.FILE_FRAME_UNLABEL}"
        write_yaml(ase_args, f"{work_dir}/{K.FILE_ARG_ASE}")
        Config.validate(config_dict=ase_args, schema_file=K.SCHEMA_ASE_RUN)

        ### GPAW_runfile
        self.RUNFILE_GPAW = "cli_gpaw_singlepoint.py"
        self._prepare_runfile_gpaw()
        return

    def postprocess(self):
        """Do post DFT tasks."""
        ### Ref collect data in gendata
        # Nothing to do here
        return
