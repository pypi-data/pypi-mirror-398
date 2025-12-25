"""Library for GPAW-based phonon calculations."""

from copy import deepcopy

from alff.base import KEY as K
from alff.pes.libpes_gpaw import OperPESGpawOptimize
from asext.io.readwrite import read_extxyz
from thkit.config import Config
from thkit.io import write_yaml
from thkit.path import filter_dirs, remove_files_in_paths


#####ANCHOR Stage 1 - GPAW optimize initial structure
class OperPhononGpawOptimize(OperPESGpawOptimize):
    ### Can use the same class as OperPESGpawOptimize.
    def __init__(self, work_dir, pdict, multi_mdict, mdict_prefix="gpaw"):
        super().__init__(work_dir, pdict, multi_mdict, mdict_prefix)
        return

    def prepare(self):
        work_dir = self.work_dir
        pdict = self.pdict

        ### Prepare ase_args
        ase_args = {}
        ase_args.setdefault("structure", {})["from_extxyz"] = f"{K.FILE_FRAME_UNLABEL}"
        ase_args["calc_args"] = deepcopy(pdict["calculator"].get("calc_args", {}))
        ase_args["optimize"] = pdict["optimize_args"].get("gpaw", {})
        ### Set constraint if any
        if "constraint" in pdict:
            ase_args["constraint"] = pdict.get("constraint")

        Config.validate(config_dict=ase_args, schema_file=K.SCHEMA_ASE_RUN)
        write_yaml(ase_args, f"{work_dir}/{K.FILE_ARG_ASE}")

        ### GPAW_runfile
        self.RUNFILE_GPAW = "cli_gpaw_optimize.py"
        self._prepare_runfile_gpaw()
        return


#####ANCHOR Stage 3 - scale and relax
class OperPhononGpawOptimizeFixbox(OperPESGpawOptimize):
    """Only need to redefine the prepare() method, to fix box during optimization."""

    def __init__(self, work_dir, pdict, multi_mdict, mdict_prefix="gpaw"):
        super().__init__(work_dir, pdict, multi_mdict, mdict_prefix)
        self.op_name = "GPAW optimize fixed box"
        return

    def prepare(self):
        work_dir = self.work_dir
        pdict = self.pdict

        ### Prepare ase_args
        ase_args = {}
        ase_args.setdefault("structure", {})["from_extxyz"] = f"{K.FILE_FRAME_UNLABEL}"
        ase_args["calc_args"] = deepcopy(pdict["calculator"].get("calc_args", {}))
        ase_args["optimize"] = pdict["optimize_args"].get("gpaw", {})
        ase_args["optimize"]["mask"] = [0, 0, 0, 0, 0, 0]
        ### Set constraint if any
        if "constraint" in pdict:
            ase_args["constraint"] = pdict.get("constraint")

        Config.validate(config_dict=ase_args, schema_file=K.SCHEMA_ASE_RUN)
        write_yaml(ase_args, f"{work_dir}/{K.FILE_ARG_ASE}")

        ### GPAW_runfile
        self.RUNFILE_GPAW = "cli_gpaw_optimize.py"
        self._prepare_runfile_gpaw()
        return


#####ANCHOR Stage 4 - run DFT singlepoint on supercell
class OperPhononGpawSinglepoint(OperPESGpawOptimize):
    """Need to redefine the prepare() and postprocess() methods."""

    def __init__(self, work_dir, pdict, multi_mdict, mdict_prefix="gpaw"):
        super().__init__(work_dir, pdict, multi_mdict, mdict_prefix)
        self.op_name = "GPAW Singlepoint"
        return

    def prepare(self):
        work_dir = self.work_dir
        pdict = self.pdict

        ### Prepare ase_args
        ase_args = {}
        ase_args.setdefault("structure", {})["from_extxyz"] = f"{K.FILE_FRAME_UNLABEL}"
        ase_args["calc_args"] = deepcopy(pdict["calculator"].get("calc_args", {}))
        Config.validate(config_dict=ase_args, schema_file=K.SCHEMA_ASE_RUN)
        write_yaml(ase_args, f"{work_dir}/{K.FILE_ARG_ASE}")

        ### GPAW_runfile
        self.RUNFILE_GPAW = "cli_gpaw_singlepoint.py"
        self._prepare_runfile_gpaw()
        return

    def postprocess(self) -> list[list]:  # type: ignore
        """Postprocess the operation.

        Includes:
        - Clean up unlabelled extxyz files
        - Collect forces from the output files
        """
        task_dirs = self.task_dirs
        ### Remove unlabeled extxyz files
        unlabel_dirs = filter_dirs(task_dirs, has_files=[K.FILE_FRAME_UNLABEL, K.FILE_FRAME_LABEL])
        remove_files_in_paths(files=[K.FILE_FRAME_UNLABEL], paths=unlabel_dirs)

        ### Collect forces to list_of_forces
        labeled_dirs = filter_dirs(task_dirs, has_files=[K.FILE_FRAME_LABEL])
        set_of_forces = []
        for d in labeled_dirs:
            list_atoms = read_extxyz(f"{d}/{K.FILE_FRAME_LABEL}")
            forces = [atoms.calc.results["forces"].tolist() for atoms in list_atoms]  # type: ignore
            set_of_forces.extend(forces)
        return set_of_forces
