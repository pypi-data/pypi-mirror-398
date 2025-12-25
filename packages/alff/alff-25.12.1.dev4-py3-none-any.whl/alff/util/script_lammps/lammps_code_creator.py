import random
from copy import deepcopy
from typing import Literal

from ase import units as ase_units

from thkit.io import list2txt
from thkit.stuff import simple_uuid


#####ANCHOR lammps script for singlepoint calculation
def generate_script_lammps_singlepoint(
    units: str = "metal",
    atom_style: str = "atomic",
    dimension: int = 3,
    pbc: list = [1, 1, 1],
    read_data: str = "path_to_file.lmpdata",
    read_restart: str | None = None,
    pair_style: list[str] | None = None,
    pair_coeff: list[str] | None = None,
    output_script: str = "cli_script_lammps.lmp",
    **kwargs,
):
    """Generate lammps script for single-point calculation.

    Args:
        units (str): Units for lammps. Default "metal"
        atom_style (str): Atom style of system. Default "atomic"
        dimension (int): Dimension of system. Default 3
        pbc (list): Periodic boundary conditions. Default [1, 1, 1]
        read_data (str): Path to the data file. e.g. "path_to_lmpdata"
        read_restart (str): Path to the restart file. e.g. "path_to_restart". If provided, `read_restart` is used instead of `read_data`.
        pair_style (list[str] | None): List of pair_style, e.g., ["eam/alloy"]. Default is None
        pair_coeff (list[str] | None): List of pair_coeff,e.g., ["* * Cu.eam.alloy Cu"]. Default is None
        output_script (str): Path to the output script. Default "cli_script_lammps.in"
        **kwargs: Any other arguments which may be ignored.
    """
    args = deepcopy(locals())
    args.update(**kwargs)
    lines = lmp_section_atom_forcefield(**args)
    lines += lmp_section_common_setting(**args)
    lines += _lmp_section_run0()[0]
    list2txt(lines, output_script)
    return


#####ANCHOR lammps script for minimization
def generate_script_lammps_minimize(
    units: str = "metal",
    atom_style: str = "atomic",
    dimension: int = 3,
    pbc: list = [1, 1, 1],
    read_data: str = "path_to_file.lmpdata",
    read_restart: str | None = None,
    pair_style: list[str] | None = None,
    pair_coeff: list[str] | None = None,
    ### for minimize
    min_style: str = "cg",
    etol: float = 1.0e-9,
    ftol: float = 1.0e-9,
    maxiter: int = 100000,
    maxeval: int = 100000,
    dmax: float = 0.01,
    ### control pressure
    press: list[int] | float | bool = [None, None, None],  # type: ignore
    mask: list[int] = [1, 1, 1],
    couple: str = "none",
    output_script: str = "cli_script_lammps.lmp",
    **kwargs,
):
    """Generate lammps script for minimization.

    Args:
        etol (float): Energy tolerance for minimization. Default 1.0e-9
        ftol (float): Force tolerance for minimization. Default 1.0e-9
        maxiter (int): Maximum number of iterations. Default 100000
        maxeval (int): Maximum number of evaluations. Default 100000
        dmax (float): maximum distance for line search to move (distance units). Default: 0.01

        press (Union[list[int], float, bool]): float/1x3 list of Pressure values in GPa. If a single value is provided, it is applied to all directions.
        mask (list[int]): 3x1 list of Mask for pressure. Default [1, 1, 1]. Mask to more control which directions is allowed to relax.
        couple (str): "none", xyz, xy, yz, xz. Default "none"
        output_script (str): Path to the output script. Default "cli_script_lammps.in"

    Note: For control pressure
        - Only control pressure in the periodic directions.
        - If single value is given, it is assumed to be the pressure in all directions.
        - If three values are given, they are assumed to be the pressure in x, y, and z directions, respectively.
        - `**kwargs`, to accept unused arguments, **any other arguments which may be ignored.**
    """
    args = deepcopy(locals())
    args.update(**kwargs)
    args["press"] = _revise_input_pressure(press, pbc, mask, units)

    lines = lmp_section_atom_forcefield(**args)
    lines += lmp_section_common_setting(**args)
    tmp_lines, tmp_fixes = lmp_section_minimize(**args)
    lines += tmp_lines
    lines += _lmp_section_unfix(tmp_fixes, [])
    lines += _lmp_section_run0()[0]
    list2txt(lines, output_script)
    return


#####ANCHOR lammps script for MD simulation
### note: Do not use `dataclass`, it is over-complicated


def generate_script_lammps_md(
    units: str = "metal",
    atom_style: str = "atomic",
    dimension: int = 3,
    pbc: list = [1, 1, 1],
    read_data: str = "path_to_file.lmpdata",
    read_restart: str | None = None,
    pair_style: list[str] | None = None,
    pair_coeff: list[str] | None = None,
    ### for MD
    ensemble: Literal["NVE", "NVT", "NPT"] = "NVE",
    dt: float = 0.001,  # 0.001 ps = 1 fs if unit metal, 1 fs if unit real
    num_frames: int = 0,
    traj_freq: int = 1,
    equil_steps: int = 0,
    plumed_file: str | None = None,
    thermo_freq: int = 5000,
    first_minimize: bool = False,
    ### temperature control
    temp: float = 300,
    tdamp: int = 100,
    thermostat: Literal["nose_hoover_chain", "langevin"] = "nose_hoover_chain",
    ### pressure control
    press: float | list[float] | None = None,  # can be [None, None, None]
    mask: list[int] = [1, 1, 1],
    couple: str = "none",  # "none", xyz, xy, yz, xz
    pdamp: int = 1000,
    barostat: Literal["nose_hoover_chain"] = "nose_hoover_chain",
    deform_limit: float | None = None,
    output_script: str = "cli_script_lammps.lmp",
    **kwargs,
):
    """Generate lammps script for MD simulation.

    Args:
        first_minimize (bool): Whether to perform a first minimization before MD simulation. Default False
        ensemble (Literal["NVE", "NVT", "NPT"]): Ensemble for MD simulation. Default "NVE"
        dt (float): Time step for MD simulation. Default 0.001 ps = 1 fs if unit metal, 1 fs if unit real
        traj_freq (int): Frequency to dump trajectory. Default 1
        num_frames (int): number of frames to be collected. Then total MD nsteps = (num_frames * traj_freq)
        equil_steps (int): Number of steps for first equilibration. Default 0
        plumed_file (str): Path to the plumed file. Default None
        thermo_freq (int): Frequency to print thermo. Default 5000
        temp (float): Temperature for MD simulation. Default 300
        tdamp (int): Damping time for thermostat. Default 100
        thermostat (Literal["nose_hoover_chain", "langevin"]): Thermostat for MD simulation. Default "nose_hoover_chain"

        press (Union[list[int], float, bool]): float/1x3 list of Pressure values. If a single value is provided, it is applied to all directions.
        mask (list[int]): 3x1 list of Mask for pressure. Default [1, 1, 1]. Mask to more control which directions is allowed to relax.
        couple (str): "none", xyz, xy, yz, xz. Default "none"
        pdamp (int): Damping time for barostat. Default 1000
        barostat (Literal["nose_hoover_chain"]): Barostat for MD simulation. Default "nose_hoover_chain"
        deform_limit (Optional[float]): Maximum **fractional change** allowed for any box dimension. The simulation stops if $abs(L - L0) / L0 > deform_limit$ in any of x, y, or z dim.
        output_script (str): Path to the output script. Default "cli_script_lammps.in"

    Note: For control pressure
        - Only control pressure in the periodic directions.
        - If single value is given, it is assumed to be the pressure in all directions.
        - If three values are given, they are assumed to be the pressure in x, y, and z directions, respectively.
    """
    ### Revise inputs
    press = _revise_input_pressure(press, pbc, mask, units)
    args = deepcopy(locals())
    args.update(**kwargs)
    args["press"] = press

    lines = lmp_section_atom_forcefield(**args)
    lines += lmp_section_common_setting(**args)
    ### First minimization
    if first_minimize:
        tmp_lines, tmp_fixes = lmp_section_minimize(etol=1.0e-6, ftol=1.0e-6, **args)
        lines += tmp_lines
        lines += _lmp_section_unfix(tmp_fixes, [])
    lines += lmp_section_dynamic_setting(**args)
    ### MD run
    equil_args = deepcopy(args)
    equil_args.update(
        {"num_frames": 1, "traj_freq": equil_steps, "plumed_file": None, "dump_result": False}
    )
    args.update({"dump_result": True})
    if ensemble == "NVE":
        if equil_steps > 0:
            tmp_lines, tmp_fixes, tmp_dumps = lmp_section_nve(**equil_args)
            lines += tmp_lines
            lines += _lmp_section_unfix(tmp_fixes, tmp_dumps)
        tmp_lines, tmp_fixes, tmp_dumps = lmp_section_nve(**args)
        lines += tmp_lines
        lines += _lmp_section_unfix(tmp_fixes, tmp_dumps)
    elif ensemble == "NVT":
        if equil_steps > 0:
            tmp_lines, tmp_fixes, tmp_dumps = lmp_section_nvt(**equil_args)
            lines += tmp_lines
            lines += _lmp_section_unfix(tmp_fixes, tmp_dumps)
        tmp_lines, tmp_fixes, tmp_dumps = lmp_section_nvt(**args)
        lines += tmp_lines
        lines += _lmp_section_unfix(tmp_fixes, tmp_dumps)
    elif ensemble == "NPT":
        if equil_steps > 0:
            tmp_lines, tmp_fixes, tmp_dumps = lmp_section_npt(**equil_args)
            lines += tmp_lines
            lines += _lmp_section_unfix(tmp_fixes, tmp_dumps)
        tmp_lines, tmp_fixes, tmp_dumps = lmp_section_npt(**args)
        lines += tmp_lines
        lines += _lmp_section_unfix(tmp_fixes, tmp_dumps)
    else:
        raise ValueError("Invalid ensemble, only support 'nve', 'nvt', 'npt'")

    list2txt(lines, output_script)
    return


#####SECTION Lammps sections
def lmp_section_atom_forcefield(
    units: str = "metal",
    atom_style: str = "atomic",
    dimension: int = 3,
    pbc: list = [1, 1, 1],
    read_data: str = "path_to_file.lmpdata",
    read_restart: str | None = None,
    pair_style: list[str] | None = None,
    pair_coeff: list[str] | None = None,
    **kwargs,
) -> list[str]:
    """Generate lammps input block for atom and forcefield.

    Args:
        read_data (str): Path to the data file. e.g. "path_to_lmpdata"
        read_restart (str): Path to the restart file. e.g. "path_to_restart". If provided, `read_restart` is used instead of `read_data`.
        pair_style (list[str]): List of pair_style, e.g., ["eam/alloy"]. Default is None
        pair_coeff (list[str]): List of pair_coeff,e.g., ["* * Cu.eam.alloy Cu"]. Default is None
    """
    pbc_str = _pbc_string(pbc)  # convert pbc list to string
    lines = [
        f"units         {units}",
        f"atom_style    {atom_style}",
        f"dimension     {dimension}",
        f"boundary      {pbc_str}\n",
    ]

    if read_data:
        lines.append(f"read_data     {read_data}")
    elif read_restart:
        lines.append(f"read_restart  {read_restart}")

    if pair_style is not None:
        lines.extend([f"pair_style    {style}" for style in pair_style])
    if pair_coeff is not None:
        lines.extend([f"pair_coeff    {coeff}" for coeff in pair_coeff])

    lines = [f"  {line}" for line in lines]  ## add indentation
    lines.insert(0, "\n#####ANCHOR ATOMS & FORCEFIELD")
    return lines


def lmp_section_common_setting(extra_settings: list | None = None, **kwargs) -> list[str]:
    """Generate lammps input block for common settings.

    Args:
        extra_settings (list[str] | None): List of extra settings to be added. Default None.

    Notes:
        - The `fix balance` requires setting `pair_coeff` before it.
    """
    lines = [
        "variable      PXX     equal   pxx",
        "variable 	    PYY     equal 	pyy",
        "variable 	    PZZ     equal 	pzz",
        "variable 	    PYZ     equal 	pyz",
        "variable 	    PXZ     equal 	pxz",
        "variable 	    PXY     equal 	pxy",
        "variable 	    LX      equal 	lx",
        "variable 	    LY      equal 	ly",
        "variable 	    LZ      equal 	lz",
        "variable 	    TEMP    equal 	temp",
        "variable 	    PE      equal 	pe",
        "variable 	    KE      equal 	ke\n",
    ]
    if extra_settings is not None:
        lines += ["### Extra settings"]
        lines.extend(extra_settings)

    lines += [
        "balance       1.0 shift xyz 20 1.0",
        "fix     fbala all balance 20000 1.0 shift xyz 20 1.0",
    ]

    lines = [f"  {line}" for line in lines]  ## add indentation
    lines.insert(0, "\n#####ANCHOR COMMON SETUP")
    return lines


def lmp_section_minimize(
    min_style: str = "cg",
    etol: float = 1.0e-9,
    ftol: float = 1.0e-9,
    maxiter: int = 100000,
    maxeval: int = 100000,
    dmax: float = 0.01,
    press: list = [None, None, None],
    couple: str = "none",  # "none", xyz, xy, yz, xz
    uid: str | None = None,
    **kwargs,
) -> list[str]:
    """Generate lammps input block for minimization."""
    uid = simple_uuid() if not uid else uid
    press_str = _press_string_minimize(press)
    lines, fixes = [], []
    if press_str:
        lines.append(f"fix 	  f_{uid} all box/relax {press_str} couple {couple}")
        fixes.append(f"f_{uid}")
    lines += [
        f"min_style     {min_style}",
        f"min_modify    dmax {dmax} line quadratic",
        f"minimize      {etol} {ftol} {maxiter} {maxeval}",
    ]

    lines = [f"  {line}" for line in lines]  ## add indentation
    lines.insert(0, "\n#####ANCHOR MINIMIZATION")
    return lines, fixes


def lmp_section_dynamic_setting(
    dt: float,
    temp: float,
    thermo_freq: int = 5000,
    **kwargs,
) -> list[str]:
    rnd = random.randint(10000, 99999)
    temp = float(temp)
    lines = [
        "thermo_style  custom step temp pe lx ly lz pxx pyy pzz",
        f"thermo        {thermo_freq}\n",
        f"variable      dt equal {dt}",
        f"timestep      {dt}",
        f"velocity      all create {temp} {rnd} rot yes dist uniform",
        # "run            0",
        # f"velocity      all scale {temp}",
    ]

    lines = [f"  {line}" for line in lines]  ## add indentation
    lines.insert(0, "\n#####ANCHOR DYMAMIC SETUP")
    return lines


def lmp_section_nve(
    num_frames: int = 0,
    traj_freq: int = 1,
    plumed_file: str | None = None,
    dump_result: bool = False,
    uid: str | None = None,
    **kwargs,
) -> tuple[list[str]]:
    uid = simple_uuid() if not uid else uid
    nsteps = num_frames * traj_freq
    ### define lines
    lines, fixes, dumps = [], [], []
    if plumed_file:
        lines.append(f"fix     fplu_{uid}  all plumed {plumed_file} outfile log_plumed_{uid}.txt")
        fixes.append(f"fplu_{uid}")

    lines.append(f"fix     f_{uid}  all nve")
    fixes.append(f"f_{uid}")

    if dump_result:
        tmp_lines, tmp_fixes, tmp_dumps = _lmp_section_dump(traj_freq, uid)
        lines.extend(tmp_lines)
        fixes.extend(tmp_fixes)
        dumps.extend(tmp_dumps)
    lines.append(f"run     {nsteps}")

    lines = [f"  {line}" for line in lines]  ## add indentation
    lines.insert(0, "\n#####ANCHOR EQUIBIRUM NVE")
    return lines, fixes, dumps


def lmp_section_nvt(
    num_frames: int = 0,
    traj_freq: int = 1,
    temp: float = 300,
    tdamp: int = 100,  # unit number_steps
    thermostat: str = "nose_hoover_chain",
    ###
    plumed_file: str | None = None,
    dump_result: bool = False,
    uid: str | None = None,
    **kwargs,
) -> list[str]:
    uid = simple_uuid() if not uid else uid
    rnd = random.randint(10000, 99999)
    nsteps = num_frames * traj_freq
    temp = float(temp)
    ### define lines
    lines, fixes, dumps = [], [], []
    if plumed_file:
        lines.append(f"fix     fplu_{uid}  all plumed {plumed_file} outfile log_plumed_{uid}.txt")
        fixes.append(f"fplu_{uid}")

    if thermostat == "nose_hoover_chain":
        lines.append(f"fix     f_{uid}  all nvt temp {temp} {temp} $({tdamp}*v_dt)")
        fixes.append(f"f_{uid}")
    elif thermostat == "langevin":
        lines += [
            f"fix     f_{uid}  all langevin {temp} {temp} $({tdamp}*v_dt) {rnd}",
            f"fix     f2_{uid} all nve",
        ]
        fixes += [f"f_{uid}", f"f2_{uid}"]

    if dump_result:
        tmp_lines, tmp_fixes, tmp_dumps = _lmp_section_dump(traj_freq, uid)
        lines.extend(tmp_lines)
        fixes.extend(tmp_fixes)
        dumps.extend(tmp_dumps)
    lines.append(f"run     {nsteps}")

    lines = [f"  {line}" for line in lines]  ## add indentation
    lines.insert(0, "\n#####ANCHOR EQUIBIRUM NVT")
    return lines, fixes, dumps


def lmp_section_npt(
    num_frames: int = 0,
    traj_freq: int = 1,
    temp: float = 300,
    tdamp: int = 100,
    thermostat: str = "nose_hoover_chain",
    press: list = [0, 0, 0],
    pdamp: int = 1000,
    barostat: str = "nose_hoover_chain",
    mask: list[int] = [1, 1, 1],
    couple: str = "none",
    ###
    plumed_file: str | None = None,
    dump_result: bool | None = False,
    deform_limit: float | None = None,
    uid: str | None = None,
    **kwargs,
) -> list[str]:
    """Generate lammps input block for NPT simulation.
    Support tracking box expension during NPT simulation.
    The simulation stops if $abs(L - L0) / L0 > deform_limit$ in any of x, y, or z.
    """
    uid = simple_uuid() if not uid else uid
    rnd = random.randint(10000, 99999)
    nsteps = num_frames * traj_freq
    temp = float(temp)
    press_str = _press_string_md(press, pdamp)
    ### define lines
    lines, fixes, dumps = [], [], []
    if plumed_file is not None:
        lines.append(f"fix     fplu_{uid}  all plumed {plumed_file} outfile log_plumed_{uid}.txt")
        fixes.append(f"fplu_{uid}")

    if barostat == "nose_hoover_chain":
        if thermostat == "nose_hoover_chain":
            lines.append(
                f"fix     f_{uid}  all npt temp {temp} {temp} $({tdamp}*v_dt) {press_str} couple {couple}"
            )
            fixes.append(f"f_{uid}")
        elif thermostat == "langevin":
            lines += [
                f"fix     f_{uid}  all langevin {temp} {temp} $({tdamp}*v_dt) {rnd}",
                f"fix     f2_{uid} all nph {press_str} couple {couple}",
            ]
            fixes += [f"f_{uid}", f"f2_{uid}"]

    if dump_result:
        tmp_lines, tmp_fixes, tmp_dumps = _lmp_section_dump(traj_freq, uid)
        lines.extend(tmp_lines)
        fixes.extend(tmp_fixes)
        dumps.extend(tmp_dumps)

    if deform_limit is not None:
        tmp_lines = [
            "variable 	    LX0      equal 	${LX}",
            "variable 	    LY0      equal 	${LY}",
            "variable 	    LZ0      equal 	${LZ}",
            f'variable      ISSTOP   equal  "(abs(v_LX-v_LX0)/v_LX0 >{deform_limit}) || (abs(v_LY-v_LY0)/v_LY0 >{deform_limit}) || (abs(v_LZ-v_LZ0)/v_LZ0 >{deform_limit})"',
            f"fix     fstop_{uid} all halt $(ceil(5*{pdamp}*v_dt)) v_ISSTOP == 1 error hard message yes",
        ]
        lines.extend(tmp_lines)
        fixes.append(f"fstop_{uid}")

    lines.append(f"run     {nsteps}")

    lines = [f"  {line}" for line in lines]  ## add indentation
    lines.insert(0, "\n#####ANCHOR EQUIBIRUM NPT")
    return lines, fixes, dumps


def lmp_section_nph():
    lines = []

    lines = [f"  {line}" for line in lines]  ## add indentation
    lines.insert(0, "\n#####ANCHOR EQUIBIRUM NPH")
    return lines


#####ANCHOR helper functions
def _lmp_section_dump(traj_freq: int, uid: str = None, single_frame=False) -> tuple[list[str]]:
    uid = simple_uuid() if not uid else uid
    prefix = "frame" if single_frame else "traj_md"
    lines = [
        "### Output",
        f"fix     fprt_{uid} all ave/time 1 1 {traj_freq} v_PXX v_PYY v_PZZ v_PYZ v_PXZ v_PXY v_LX v_LY v_LZ v_TEMP v_PE v_KE &",
        f"        title1 'time pxx pyy pzz pyz pxz pxy lx ly lz temp pe ke' title2 '#' file {prefix}_label_stress_value.txt",
        f"dump    d_{uid} all custom {traj_freq} {prefix}_label.lmpdump id type mass xu yu zu fx fy fz",
        f"dump_modify d_{uid} sort id \n",
    ]
    fixes = [f"fprt_{uid}"]
    dumps = [f"d_{uid}"]
    return lines, fixes, dumps


def _lmp_section_run0(uid: str = None) -> tuple[list[str]]:
    lines, fixes, dumps = _lmp_section_dump(1, uid, single_frame=True)
    lines.append("run     0")

    lines = [f"  {line}" for line in lines]  ## add indentation
    return lines, fixes, dumps


def _lmp_section_unfix(fixes: list[str] = [], dumps: list[str] = []) -> list[str]:
    lines = []
    if fixes:
        lines += [f"  unfix   {fix}" for fix in fixes]
    if dumps:
        lines += [f"  undump  {dump}" for dump in dumps]
    return lines


def _pbc_string(pbc: list = [1, 1, 1]) -> str:
    """Convert pbc list to string. Acceptable values: 1, 0, p, f, s, m.

    [1, 1, 0] -> "p p f". See https://docs.lammps.org/boundary.html
    """
    pbc_map = {1: "p", 0: "f", "p": "p", "f": "f", "s": "s", "m": "m"}
    pbc = [pbc_map[v] for v in pbc]
    return " ".join(pbc)


def _revise_input_pressure(
    press: list[int] | float | bool,
    pbc: list = [1, 1, 1],
    mask: list = [1, 1, 1],
    units: str = "metal",
) -> list:
    """Revise pressure string based on pbc and mask. This allows more flexible control of pressure setting, fllowing that:
        - Pressures only applied to the directions with pbc=1 and mask=1, regardless input press.
        - If press is a single value, this value is used to all directions.
        - Convert pressure unit from GPa to lammps unit based on choosen units (e.g. `metal`, `real`).

    Args:
        press (Union[list[int], float, bool]): float/1x3 list of Pressure values in GPa. If a single value is provided, it is applied to all directions.
        pbc (list[int]): 3x1 list of Periodic boundary conditions. Default [1, 1, 1]
        mask (list[int]): 3x1 list of Mask for pressure. Default [1, 1, 1]. Mask to more control which directions is allowed to relax.
        units (str): Lammps units. Default "metal"
    """
    if not isinstance(press, list):
        press = [press] * 3

    if units == "metal":
        press = [p * ase_units.GPa / ase_units.bar for p in press if p is not None]
    elif units == "real":
        press = [p * ase_units.GPa / ase_units.atm for p in press if p is not None]
    else:
        raise ValueError(f"Unknown Lammps unit: {units}")

    revise_mask = [1 if (bc == 1 and m == 1) else 0 for bc, m in zip(pbc, mask)]
    press = [p if m == 1 else None for m, p in zip(revise_mask, press)]
    return press


def _press_string_minimize(press: list = [0.0, 0.0, 0.0]) -> str:
    """Convert pressure list to lammps-style string.

    Example:
    - [0.0, 0.0, 0.0] -> 'x 0.0 y 0.0 z 0.0'
    - [None, 0.0, 0.0] -> 'y 0.0 z 0.0'
    - [None, None, None] -> ''
    """
    if all(p is None for p in press):
        text = ""
    else:
        press_str = [f"{dim} {p}" for dim, p in zip(["x", "y", "z"], press) if p is not None]
        text = " ".join(press_str)
    return text


def _press_string_md(press: list = [0.0, 0.0, 0.0], pdamp: int = 1000) -> str:
    """Convert pressure list to lammps-style string.

    Example:
    - [0.0, 0.0, 0.0] -> 'x 0.0 y 0.0 z 0.0'
    - [None, 0.0, 0.0] -> 'y 0.0 z 0.0'
    - [None, None, None] -> error
    """
    if all(p is None for p in press):
        raise ValueError("Must provide pressure for at least one direction to run NPT simulation.")
    else:
        press_str = [
            f"{dim} {p} {p} $({pdamp}*v_dt)"
            for dim, p in zip(["x", "y", "z"], press)
            if p is not None
        ]
        text = " ".join(press_str)
    return text


def process_lammps_argdict(argdict: dict) -> dict:
    """LAMMPS argdict must be defined as a dictionary with 4 'top-level' keys: `structure`, `optimize`, `md`, `extra`.
    That form requirement is to be validated using [LAMMPS args schema](https://thangckt.github.io/alff_doc/schema/config_lammps/).

    However, when generating lammps script, we only need the 'sub-level' keys. So, this function is to remove 'top-level' keys, and return 'sub-level' keys only to be used generate lammps script functions.

    Args:
        argdict (dict): Dictionary of dicts of lammps arguments.

    Returns:
        dict: Processed lammps arguments.
    """
    new_dict = {}
    for top_key, sub_dict in argdict.items():
        if isinstance(sub_dict, dict):
            new_dict.update(sub_dict)
        else:
            raise ValueError(f"Top-level key '{top_key}' does not map to a dictionary")
    return new_dict


##### SECTION
