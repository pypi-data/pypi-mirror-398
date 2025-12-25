"""Library for LAMMPS-based phonon calculations."""

from copy import deepcopy
from pathlib import Path

from alff.base import KEY as K
from alff.pes.libpes_lammps import OperPESLammpsOptimize
from alff.util.script_lammps.lammps_code_creator import (
    generate_script_lammps_minimize,
    generate_script_lammps_singlepoint,
    process_lammps_argdict,
)
from asext.io.readwrite import extxyz2lmpdata, lmpdump2extxyz, read_extxyz
from thkit.config import Config
from thkit.io import write_yaml
from thkit.path import filter_dirs, remove_files_in_paths

"""
Notes:
- use `deepcopy` to avoid changing the original dict.
"""


#####ANCHOR Stage 1 - LAMMPS optimize initial structure
class OperPhononLammpsOptimize(OperPESLammpsOptimize):
    ### Can use the same class as OperPESLammpsOptimize.
    ### Notes: Phonon caclulation does not need stress tensor.
    def __init__(self, work_dir, pdict, multi_mdict, mdict_prefix="lammps"):
        super().__init__(work_dir, pdict, multi_mdict, mdict_prefix)
        return


#####ANCHOR Stage 3 - scale and relax
class OperPhononLammpsOptimizeFixbox(OperPESLammpsOptimize):
    """Only need to redefine the prepare() method, to fix box during optimization."""

    def __init__(self, work_dir, pdict, multi_mdict, mdict_prefix="lammps"):
        super().__init__(work_dir, pdict, multi_mdict, mdict_prefix)
        self.op_name = "LAMMPS optimize fixed box"
        return

    def prepare(self):
        """This function does:
        - Prepare lammps_optimize and lammps_input files.
            - Convert extxyz to lmpdata.
            - Copy potential file to work_dir.

        - Prepare the task_list
        - Prepare forward & backward files
        - Prepare commandlist_list for multi-remote submission
        """
        calc_args = self.pdict["calculator"]["calc_args"]["lammps"]
        optimize_args = self.pdict["optimize_args"]["lammps"]

        ### Prepare lammps_arg for MS fixbox
        lammps_args = {}
        lammps_args["optimize"] = optimize_args
        lammps_args["optimize"].pop("press", None)  # remove press for fixed cell
        lammps_args["structure"] = deepcopy(calc_args)
        origin_pair_coeff_list = deepcopy(lammps_args["structure"].get("pair_coeff", []))

        ### Convert EXTXYZ to LAMMPS data file
        task_dirs = self.task_dirs
        for tdir in task_dirs:
            if Path(f"{tdir}/{K.FILE_FRAME_LABEL}").is_file():
                continue  # this structure is already labeled, skip it

            lmpdata_name = K.FILE_FRAME_UNLABEL.replace(".extxyz", ".lmpdata")
            lammps_args["structure"]["read_data"] = lmpdata_name
            atom_names, pbc = extxyz2lmpdata(
                extxyz_file=f"{tdir}/{K.FILE_FRAME_UNLABEL}",
                lmpdata_file=f"{tdir}/{lmpdata_name}",
                atom_style="atomic",
            )
            lammps_args["structure"]["pbc"] = pbc
            ### Auto assign atom_names in pair_coeff
            auto_atom_names = calc_args.get("auto_atom_names", False)
            if auto_atom_names:
                pair_coeff_list = [
                    f"{line} {' '.join(atom_names)}" for line in origin_pair_coeff_list
                ]
                lammps_args["structure"]["pair_coeff"] = pair_coeff_list

            lammps_args["extra"] = {"output_script": f"{tdir}/{K.RUNFILE_LAMMPS}"}
            Config.validate(config_dict=lammps_args, schema_file=K.SCHEMA_LAMMPS)
            write_yaml(lammps_args, f"{tdir}/{K.FILE_ARG_LAMMPS}")
            tmp_lammps_args = process_lammps_argdict(lammps_args)
            generate_script_lammps_minimize(**tmp_lammps_args)

        ### Copy runfile
        self._prepare_runfile_lammps()
        return


#####ANCHOR Stage 4 - run MD singlepoint on supercell
class OperPhononLammpsSinglepoint(OperPESLammpsOptimize):
    """Class to run LAMMPS singlepoint calculation, used for phonon calculation.
    Notes: the .postprocess() method returns `set_of_forces`, a 3D array.
    """

    def __init__(self, work_dir, pdict, multi_mdict, mdict_prefix="lammps"):
        super().__init__(work_dir, pdict, multi_mdict, mdict_prefix)
        self.op_name = "LAMMPS optimize"
        self.task_filter = {
            "has_files": [K.FILE_FRAME_UNLABEL],
            "no_files": ["frame_label.lmpdump"],
        }
        return

    def prepare(self):
        """This function does:
        - Prepare lammps_optimize and lammps_input files.
            - Convert extxyz to lmpdata.
            - Copy potential file to work_dir.

        - Prepare the task_list
        - Prepare forward & backward files
        - Prepare commandlist_list for multi-remote submission
        """
        calc_args = self.pdict["calculator"]["calc_args"]["lammps"]
        # optimize_args = self.pdict["optimize_args"]["lammps"]

        ### Prepare lammps_arg for MS simulation
        lammps_args = {}
        lammps_args["structure"] = deepcopy(calc_args)
        origin_pair_coeff_list = deepcopy(lammps_args["structure"].get("pair_coeff", []))

        ### Convert EXTXYZ to LAMMPS data file
        task_dirs = self.task_dirs
        for tdir in task_dirs:
            if Path(f"{tdir}/{K.FILE_FRAME_LABEL}").is_file():
                continue  # this structure is already labeled, skip it

            lmpdata_name = K.FILE_FRAME_UNLABEL.replace(".extxyz", ".lmpdata")
            lammps_args["structure"]["read_data"] = lmpdata_name
            atom_names, pbc = extxyz2lmpdata(
                extxyz_file=f"{tdir}/{K.FILE_FRAME_UNLABEL}",
                lmpdata_file=f"{tdir}/{lmpdata_name}",
                atom_style="atomic",
            )
            lammps_args["structure"]["pbc"] = pbc
            ### Auto assign atom_names in pair_coeff
            auto_atom_names = calc_args.get("auto_atom_names", False)
            if auto_atom_names:
                pair_coeff_list = [
                    f"{line} {' '.join(atom_names)}" for line in origin_pair_coeff_list
                ]
                lammps_args["structure"]["pair_coeff"] = pair_coeff_list

            lammps_args["extra"] = {"output_script": f"{tdir}/{K.RUNFILE_LAMMPS}"}
            Config.validate(config_dict=lammps_args, schema_file=K.SCHEMA_LAMMPS)
            write_yaml(lammps_args, f"{tdir}/{K.FILE_ARG_LAMMPS}")
            tmp_lammps_args = process_lammps_argdict(lammps_args)
            generate_script_lammps_singlepoint(**tmp_lammps_args)

        ### Copy runfile
        self._prepare_runfile_lammps()
        return

    def postprocess(self) -> list[list]:  # type: ignore
        """This function does:
        - Remove unlabeled .extxyz files, just keep the labeled ones.
        - Convert LAMMPS output to extxyz_labeled.
        """
        task_dirs = self.task_dirs
        ### Convert LAMMPS output to extxyz_labeled
        task_dirs = filter_dirs(task_dirs, has_files=[K.FILE_FRAME_UNLABEL, "frame_label.lmpdump"])
        for task_path in task_dirs:
            lmpdump2extxyz(
                lmpdump_file=f"{task_path}/frame_label.lmpdump",
                extxyz_file=f"{task_path}/{K.FILE_FRAME_LABEL}",
                original_cell_file=f"{task_path}/conf.lmpdata.original_cell",
            )

        ### Remove unlabeled extxyz files
        unlabel_dirs = filter_dirs(task_dirs, has_files=[K.FILE_FRAME_UNLABEL, K.FILE_FRAME_LABEL])
        remove_files_in_paths(files=[K.FILE_FRAME_UNLABEL], paths=unlabel_dirs)

        ### Remove lammps input files
        # _ = [Path(f"{p}/{RUNFILE_LAMMPS}").unlink() for p in unlabel_dirs]
        remove_files_in_paths(files=["conf.lmpdata"], paths=unlabel_dirs)

        ### Collect forces to list_of_forces
        labeled_dirs = filter_dirs(task_dirs, has_files=[K.FILE_FRAME_LABEL])
        set_of_forces = []
        for d in labeled_dirs:
            list_struct = read_extxyz(f"{d}/{K.FILE_FRAME_LABEL}")
            forces = [struct.calc.results["forces"].tolist() for struct in list_struct]  # type: ignore
            set_of_forces.extend(forces)
        # can save by `np.save("set_of_forces.npy", set_of_forces)`
        return set_of_forces
