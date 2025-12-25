"""Some notes
- Must set txt='calc.txt' in GPAW calculator for backward files.
- param_yaml must contain
    - a dict `gpaw_calc` with GPAW parameters.
"""

import argparse
from typing import cast

import yaml
from ase import Atoms
from ase.calculators.mixing import SumCalculator
from ase.io import read, write
from ase.parallel import parprint
from gpaw import GPAW


#####ANCHOR Helper functions
def get_cli_args():
    """Get the arguments from the command line."""
    parser = argparse.ArgumentParser(description="Optimize structure using GPAW")
    parser.add_argument("param", type=str, help="The YAML file contains parameters")
    args = parser.parse_args()
    configfile = args.param
    pdict = yaml.safe_load(open(configfile))
    return pdict


pdict = get_cli_args()
calc_args = pdict.get("calc_args", {})

#####ANCHOR Define calculator
gpaw_args = calc_args.get("gpaw", {})
if not gpaw_args:
    parprint(
        "WARNING: `calc.gpaw` is not set in the YAML file. Therefore, default parameters is used."
    )

gpaw_params = {  # GPAW default parameters
    "mode": {"name": "pw", "ecut": 500},  # use PlaneWave method, with energy cutoff in eV
    "xc": "PBE",  # exchange-correlation functional
    "convergence": {"energy": 1e-6, "density": 1e-4, "eigenstates": 1e-8},  #  convergence criteria
    "occupations": {"name": "fermi-dirac", "width": 0.01},
    "txt": "calc_singlepoint.txt",
    # "kpts": {"density": 3.0, "gamma": True},  # if not set only Gamma-point is used
    # "symmetry": "off",  # to avoid error: `broken symmetry`
    # "parallel": {
    #     "sl_auto": True,  # enable ScaLAPACK parallelization
    #     "use_elpa": True,  # enable Elpa eigensolver
    #     "augment_grids":True,  # use all cores for XC/Poisson
    #     'domain': (int(world.size/8), 8, 1),
    # },
}
gpaw_params.update(gpaw_args)
calc_pw = GPAW(**gpaw_params)

### DFTD3
dftd3_args = calc_args.get("dftd3", {})
if dftd3_args and not calc_args.get("exclude_result_dftd3", False):
    from dftd3.ase import DFTD3

    xc = gpaw_params["xc"].lower()
    calc_d3 = DFTD3(method=xc, **dftd3_args)
    calc = SumCalculator([calc_pw, calc_d3])
    parprint("INFO: Use DFTD3 for dispersion correction")
else:
    calc = calc_pw

#####ANCHOR Define atoms
### atoms: read EXTXYZ file
struct_args = pdict["structure"]
extxyz_file = struct_args["from_extxyz"]
atoms = read(extxyz_file, format="extxyz", index="-1")
atoms = cast(Atoms, atoms)  # for type checker
input_pbc = struct_args.get("pbc", False)
if input_pbc:
    atoms.pbc = input_pbc

### set calculator
atoms.calc = calc

#####ANCHOR Calculation
### compute properties
pot_energy = (
    atoms.get_potential_energy()
)  # `force_consistent=True` cause error if combine multi-calculators
forces = atoms.get_forces()
try:  # compute stress when the calculator supports it
    stress = atoms.get_stress()
except Exception:
    stress = None
    pass

### Save results (only last frame)
atoms.info["pbc"] = atoms.get_pbc()

##### write output extxyz file (final frame)
output_file = extxyz_file.replace(".extxyz", "_label.extxyz")
write(output_file, atoms, format="extxyz")
