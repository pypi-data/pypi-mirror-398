"""Some notes:
- Run MD in ase following this tutorial: https://wiki.fysik.dtu.dk/ase/tutorials/md/md.html
- For MD run, control symmetry to avoid error: `broken symmetry`.
- Must set txt='calc.txt' in GPAW calculator for backward files.
- param_yaml must contain
    - a dict `gpaw_calc` with GPAW parameters.
    - a dict `md` with ASE MD parameters.
"""

import argparse
import warnings
from pathlib import Path
from typing import cast

import yaml
from ase import Atoms, units
from ase.calculators.mixing import SumCalculator
from ase.calculators.singlepoint import SinglePointCalculator
from ase.io import read, write  # Trajectory
from ase.md.langevin import Langevin
from ase.md.melchionna import MelchionnaNPT
from ase.md.nose_hoover_chain import NoseHooverChainNVT  # , IsotropicMTKNPT
from ase.md.velocitydistribution import MaxwellBoltzmannDistribution, Stationary
from ase.md.verlet import VelocityVerlet
from ase.parallel import paropen, parprint
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
    "txt": "calc_aimd.txt",
    # "kpts": {"density": 3.0, "gamma": True},                              # if not set only Gamma-point is used
    "symmetry": "off",  # to avoid error: `broken symmetry`
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

    xc = dftd3_args.get("xc", "pbe").lower()
    if gpaw_params.get("xc", None):
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


#####ANCHOR MD simulation
### MD parameters
md_args = {
    "ensemble": "NVE",
    "dt": 1,
    "temp": 300,
    "thermostat": "langevin",
    "barostat": "parrinello_rahman",
}
input_md_args = pdict.get("md", {})
md_args.update(input_md_args)

thermostat = md_args["thermostat"]
support_thermostats = ["langevin", "nose_hoover", "nose_hoover_chain"]
if thermostat not in support_thermostats:
    raise ValueError(f"Unsupported thermostat '{thermostat}'. Choices: {support_thermostats}")
barostat = md_args["barostat"]
support_barostats = ["parrinello_rahman", "iso_nose_hoover_chain", "aniso_nose_hoover_chain"]
if barostat not in support_barostats:
    raise ValueError(f"Unsupported barostat {barostat}. Choices: {support_barostats}")

dt = md_args["dt"] * units.fs
temp = md_args["temp"]
ensemble = md_args["ensemble"]

### Set the momenta corresponding to T=300K
MaxwellBoltzmannDistribution(atoms, temperature_K=temp, force_temp=True)
Stationary(atoms)  # Set zero total momentum to avoid drifting

### DYN object
dyn = VelocityVerlet(atoms, timestep=dt)  # default, for type checker

if ensemble == "NVE":
    dyn = VelocityVerlet(atoms, timestep=dt)

elif ensemble == "NVT":
    if thermostat == "langevin":
        friction = md_args.get("langevin_friction", 0.002) / units.fs
        dyn = Langevin(atoms, timestep=dt, temperature_K=temp, friction=friction)
    elif thermostat == "nose_hoover":
        tdamp = md_args.get("tdamp", 100)  # damping time for Nose-Hoover thermostat
        dyn = MelchionnaNPT(
            atoms,
            timestep=dt,
            temperature_K=temp,
            ttime=tdamp * dt,
            pfactor=None,  # none for NVT
        )
    elif thermostat == "nose_hoover_chain":
        tdamp = thermostat.get("tdamp", 100)  # damping time for nose_hoover_chain, # type: ignore
        dyn = NoseHooverChainNVT(
            atoms,
            timestep=dt,
            temperature_K=temp,
            tdamp=tdamp * dt,
            tchain=3,
        )

elif ensemble == "NPT":
    stress = md_args.get("press", None)  # external stress for NPT, in GPa
    if stress is not None:
        stress_in_eVA3 = stress / units.GPa  # to eV/Angstrom^3
    else:
        stress_in_eVA3 = None

    if barostat == "parrinello_rahman":
        warnings.warn("This dynamics is not recommended due to stability problems.")
        tdamp = md_args.get("tdamp", 100)
        pfactor = md_args.get(
            "pfactor", 2e6
        )  # pressure scaling factor for parrinello_rahman barostat
        mask = md_args.get("mask", None)
        if mask is None:
            mask = atoms.pbc
        dyn = MelchionnaNPT(
            atoms,
            timestep=dt,
            temperature_K=temp,
            externalstress=stress_in_eVA3,  # stress in eV/Angstrom^3
            ttime=tdamp * dt,
            pfactor=pfactor,
            mask=mask,
        )
    elif barostat in ["iso_nose_hoover_chain", "aniso_nose_hoover_chain"]:
        from ase.md.nose_hoover_chain import MTKNPT, IsotropicMTKNPT

        tdamp = thermostat.get("tdamp", 100)
        pdamp = barostat.get("pdamp", 1000)
        if barostat == "iso_nose_hoover_chain":
            dyn = IsotropicMTKNPT(
                atoms,
                timestep=dt,
                temperature_K=temp,
                pressure_au=stress_in_eVA3,  # stress in eV/Angstrom^3, # type: ignore
                tdamp=tdamp * dt,
                pdamp=pdamp * dt,
                tchain=3,
                pchain=3,
            )
        elif barostat == "aniso_nose_hoover_chain":
            mask = barostat.get("mask", None)  # type: ignore
            if mask is None:
                mask = atoms.pbc
            if any(x == 0 for x in mask):
                raise NotImplementedError(
                    "'aniso_nose_hoover_chain' is not implemented yet. Consider using 'parrinello_rahman' instead."
                )
            dyn = MTKNPT(
                atoms,
                timestep=dt,
                temperature_K=temp,
                pressure_au=stress_in_eVA3,  # stress in eV/Angstrom^3, # type: ignore
                tdamp=tdamp * dt,
                pdamp=pdamp * dt,
                tchain=3,
                pchain=3,
            )

    else:
        raise NotImplementedError("{barostat_name} is not supported")
else:
    raise ValueError(f"Unsupported ensemble {ensemble}. Choices: NVE, NVT, NPT")


### tailor properties
def print_dynamic(atoms, filename="calc_dyn_properties.txt"):
    """Function to print the potential, kinetic and total energy.
    Note: Stress printed in this file in GPa, but save in EXTXYZ in eV/Angstrom^3.
    """
    ### Extract properties
    step = dyn.nsteps
    epot = atoms.get_potential_energy() / len(atoms)
    ekin = atoms.get_kinetic_energy() / len(atoms)
    temp = atoms.get_temperature()
    stress = atoms.get_stress() / units.GPa  # 6_vector in Voigt notation
    cellpar = atoms.cell.cellpar()
    ### Write the header line
    if not Path(filename).exists():
        with paropen(filename, "w") as f:
            f.write("step temperature epot ekin pxx pyy pzz lx ly lz\n")
    ### Append the data to the file
    with paropen(filename, "a") as f:
        f.write(
            f"{step} {temp:.1f} {epot:.8f} {ekin:.8f} {stress[0]:.8f} {stress[1]:.8f} {stress[2]:.8f} {cellpar[0]:.7f} {cellpar[1]:.7f} {cellpar[2]:.7f}\n"
        )


### Traj in eXYZ format
def write_dyn_extxyz(atoms, filename="traj_label.extxyz"):
    # write("test_Cu.exyz", a, format="extxyz", append=True)
    _ = (
        atoms.get_potential_energy()
    )  # `force_consistent=True` cause error if combine multi-calculators
    _ = atoms.get_forces()
    _ = atoms.get_stress()
    atoms.info["pbc"] = atoms.get_pbc()
    write(filename, atoms, format="extxyz", append=True)


### Save ASE trajectory
# traj = Trajectory("CONF.asetraj", "w", atoms, properties=["energy", "forces", "stress"])
# dyn.attach(traj.write, interval=traj_freq)

parprint(f"INFO: Start MD with ensemble {ensemble}: {dyn.__class__.__name__}")
Path("calc_dyn_properties.txt").unlink(missing_ok=True)
Path("traj_label.extxyz").unlink(missing_ok=True)
### run MD
equil_steps = md_args.get("equil_steps", 0)
if equil_steps > 0:
    dyn.run(equil_steps)
    parprint(f"INFO: Finish {dyn.nsteps} steps of equilibration run.")

num_frames = md_args.get("num_frames", 1)
traj_freq = md_args.get("traj_freq", 1)
nsteps = num_frames * traj_freq

### Attach functions to the MD loop
if calc_args.get("exclude_result_dftd3", False) and dftd3_args:
    struct = atoms.copy()
    struct.calc = SinglePointCalculator(struct)
    struct.calc.results = calc_pw.results  # only PW-calculator results (no DFTD3)
    dyn.attach(lambda: print_dynamic(struct), interval=traj_freq)
    dyn.attach(lambda: write_dyn_extxyz(struct), interval=traj_freq)
else:
    dyn.attach(lambda: print_dynamic(atoms), interval=traj_freq)
    dyn.attach(lambda: write_dyn_extxyz(atoms), interval=traj_freq)

dyn.run(nsteps)

parprint(
    f"INFO: Finish {dyn.nsteps} steps of product run, to collect {num_frames} frames with {traj_freq} steps interval."
)
