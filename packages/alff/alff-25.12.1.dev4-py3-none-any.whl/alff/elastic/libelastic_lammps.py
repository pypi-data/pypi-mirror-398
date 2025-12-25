from pathlib import Path

from asext.io.readwrite import lmpdump2extxyz
from thkit.io import read_yaml
from thkit.path import filter_dirs, remove_files_in_paths

from alff.base import KEY as K

### Reuse almost functions from phonon_lammps, except for the post_* functions. Need to collect stress.


#####ANCHOR Stage 1 - LAMMPS optimize initial structure
def postelast_lammps_optimize(work_dir, pdict):
    """This function does:
    - Remove unlabeled .extxyz files, just keep the labeled ones.
    - Convert LAMMPS output to extxyz_labeled.
    """
    structure_paths = read_yaml(f"{work_dir}/structure_dirs.yml")
    ### Convert LAMMPS output to extxyz_labeled
    task_dirs = [p for p in structure_paths if not Path(f"{p}/{K.FILE_FRAME_LABEL}").exists()]
    for task_path in task_dirs:
        lmpdump2extxyz(
            lmpdump_file=f"{task_path}/output_md/conf_0.lmpdump",
            extxyz_file=f"{task_path}/{K.FILE_FRAME_LABEL}",
            original_cell_file=f"{task_path}/conf.lmpdata.original_cell",
            stress_file=f"{task_path}/output_md/run0_stress_value.txt",
        )

    ### Remove unlabeled extxyz files
    unlabel_paths = filter_dirs(
        structure_paths, has_files=[K.FILE_FRAME_UNLABEL, K.FILE_FRAME_LABEL]
    )
    remove_files_in_paths(files=[K.FILE_FRAME_UNLABEL], paths=unlabel_paths)

    ### Remove lammps input files
    # remove_files_in_paths(files=[RUNFILE_LAMMPS], paths=unlabel_paths)
    remove_files_in_paths(files=["conf.lmpdata"], paths=unlabel_paths)
    # remove_dirs_in_paths(dirs=['output_md'],paths=unlabel_paths)
    return


#####ANCHOR Stage 4 - run MD singlepoint on supercell
def postelast_lammps_singlepoint(work_dir, pdict):
    """This function does:
    - Clean up unlabelled extxyz files
    - Collect forces from the output files
    """
    supercell_paths = read_yaml(f"{work_dir}/structure_dirs.yml")
    ### Convert LAMMPS output to extxyz_labeled
    task_dirs = [p for p in supercell_paths if not Path(f"{p}/{K.FILE_FRAME_LABEL}").exists()]
    for task_path in task_dirs:
        lmpdump2extxyz(
            lmpdump_file=f"{task_path}/output_md/conf_0.lmpdump",
            extxyz_file=f"{task_path}/{K.FILE_FRAME_LABEL}",
            original_cell_file=f"{task_path}/conf.lmpdata.original_cell",
            stress_file=f"{task_path}/output_md/run0_stress_value.txt",
        )

    ### Remove unlabeled extxyz files
    unlabel_paths = filter_dirs(task_dirs, has_files=[K.FILE_FRAME_UNLABEL, K.FILE_FRAME_LABEL])
    remove_files_in_paths(files=[K.FILE_FRAME_UNLABEL], paths=unlabel_paths)

    ### Remove lammps input files
    # remove_files_in_paths(files=[RUNFILE_LAMMPS], paths=unlabel_paths)
    remove_files_in_paths(files=["conf.lmpdata"], paths=unlabel_paths)
    # remove_dirs_in_paths(dirs=["output_md"], paths=unlabel_paths)
    return
