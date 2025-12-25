### Source: https://github.com/janosh/matbench-discovery/blob/main/models/sevennet/train_sevennet/convert_mptrj_to_xyz.py
# The original script used a `SinglePointCalculator` to save the energy, forces, and stress in the ASE Atoms object.
# This modified script uses the `atoms.info` and `atoms.arrays` to store these information.
### Modified by C.Thang Nguyen

import argparse
import json
from typing import Any

import ase.units
import numpy as np
from ase import Atoms
from ase.data import atomic_numbers
from ase.io import write
from ase.stress import full_3x3_to_voigt_6_stress
from rich.progress import track

### keys from MPtrj_2022.9_full.json (excluded "forces" and "stress")
info_keys = [
    "uncorrected_total_energy",
    "corrected_total_energy",
    "energy_per_atom",
    "ef_per_atom",
    "e_per_atom_relaxed",
    "ef_per_atom_relaxed",
    "magmom",  # 1d list (n_atoms)
    "bandgap",
    "mp_id",
]


def chgnet_to_ase_atoms(datum: dict[str, dict[str, Any]]) -> list[Atoms]:
    struct_list = [None] * len(datum)
    for i, (mat_id, dtm) in enumerate(datum.items()):
        ### pymatgen.core.Structure to ase.Atoms
        struct = dtm["structure"]
        cell = struct["lattice"]["matrix"]
        sites = struct["sites"]
        species = [atomic_numbers[site["species"][0]["element"]] for site in sites]
        pos = [site["xyz"] for site in sites]
        atoms = Atoms(species, pos, cell=cell, pbc=True)

        ### update matrix
        force = dtm["force"]
        atoms.arrays["ref_force"] = np.array(force)  # eV/Angstrom

        ### Add info (note: can not read value from keys `energy`, `forces` and `stress`, since they are used by ASE in `calc.results` dict. So, use prefix `ref_` to avoid conflict). See more https://gitlab.com/ase/ase/-/issues/1432
        stress_33 = dtm["stress"]  # 2d list (3, 3), kBar
        ## Convert stress from kBar to eV/A^3 and use ASE sign convention
        stress_33 = np.array(stress_33) * (-0.1 / ase.units.GPa)  # eV/A^3
        stress = full_3x3_to_voigt_6_stress(stress_33)  # eV/A^3

        info = {
            "data_from": "MP-CHGNet",
            "calc_id": mat_id.split("-")[2],
            "ionic_step_id": mat_id.split("-")[3],
            "stress_33": stress_33,
            "ref_stress": stress,
            "ref_energy": dtm["corrected_total_energy"],
        }
        for key in info_keys:
            info[key] = dtm[key]
        atoms.info = info

        struct_list[i] = atoms  # type: ignore
    return struct_list  # type: ignore


def run_convert():
    ### Parameters
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "mptrj",
        type=str,
        default="MPtrj_2022_9_full.json",
        help="The path to the MPtrj JSON file",
    )
    args = parser.parse_args()
    filename = args.mptrj

    ### Start reading data
    print(f"Reading file {filename} ...")
    with open(filename) as f:
        data = json.load(f)

    dataset = list(data.values())
    asestruct_list = []
    for frame_dict in track(dataset, refresh_per_second=0.1):
        asestruct_list.extend(chgnet_to_ase_atoms(frame_dict))

    new_filename = filename.replace(".json", ".extxyz")
    print(f"Writing file {new_filename} ...")
    write(new_filename, asestruct_list, "extxyz", append=True)

    print("Done!")
    return


if __name__ == "__main__":
    run_convert()
