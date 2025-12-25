"""Command line interfaces for ALFF workflows."""

import argparse

from alff.al.active_learning import WorkflowActiveLearning
from alff.al.finetune import WorkflowFinetune
from alff.elastic.elastic import WorkflowElastic
from alff.gdata.gendata import WorkflowGendata
from alff.pes.pes_scan import WorkflowPes
from alff.phonon.phonon import WorkflowPhonon


#####ANCHOR Processes
def alff_al():
    """CLI for active learning."""
    params_file, machines_file = get_cli_args()
    wf = WorkflowActiveLearning(params_file, machines_file)
    wf.run()
    return


def alff_finetune():
    """CLI for fine-tuning."""
    params_file, machines_file = get_cli_args()
    wf = WorkflowFinetune(params_file, machines_file)
    wf.run()
    return


def alff_gen():
    """CLI for data generation."""
    params_file, machines_file = get_cli_args()
    wf = WorkflowGendata(params_file, machines_file)
    wf.run()
    return


def alff_phonon():
    """CLI for phonon calculation."""
    params_file, machines_file = get_cli_args()
    wf = WorkflowPhonon(params_file, machines_file)
    wf.run()
    return


def alff_pes():
    """CLI for PES scanning calculation."""
    params_file, machines_file = get_cli_args()
    wf = WorkflowPes(params_file, machines_file)
    wf.run()
    return


def alff_elastic():
    """CLI for elastic constants calculation."""
    params_file, machines_file = get_cli_args()
    wf = WorkflowElastic(params_file, machines_file)
    wf.run()
    return


def convert_chgnet_to_xyz():
    """CLI for converting the MPCHGNet dataset to XYZ format."""
    from alff.gdata.convert_mpchgnet_to_xyz import run_convert

    run_convert()
    return


#####ANCHOR Helper functions
def get_cli_args() -> tuple[str, str]:
    """Get arguments from the command line."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "params_file",
        type=str,
        help="The file contains setting parameters for the generator",
    )
    parser.add_argument(
        "machines_file",
        type=str,
        help="The file contains settings of the machine that running the generator",
    )
    args = parser.parse_args()
    params_file = args.params_file
    machines_file = args.machines_file
    return params_file, machines_file
