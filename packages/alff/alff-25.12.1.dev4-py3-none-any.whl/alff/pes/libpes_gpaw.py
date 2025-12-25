"""Library for GPAW-based PES operations."""

from copy import deepcopy

from alff.base import KEY as K
from alff.base import logger
from alff.gdata.libgen_gpaw import OperGendataGpawOptimize
from thkit.config import Config
from thkit.io import read_yaml, write_yaml


#####ANCHOR Stage 1 - GPAW optimize initial structure
class OperPESGpawOptimize(OperGendataGpawOptimize):
    """This class does GPAW optimization for a list of structures in `task_dirs`.

    This class can also be used for phonon GPAW optimization
    """

    def __init__(self, work_dir, pdict, multi_mdict, mdict_prefix="gpaw"):
        super().__init__(work_dir, pdict, multi_mdict, mdict_prefix)
        return

    def prepare(self):
        ### Refer functions from `libgen_gpaw.py`
        """Prepare the operation.

        Includes:
        - Prepare ase_args for GPAW and gpaw_run_file. Note: Must define `pdict.dft.calc_args.gpaw{}` for this function.
        - Prepare the task_list
        - Prepare forward & backward files
        - Prepare commandlist_list for multi-remote submission
        """
        work_dir = self.work_dir
        pdict = self.pdict

        ### Prepare ase_args
        ase_args = {}
        ase_args.setdefault("structure", {})["from_extxyz"] = f"{K.FILE_FRAME_UNLABEL}"
        ase_args["calc_args"] = deepcopy(pdict["calculator"].get("calc_args", {}))
        ase_args["optimize"] = pdict.get("optimize_args", {}).get("gpaw", {})
        Config.validate(config_dict=ase_args, schema_file=K.SCHEMA_ASE_RUN)
        write_yaml(ase_args, f"{work_dir}/{K.FILE_ARG_ASE}")

        ### GPAW_runfile
        self.RUNFILE_GPAW = "cli_gpaw_optimize.py"
        self._prepare_runfile_gpaw()
        return

    def postprocess(self):
        ### Do nothing
        return


#####ANCHOR Stage 4 - compute energy by DFT/MD
class OperPESGpawOptimizeFixatom(OperPESGpawOptimize):
    """Perform optimization with some atoms fixed."""

    def __init__(self, work_dir, pdict, multi_mdict, mdict_prefix="gpaw"):
        super().__init__(work_dir, pdict, multi_mdict, mdict_prefix)
        self.op_name = "GPAW optimize fixed atoms"
        return

    def prepare(self):
        work_dir = self.work_dir
        pdict = self.pdict

        ### Prepare ase_args
        ase_args = {}
        ase_args.setdefault("structure", {})["from_extxyz"] = f"{K.FILE_FRAME_UNLABEL}"
        ase_args["calc_args"] = deepcopy(pdict["calculator"].get("calc_args", {}))
        ase_args["optimize"] = pdict["optimize_args"].get("gpaw", {})
        ### Read fixed atoms
        fixed_atoms = read_yaml(f"{work_dir}/fix_idxs.yml")
        ase_args.setdefault("constraint", {})["fix_atoms"] = {}
        ase_args["constraint"]["fix_atoms"]["fix_idxs"] = fixed_atoms
        if pdict.get("constraint", {}).get("fix_atoms", {}).get("fix_only_z", False):
            ase_args["constraint"]["fix_atoms"]["fix_only_z"] = True
            logger.info("Only fix atom positions in z-direction.")
        else:
            logger.info("Fix atom positions in all directions.")

        Config.validate(config_dict=ase_args, schema_file=K.SCHEMA_ASE_RUN)
        write_yaml(ase_args, f"{work_dir}/{K.FILE_ARG_ASE}")

        ### GPAW_runfile
        self.RUNFILE_GPAW = "cli_gpaw_optimize.py"
        self._prepare_runfile_gpaw()
        return
