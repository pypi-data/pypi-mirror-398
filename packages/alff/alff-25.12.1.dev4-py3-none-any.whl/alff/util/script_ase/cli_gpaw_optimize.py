"""Some notes
- Must set txt='calc.txt' in GPAW calculator for backward files.
- param_yaml must contain
    - a dict `gpaw_calc` with GPAW parameters.
    - a dict `optimize` with ASE optimization parameters.
"""

import argparse
from typing import cast

import yaml
from ase import Atoms
from ase.calculators.mixing import SumCalculator
from ase.calculators.singlepoint import SinglePointCalculator
from ase.constraints import FixAtoms, FixedPlane, FixSymmetry
from ase.filters import FrechetCellFilter
from ase.io import read, write
from ase.optimize import BFGS
from ase.parallel import parprint
from gpaw import GPAW


#####ANCHOR Helper functions
def get_cli_args():
    """Get the arguments from the command line."""
    parser = argparse.ArgumentParser(description="Optimize structure using GPAW")
    parser.add_argument("param", type=str, help="The YAML file contains parameters")
    args = parser.parse_args()
    configfile = args.param
    with open(configfile) as f:
        pdict = yaml.safe_load(f)
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
    "txt": "calc_optimize.txt",
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
if dftd3_args:
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


#####ANCHOR Relax structure
### Constraints
constraint_arg = pdict.get("constraint", None)
if constraint_arg is not None:
    c = []
    if "fix_atoms" in constraint_arg:
        if "fix_idxs" in constraint_arg["fix_atoms"]:
            fix_idxs = constraint_arg["fix_atoms"]["fix_idxs"]
            if constraint_arg["fix_atoms"].get("fix_only_z", False):
                c.append(FixedPlane(indices=fix_idxs, direction=[0, 0, 1]))
                parprint(f"INFO: Fix positions in z-direction, with atom indices {fix_idxs}")
            else:
                c.append(FixAtoms(indices=fix_idxs))
                parprint(f"INFO: Fix positions in all directions, with atom indices {fix_idxs}")
    if "fix_symmetry" in constraint_arg:
        symprec = constraint_arg["fix_symmetry"].get("symprec", 1e-5)
        c.append(FixSymmetry(atoms, symprec=symprec))
        parprint("INFO: Fix symmetry of the structure.")
    atoms.set_constraint(c)

### optimize parameters
opt_args = pdict.get("optimize", {})
mask = opt_args.get("mask", None)
if mask is not None:
    assert len(mask) in [3, 6], "`mask` must be a list of 3 or 6 boolean values."
    if len(mask) == 3:
        mask = mask + [0, 0, 0]  # noqa: RUF005

fmax = opt_args.get("fmax", 0.05)
max_steps = opt_args.get("max_steps", 10000)

### relax structure
atoms_filter = FrechetCellFilter(atoms, mask=mask)
opt = BFGS(atoms_filter)  # type: ignore
opt.run(fmax=fmax, steps=max_steps)

#####ANCHOR Write final optimized structure
pot_energy = (
    atoms.get_potential_energy()
)  # `force_consistent=True` cause error if combine multi-calculators
forces = atoms.get_forces()
stress = atoms.get_stress()

atoms.info["pbc"] = atoms.get_pbc()
# atoms.info["test_force"] = atoms_filter.get_forces()

##### write output extxyz file (final frame)
if constraint_arg != {}:
    atoms.set_constraint()  # remove constraints before write to avoid possible error in write()

if calc_args.get("exclude_result_dftd3", False) and dftd3_args:
    parprint("INFO: Exclude DFTD3 results from final energy/force/stress")
    struct = atoms.copy()
    struct.calc = SinglePointCalculator(struct)
    struct.calc.results = calc_pw.results
else:
    struct = atoms

output_file = extxyz_file.replace(".extxyz", "_label.extxyz")
write(output_file, struct, format="extxyz")
