"""Library for LAMMPS MD with SevenNet model."""

import textwrap
from copy import deepcopy
from pathlib import Path

from natsort import natsorted

from alff import ALFF_ROOT
from alff.al.utilal import D3ParamMD, MLP2Lammps
from alff.base import KEY as K
from alff.base import RemoteOperation, logger
from alff.util.script_lammps.lammps_code_creator import (
    generate_script_lammps_md,
    process_lammps_argdict,
)
from asext.io.readwrite import extxyz2lmpdata
from thkit.config import Config
from thkit.io import read_yaml, write_yaml
from thkit.path import collect_files, copy_file, filter_dirs, remove_dirs
from thkit.range import composite_index


#####ANCHOR pre MD Lammps
def premd_lammps_sevenn(work_dir, pdict, mdict):
    """Prepare MD args.

    Includes:
    - copy ML models to work_dir
    - collect initial configurations
    - prepare lammps args
    - generate task_dirs for ranges of temperature and press
    """
    ### note: work_dir = iter_dir/DIR_MD
    pdict_md = pdict["md"]

    ### copy ML_models to work_dir
    iter_dir = Path(work_dir).parent
    initial_checkpoints = read_yaml(f"{iter_dir}/{K.DIR_TRAIN}/{K.FILE_CHECKPOINTS}")
    checkpoints = [
        copy_file(p, p.replace(f"{K.DIR_TRAIN}", f"{K.DIR_MD}/{K.DIR_FWDATA}"))
        for p in initial_checkpoints
    ]
    write_yaml(checkpoints, f"{work_dir}/checkpoints.yml")

    ### collect initial configurations
    space_args: dict = read_yaml(f"{work_dir}/current_space.yml")
    init_struct_paths = pdict_md["init_struct_paths"]
    init_struct_idxs = list(set(composite_index(space_args.get("init_struct_idxs", []))))
    assert max(init_struct_idxs) < len(init_struct_paths), (
        "indices in 'init_struct_idxs' must be smaller than the number of 'init_struct_paths'"
    )

    structure_files = []
    struct_dict = {}  # save structures idx for information
    for idx in init_struct_idxs:
        files = sorted(collect_files(init_struct_paths[idx], patterns=["*.extxyz"]))
        copied_files = [
            copy_file(myfile, f"{work_dir}/idx{idx}_{i}/{K.FILE_FRAME_UNLABEL}")
            for i, myfile in enumerate(files)
        ]
        structure_files.extend(copied_files)
        struct_dict[f"init_struct_idx_{idx}"] = files  # relative to run_dir
    structure_dirs = [Path(fi).parent.as_posix() for fi in structure_files]
    write_yaml(structure_dirs, f"{work_dir}/structure_dirs.yml")
    write_yaml(struct_dict, f"{work_dir}/init_struct_paths.yml")

    ##### Prepare MD args
    temperature_list = space_args.get("temps", [])
    press_list = space_args.get("pressures", [])
    current_space_args = deepcopy(space_args)
    for key in ["init_struct_idxs", "temps", "pressures"]:
        current_space_args.pop(key, None)
    md_args = deepcopy(pdict_md.get("common_md_args", {}))
    md_args.update(current_space_args)

    ### Define LAMMPS args & checkpoint files (need convert checkpoint to lammps format)
    convert_args = pdict_md.get("checkpoint_conversion", {})
    selected_chkp = checkpoints[convert_args.get("checkpoint_idx", 0)]

    ### convert checkpoint to lammps_serial
    mlp_model = pdict["train"].get("mlp_model", "sevenn")
    extra_kwargs = convert_args.get("extra_kwargs", {})
    deployed_chkp = (Path(selected_chkp).parent / "deployed_sevenn.pt").as_posix()
    MLP2Lammps(mlp_model).convert(selected_chkp, outfile=deployed_chkp, **extra_kwargs)

    rel_deployed_chkp = Path(deployed_chkp).relative_to(work_dir).as_posix()

    lammps_args = {}
    ### D3 correction params
    ### There are combinations of (mlp_model, d3_package): mlp_model=["sevenn", "sevenn_mliap"], d3_package=["sevenn", "lammps"]
    dftd3_args = pdict_md.get("dftd3", None)
    if dftd3_args is not None:
        xc = dftd3_args.get("xc", "pbe")
        damping = dftd3_args.get("damping", "zero")
        cutoff = dftd3_args.get("cutoff", D3ParamMD().default_cutoff)
        cn_cutoff = dftd3_args.get("cn_cutoff", D3ParamMD().default_cn_cutoff)

        if dftd3_args.get("d3package", "sevenn") == "sevenn":
            ### use sevenn D3
            d3param = D3ParamMD("sevenn")
            damping = d3param.damping_map[damping]
            cutoff = d3param.angstrom_to_bohr2(cutoff)
            cn_cutoff = d3param.angstrom_to_bohr2(cn_cutoff)

            if mlp_model == "sevenn":
                lammps_args["structure"] = {
                    "pair_style": [f"hybrid/overlay e3gnn d3 {cutoff} {cn_cutoff} {damping} {xc}"],
                    "pair_coeff": [
                        f"* * e3gnn ../{rel_deployed_chkp} placeholder_for_atomnames",
                        "* * d3 placeholder_for_atomnames",
                    ],
                }
            elif mlp_model == "sevenn_mliap":
                lammps_args["structure"] = {
                    "pair_style": [
                        f"hybrid/overlay mliap unified ../{rel_deployed_chkp} 0  d3 {cutoff} {cn_cutoff} {damping} {xc}"
                    ],
                    "pair_coeff": [
                        "* * mliap         placeholder_for_atomnames",
                        "* * d3 placeholder_for_atomnames",
                    ],
                }

        elif dftd3_args.get("d3package", "sevenn") == "lammps":
            ### use lammps' D3 in sevenn: https://github.com/MDIL-SNU/SevenNet/issues/246
            d3param = D3ParamMD("lammps")
            damping = d3param.damping_map[damping]

            if mlp_model == "sevenn":
                lammps_args["structure"] = {
                    "pair_style": [
                        f"hybrid/overlay e3gnn dispersion/d3 {damping} {xc} {cutoff} {cn_cutoff}"
                    ],
                    "pair_coeff": [
                        f"* * e3gnn ../{rel_deployed_chkp} placeholder_for_atomnames",
                        "* * dispersion/d3 placeholder_for_atomnames",
                    ],
                }
            elif mlp_model == "sevenn_mliap":
                lammps_args["structure"] = {
                    "pair_style": [
                        f"hybrid/overlay mliap unified ../{rel_deployed_chkp} 0  dispersion/d3 {damping} {xc} {cutoff} {cn_cutoff}"
                    ],
                    "pair_coeff": [
                        "* * mliap         placeholder_for_atomnames",
                        "* * dispersion/d3 placeholder_for_atomnames",
                    ],
                }
            lammps_args["structure"]["extra_settings"] = ["neigh_modify one 20000 page 1000000"]

    else:  # no D3 correction
        if mlp_model == "sevenn":
            lammps_args["structure"] = {
                "pair_style": ["e3gnn"],
                "pair_coeff": [f"* * ../{rel_deployed_chkp} placeholder_for_atomnames"],
            }
        elif mlp_model == "sevenn_mliap":
            lammps_args["structure"] = {
                "pair_style": [f"mliap unified ../{rel_deployed_chkp} 0"],
                "pair_coeff": ["* * mliap         placeholder_for_atomnames"],
            }

    ### convert checkpoint to lammps_parallel (Note: Sevennet raises error with small simulation box < 200 atoms)
    # convert_model_sevenn_to_lammps(
    #     Path(model_files[0]).name, rundir=Path(model_files[0]).parent, parallel=True
    # )
    # rel_deployed_chkp = Path(model_files[0]).relative_to(work_dir).as_posix()
    # rel_deployed_chkp = rel_deployed_chkp.replace(Path(rel_deployed_chkp).name, "deployed_parallel")
    # pt_file_count = sum(
    #     1 for file in Path(f"{work_dir}/{rel_deployed_chkp}").glob("deployed_parallel*.pt")
    # )
    # lammps_args = {}
    # lammps_args["structure"] = {
    #     "pair_style": ["e3gnn/parallel"],
    #     "pair_coeff": [f"* * {pt_file_count} ../{rel_deployed_chkp} placeholder_for_atomnames"],
    # }

    lammps_args.update({"md": md_args})
    task_dirs = temperature_press_mdarg_lammps(
        structure_dirs, temperature_list, press_list, lammps_args
    )
    write_yaml(task_dirs, f"{work_dir}/task_dirs.yml")

    ##### Write python script for compute committee_error and select candidates
    _ = copy_file(
        f"{ALFF_ROOT}/al/utilal_uncertainty.py",
        f"{work_dir}/{K.DIR_FWDATA}/utilal_uncertainty.py",
    )
    committee_args = {  # default args
        "compute_stress": pdict_md.get("committee_std", {}).get("compute_stress", True),
        "rel_force": pdict_md.get("committee_std", {}).get("rel_force", None),
        "rel_stress": pdict_md.get("committee_std", {}).get("rel_stress", None),
        "e_std_lo": pdict_md.get("committee_std", {}).get("e_std_lo", 0.0),
        "e_std_hi": pdict_md.get("committee_std", {}).get("e_std_hi", 0.15),
        "f_std_lo": pdict_md.get("committee_std", {}).get("f_std_lo", 0.0),
        "f_std_hi": pdict_md.get("committee_std", {}).get("f_std_hi", 0.15),
        "s_std_lo": pdict_md.get("committee_std", {}).get("s_std_lo", 0.0),
        "s_std_hi": pdict_md.get("committee_std", {}).get("s_std_hi", 0.15),
        "block_size": 10000,
    }
    committee_str = ",\n        ".join([f"{k}={v}" for k, v in committee_args.items()])

    pyscript = textwrap.dedent(f"""
    import sys
    sys.path.append("../{K.DIR_FWDATA}")
    from utilal_uncertainty import ModelCommittee, simple_lmpdump2extxyz
    from glob import glob

    lmpdump_file = "traj_md_label.lmpdump"
    extxyz_file = "{K.FILE_TRAJ_MD}"

    ### Covert lmpdump to extxyz
    simple_lmpdump2extxyz(lmpdump_file, extxyz_file)

    ### Select candidate configurations
    checkpoints = glob("../{K.DIR_FWDATA}/model*/*.pth")
    print(checkpoints)

    committee = ModelCommittee(
        mlp_model="sevenn",
        model_files=checkpoints,
        {committee_str},
    )
    committee.select_candidate(extxyz_file)
    """)
    with open(f"{work_dir}/{K.DIR_FWDATA}/cli_committee_sevenn.py", "w") as f:
        f.write(pyscript)
    return


#####ANCHOR MD operation LammpsSevennet
class OperAlmdLammpsSevennet(RemoteOperation):
    """This class runs LAMMPS md for a list of structures in `task_dirs`."""

    def __init__(self, work_dir, pdict, multi_mdict, mdict_prefix="md"):
        super().__init__(work_dir, pdict, multi_mdict, mdict_prefix)
        self.op_name = "LAMMPS MD with SevenNet"
        self.task_filter = {
            "has_files": ["conf.lmpdata"],
            "no_files": ["committee_error.txt"],
        }
        return

    def prepare(self):
        """Prepare MD tasks.

        Includes:
        - Prepare the task_list
        - Prepare forward & backward files
        - Prepare commandlist_list for multi-remote submission
        """
        ### Prepare forward & backward files
        self.forward_common_files = [K.DIR_FWDATA]  # in work_dir
        self.forward_files = ["conf.lmpdata", K.RUNFILE_LAMMPS]  # all files in task_dirs
        self.backward_files = [
            "*_stress_value.txt",
            "committee_*",
            "*.extxyz",
        ]  # FILE_TRAJ_MD, FILE_TRAJ_MD_CANDIDATE,

        ### Prepare commandlist_list for multi-remote submission
        mdict_list = self.mdict_list
        commandlist_list = []
        for mdict in mdict_list:
            command_list = []
            md_command = mdict.get("command", "lmp_mpi")
            md_command = f"{md_command} -in {K.RUNFILE_LAMMPS}"
            command_list.append(md_command)

            ### compute committee_error
            # command = f"""(python ../{DIR_FWDATA}/cli_committee_sevenn.py >>pyerr.log 2>&1 || :)"""  # not care if error
            command = f"""(python ../{K.DIR_FWDATA}/cli_committee_sevenn.py)"""
            command_list.append(command)
            commandlist_list.append(command_list)
        self.commandlist_list = commandlist_list
        return

    def postprocess(self):
        work_dir = self.work_dir
        task_dirs = self.task_dirs

        _sampling_report(work_dir, task_dirs)

        ### Clean up
        # md_traj_files = [f"{p}/{FILE_TRAJ_MD}" for p in task_dirs]
        # [Path(f).unlink() for f in md_traj_files if Path(f).exists()]
        return


#####ANCHOR Helper functions
def temperature_press_mdarg_lammps(
    struct_dirs: list,
    temperature_list: list = [],
    press_list: list = [],
    lammps_argdict: dict = {},
) -> list:
    """Generate the task_dirs for ranges of temperatures and stresses.

    Args:
        struct_dirs (list): List of dirs contains configuration files.
        temperature_list (list): List of temperatures.
        press_list (list): List of stresses.
        lammps_argdict (dict): See [lammps.md schema](https://thangckt.github.io/alff_doc/schema/config_lammps/)
    """
    lammps_args = deepcopy(lammps_argdict)  # avoid modifying original dict
    lammps_args["structure"].update({"read_data": "conf.lmpdata"})
    list_pair_coeff_original = deepcopy(lammps_args["structure"]["pair_coeff"])  # to avoid changing
    task_dirs = []
    counter = 0
    for struct_path in struct_dirs:
        if temperature_list:
            for temp in temperature_list:  # temperature range
                if press_list:
                    for press in press_list:  # stress range
                        if isinstance(press, list):
                            press_str = "_".join([f"{s:.1f}" for i, s in enumerate(press) if i < 3])
                        else:
                            press_str = f"{press:.1f}"

                        new_dir = f"{struct_path}_t{temp:.0f}_s{press_str}"
                        # new_dir = new_dir.replace("idx", f"md_{counter:{FMT_STRUCT}}_id")
                        new_dir = new_dir.replace("idx", "md_id")  # remove counter
                        copy_file(
                            f"{struct_path}/{K.FILE_FRAME_UNLABEL}",
                            f"{new_dir}/{K.FILE_FRAME_UNLABEL}",
                        )
                        ### Convert extxyz to lammps_data
                        atom_names, pbc = extxyz2lmpdata(
                            extxyz_file=f"{new_dir}/{K.FILE_FRAME_UNLABEL}",
                            lmpdata_file=f"{new_dir}/conf.lmpdata",
                            atom_style="atomic",
                        )
                        # TODO need to rotate the stress tensor
                        ### udpate lammps_md_args
                        list_pair_coeff = [
                            txt.replace("placeholder_for_atomnames", " ".join(atom_names))
                            for txt in list_pair_coeff_original
                        ]
                        lammps_args["structure"]["pair_coeff"] = list_pair_coeff
                        lammps_args["structure"]["pbc"] = pbc
                        lammps_args["extra"] = {"output_script": f"{new_dir}/{K.RUNFILE_LAMMPS}"}

                        tmp_md = {"temp": temp, "press": press, "ensemble": "NPT"}
                        lammps_args["md"].update(tmp_md)

                        Config.validate(config_dict=lammps_args, schema_file=K.SCHEMA_LAMMPS)
                        write_yaml(lammps_args, f"{new_dir}/{K.FILE_ARG_LAMMPS}")
                        tmp_lammps_args = process_lammps_argdict(lammps_args)
                        generate_script_lammps_md(**tmp_lammps_args)
                        ### save path
                        task_dirs.append(new_dir)
                        counter += 1
                else:
                    new_dir = f"{struct_path}_t{temp:.0f}"
                    # new_dir = new_dir.replace("idx", f"md_{counter:{FMT_STRUCT}}_id")
                    new_dir = new_dir.replace("idx", "md_id")  # remove counter
                    copy_file(
                        f"{struct_path}/{K.FILE_FRAME_UNLABEL}",
                        f"{new_dir}/{K.FILE_FRAME_UNLABEL}",
                    )
                    ### Convert extxyz to lammps_data
                    atom_names, pbc = extxyz2lmpdata(
                        extxyz_file=f"{new_dir}/{K.FILE_FRAME_UNLABEL}",
                        lmpdata_file=f"{new_dir}/conf.lmpdata",
                        atom_style="atomic",
                    )
                    ### udpate lammps_md_args
                    list_pair_coeff = [
                        txt.replace("placeholder_for_atomnames", " ".join(atom_names))
                        for txt in list_pair_coeff_original
                    ]
                    lammps_args["structure"]["pair_coeff"] = list_pair_coeff
                    lammps_args["structure"]["pbc"] = pbc
                    lammps_args["extra"] = {"output_script": f"{new_dir}/{K.RUNFILE_LAMMPS}"}

                    tmp_md = {"temp": temp, "ensemble": "NVT"}
                    lammps_args["md"].update(tmp_md)

                    Config.validate(config_dict=lammps_args, schema_file=K.SCHEMA_LAMMPS)
                    write_yaml(lammps_args, f"{new_dir}/{K.FILE_ARG_LAMMPS}")
                    tmp_lammps_args = process_lammps_argdict(lammps_args)
                    generate_script_lammps_md(**tmp_lammps_args)
                    ### save path
                    task_dirs.append(new_dir)
                    counter += 1
        else:
            new_dir = f"{struct_path}"
            # new_dir = new_dir.replace("idx", f"md_{counter:{FMT_STRUCT}}_id")
            new_dir = new_dir.replace("idx", "md_id")  # remove counter
            ### Convert extxyz to lammps_data
            atom_names, pbc = extxyz2lmpdata(
                extxyz_file=f"{new_dir}/{K.FILE_FRAME_UNLABEL}",
                lmpdata_file=f"{new_dir}/conf.lmpdata",
                atom_style="atomic",
            )
            ### udpate lammps_md_args
            list_pair_coeff = [
                txt.replace("placeholder_for_atomnames", " ".join(atom_names))
                for txt in list_pair_coeff_original
            ]
            lammps_args["structure"]["pair_coeff"] = list_pair_coeff
            lammps_args["structure"]["pbc"] = pbc
            lammps_args["extra"] = {"output_script": f"{new_dir}/{K.RUNFILE_LAMMPS}"}

            tmp_md = {"ensemble": "NVE"}
            lammps_args["md"].update(tmp_md)

            Config.validate(config_dict=lammps_args, schema_file=K.SCHEMA_LAMMPS)
            write_yaml(lammps_args, f"{new_dir}/{K.FILE_ARG_LAMMPS}")
            tmp_lammps_args = process_lammps_argdict(lammps_args)
            generate_script_lammps_md(**tmp_lammps_args)
            ### save path
            task_dirs.append(new_dir)
            counter += 1
    ### delete the original dirs (replaced by temp_press dirs)
    _ = [remove_dirs(p) for p in struct_dirs if p not in task_dirs]
    return task_dirs


def _sampling_report(work_dir: str, task_dirs: list[str]) -> None:
    """Generate sampling report for all task_dirs."""
    not_run_structs = filter_dirs(task_dirs, no_files=["committee_judge_summary.yml"])
    run_structs = filter_dirs(task_dirs, has_files=["committee_judge_summary.yml"])
    not_ok_structs = [
        p
        for p in run_structs
        if (_sampling_evaluation(f"{p}/committee_judge_summary.yml") == "notok")
    ]
    bad_structs = [
        p
        for p in run_structs
        if (_sampling_evaluation(f"{p}/committee_judge_summary.yml") == "bad")
    ]
    bad_structs.extend(not_run_structs)

    ### Write report
    [Path(f).unlink() for f in collect_files(work_dir, patterns=["md_warning_*.txt"])]

    if len(not_ok_structs) > 0:
        filename = f"{work_dir}/md_warning_{len(not_ok_structs)}_not_enough_sampling.txt"
        write_yaml(natsorted(not_ok_structs), filename)
        logger.warning(
            f"There are {len(not_ok_structs)} structures need more sampling, see file:\n\t'{filename}'"
        )
    if len(bad_structs) > 0:
        filename = f"{work_dir}/md_warning_{len(bad_structs)}_bad_sampling.txt"
        write_yaml(natsorted(bad_structs), filename)
        logger.warning(
            f"There are {len(bad_structs)} structures with bad sampling, see file:\n\t'{filename}'"
        )
    return


def _sampling_evaluation(summary_file: str) -> str:
    """Check if the sampling result is good enough.

    Args:
        summary_file (str): The text file summarizing the sampling result.

    Returns:
        str: "ok", "notok", or "bad"
    """
    d: dict = read_yaml(summary_file)
    result = "ok"
    if (d["inaccurates"] >= d["accurates"]) and (d["inaccurates"] >= d["candidates"]):
        if d["accurates"] == 0 and d["candidates"] == 0:
            result = "bad"
        else:
            result = "notok"
    return result
