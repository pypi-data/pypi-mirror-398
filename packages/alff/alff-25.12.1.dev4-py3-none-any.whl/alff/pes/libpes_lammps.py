"""Library for LAMMPS-based PES operations."""

from copy import deepcopy
from pathlib import Path

from alff.base import KEY as K
from alff.base import RemoteOperation, logger
from alff.util.script_lammps.lammps_code_creator import (
    generate_script_lammps_minimize,
    process_lammps_argdict,
)
from asext.io.readwrite import extxyz2lmpdata, lmpdump2extxyz
from thkit.config import Config
from thkit.io import read_yaml, write_yaml
from thkit.path import (
    copy_file,
    filter_dirs,
    remove_files_in_paths,
)


#####ANCHOR Stage 1 - LAMMPS optimize initial structure
class OperPESLammpsOptimize(RemoteOperation):
    """This class does LAMMPS optimization for a list of structures in `task_dirs`.

    This class can also be used for phonon LAMMPS optimization `alff.phonon.libphonon_lammps.py`
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
        optimize_args = self.pdict["optimize_args"]["lammps"]

        ### Prepare lammps_arg for MS simulation
        lammps_args = {}
        lammps_args["optimize"] = optimize_args
        lammps_args["optimize"]["press"] = optimize_args.get("press", 0.0)
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

    def _prepare_runfile_lammps(self):
        work_dir = self.work_dir
        calc_args = self.pdict["calculator"]["calc_args"]["lammps"]

        ### Copy potential file to work_dir
        file_potentials = calc_args.get("file_potentials", [])
        _ = [copy_file(f, work_dir) for f in file_potentials]

        ### Prepare forward & backward files
        self.forward_common_files = [Path(f).name for f in file_potentials]  # files in work_dir
        self.forward_files = ["*.lmpdata", K.RUNFILE_LAMMPS]  # files in task_path
        self.backward_files = ["log.lammps", "frame_label.lmpdump", "frame_label_*.txt"]

        ### Prepare commandlist_list for multi-remote submission
        mdict_list = self.mdict_list
        commandlist_list = []
        for mdict in mdict_list:
            command_list = []
            md_cmd = mdict.get("command", "lmp_mpi")
            md_cmd = f"{md_cmd} -in {K.RUNFILE_LAMMPS}"  #  run file in task_dir  # `../` to run file in common directory
            command_list.append(md_cmd)
            commandlist_list.append(command_list)
        self.commandlist_list = commandlist_list
        return

    def postprocess(self):
        """This function does:
        - Remove unlabeled .extxyz files, just keep the labeled ones.
        - Convert LAMMPS output to extxyz_labeled.
        """
        task_dirs = self.task_dirs
        ### Convert LAMMPS output to extxyz_labeled
        task_dirs = filter_dirs(task_dirs, has_files=[K.FILE_FRAME_UNLABEL, "frame_label.lmpdump"])
        for tdir in task_dirs:
            lmpdump2extxyz(
                lmpdump_file=f"{tdir}/frame_label.lmpdump",
                extxyz_file=f"{tdir}/{K.FILE_FRAME_LABEL}",
                original_cell_file=f"{tdir}/conf.lmpdata.original_cell",
                stress_file=f"{tdir}/frame_label_stress_value.txt",
            )

        ### Remove unlabeled extxyz files
        unlabel_dirs = filter_dirs(task_dirs, has_files=[K.FILE_FRAME_UNLABEL, K.FILE_FRAME_LABEL])
        remove_files_in_paths(files=[K.FILE_FRAME_UNLABEL], paths=unlabel_dirs)

        ### Remove lammps input files
        # remove_files_in_paths(files=[RUNFILE_LAMMPS], paths=unlabel_dirs)
        # remove_files_in_paths(files=["conf.lmpdata"], paths=unlabel_dirs)
        return


#####ANCHOR Stage 4 - compute energy by DFT/MD
class OperPESLammpsOptimizeFixatom(OperPESLammpsOptimize):
    """The same base class, only need to redefine the `.prepare()` method."""

    def __init__(self, work_dir, pdict, multi_mdict, mdict_prefix="lammps"):
        super().__init__(work_dir, pdict, multi_mdict, mdict_prefix)
        self.op_name = "LAMMPS optimize fixed atoms"
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
        work_dir = self.work_dir
        pdict = self.pdict

        calc_args = pdict["calculator"]["calc_args"]["lammps"]
        optimize_args = pdict["optimize_args"]["lammps"]

        ### Read fixed atoms
        fixed_atoms = read_yaml(f"{work_dir}/fix_idxs.yml")
        idstr = " ".join([str(i + 1) for i in fixed_atoms])  # LAMMPS id starts from 1
        extra_settings = [f"group   dead_atoms id {idstr}"]
        if pdict.get("constraint", {}).get("fix_atoms", {}).get("fix_only_z", False):
            extra_settings += ["fix     fnomove dead_atoms setforce NULL NULL 0.0"]
            logger.info("Only fix atom positions in z-direction.")
        else:
            extra_settings += ["fix     fnomove dead_atoms setforce 0.0 0.0 0.0"]
            logger.info("Fix atom positions in all directions.")

        ### Prepare lammps_arg for MS simulation
        lammps_args = {}
        lammps_args["optimize"] = optimize_args
        lammps_args["optimize"]["press"] = optimize_args.get("press", 0.0)
        lammps_args["structure"] = deepcopy(calc_args)
        lammps_args["structure"]["extra_settings"] = extra_settings
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
