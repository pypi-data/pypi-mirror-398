"""Utility functions for phonon calculations.

Notes:
    - Phonon calculations rely on a structure that is tightly converged. It is recommended to run a pre-relaxation with `opt_params: {"fmax": 1e-3}` or tighter before running phonon calculations.
    - [Notice about displacement distance: "A too small displacement distance can lead to numerical noise, while a too large displacement distance can lead to anharmonic effects. A typical value is 0.01-0.05 Angstrom.", But, [some notes](https://www.diracs-student.blog/2023/11/unoffical-way-to-use-phonopy-with-ase.html) say 0.05-0.08 Angstroms are need to converge!

Info:
    - [1] https://phonopy.github.io/phonopy/
    - [2] https://github.com/abelcarreras/phonolammps
    - [3] https://github.com/lrgresearch/gpaw-tools
    - [4] calorine: https://gitlab.com/materials-modeling/calorine/-/blob/master/calorine/tools/phonons.py?ref_type=heads
    - [5] quacc: https://github.com/Quantum-Accelerators/quacc/blob/main/src/quacc/atoms/phonons.py
    - [6] pymatgen: https://github.com/materialsproject/pymatgen/blob/master/src/pymatgen/io/phonopy.py
    - [7] vibes: https://gitlab.com/vibes-developers/vibes/-/tree/master/vibes/phonopy
    - [8] https://www.diracs-student.blog/2023/11/unoffical-way-to-use-phonopy-with-ase.html
"""

import matplotlib as mpl
import numpy as np
import phonopy
from ase import Atoms
from phonopy.phonon.band_structure import get_band_qpoints_and_path_connections
from phonopy.structure.atoms import PhonopyAtoms
from phonopy.structure.cells import get_primitive, guess_primitive_matrix

from alff.base import KEY as K

### Set global figure size and dpi
# mpl.rcParams.update({"figure.figsize": (3.4, 2.7), "figure.dpi": 300})
mpl.rcParams.update({"figure.figsize": (5, 4), "figure.dpi": 150})


#####SECTION: Structure tools
#####ANCHOR Convert struct ASE to Phonopy
### 1. gpawtools: https://github.com/sblisesivdin/gpaw-tools/blob/main/gpawsolve.py#L1786
### 2. Calorine: https://gitlab.com/materials-modeling/calorine/-/blob/master/calorine/tools/structures.py?ref_type=heads
def convert_phonopy2ase(struct_ph: PhonopyAtoms) -> Atoms:
    struct = Atoms(
        symbols=struct_ph.get_chemical_symbols(),  # type: ignore
        scaled_positions=struct_ph.get_scaled_positions(),  # type: ignore
        cell=struct_ph.get_cell(),  # type: ignore
        pbc=True,
        masses=struct_ph.get_masses(),  # type: ignore
    )
    return struct


def convert_ase2phonopy(struct: Atoms) -> PhonopyAtoms:
    struct_ph = PhonopyAtoms(
        symbols=struct.get_chemical_symbols(),
        scaled_positions=struct.get_scaled_positions(),
        cell=struct.get_cell(),
        pbc=True,
        masses=struct.get_masses(),
    )
    return struct_ph


#####ANCHOR Primitive cell
### 1. https://gitlab.com/materials-modeling/calorine/-/blob/master/calorine/tools/structures.py?ref_type=heads#L118


def get_primitive_spglib(
    struct: Atoms,
    no_idealize: bool = True,
    symprec=1e-5,
    angle_tolerance=-1.0,
) -> Atoms:
    """Find the primitive cell using spglib.standardize_cell.

    Args:
        struct (Atoms): ASE's structure object.
        no_idealize (bool): Whether to avoid idealizing the cell shape (lengths and angles). Default is True.
        symprec (float): Symmetry tolerance. Default is 1e-5.
        angle_tolerance (float): Angle tolerance. Default is -1.0 (i.e., use spglib's default).

    Note:
        - IMPORTANT: Using this function in phonon calculations is unstable. Use with caution.
            - Since `spglib.find_primitive` may fail to find the primitive cell for some structures.
            - Or the returned primitive cell may not has right symmetry. This can lead to issues in phonon calculations (e.g., negative frequencies).
        - Must use `.get_scaled_positions()` to define the cell in `spglib`.
    """
    from spglib.spglib import standardize_cell

    ### find primitive cell
    cell_tuple = (struct.cell, struct.get_scaled_positions(), struct.numbers)
    prim_cell = standardize_cell(
        cell_tuple,  # type: ignore
        to_primitive=True,
        no_idealize=no_idealize,
        symprec=symprec,
        angle_tolerance=angle_tolerance,
    )
    if prim_cell is None:
        raise RuntimeError("Failed to find primitive cell.")

    ### convert back to ASE Atoms object
    lattice, scaled_positions, numbers = prim_cell  # type: ignore
    prim_struct = Atoms(
        cell=lattice,
        scaled_positions=scaled_positions,
        numbers=numbers,
        pbc=struct.pbc,
    )

    print(
        f"Find primitive: \n\tInput struct: {len(struct)} atoms. \n\tPrimitive: {len(prim_struct)} atoms."
    )
    return prim_struct


def get_primitive_phonopy(struct: Atoms, symprec=1e-5) -> Atoms:
    """Find the primitive cell using phonopy's get_primitive() function. This is more robust than `spglib`.

    Args:
        struct (Atoms): ASE's structure object.
        symprec (float): Symmetry tolerance. Default is 1e-5.
    """
    struct_ph = convert_ase2phonopy(struct)
    primitive_matrix = guess_primitive_matrix(struct_ph, symprec)
    primitive = get_primitive(struct_ph, primitive_matrix=primitive_matrix, symprec=symprec)
    prim_struct = convert_phonopy2ase(primitive)
    print(
        f"Find primitive: \n\tInput struct: {len(struct)} atoms. \n\tPrimitive: {len(prim_struct)} atoms."
    )
    return prim_struct


#####!SECTION


#####ANCHOR Supporting functions
def get_band_path(
    atoms: Atoms,
    path_str: str = "",
    npoints: int = 61,
    path_frac=None,
    labels=None,
):
    ### ref: https://github.com/lrgresearch/gpaw-tools/blob/main/gpawsolve.py#L1462
    from ase.dft.kpoints import bandpath

    if path_str == "":
        path_str = atoms.get_cell().bandpath().path

    # Commas are part of ase's supported syntax, but we'll take care of them
    # ourselves to make it easier to get things the way phonopy wants them
    if path_frac is None:
        path_frac = []
        for substr in path_str.split(","):
            path = bandpath(substr, atoms.get_cell()[...], npoints=1)  # type: ignore
            path_frac.append(path.kpts)

    if labels is None:
        labels = []
        for substr in path_str.split(","):
            path = bandpath(substr, atoms.get_cell()[...], npoints=1)  # type: ignore
            _, _, substr_labels = path.get_linear_kpoint_axis()
            labels.extend(["$\\Gamma$" if s == "G" else s for s in substr_labels])

    qpoints, connections = get_band_qpoints_and_path_connections(path_frac, npoints=npoints)
    return qpoints, labels, connections


#####ANCHOR Compute properties from phonon object
def get_band_structure(work_dir, pdict):
    ### REF vibes: https://gitlab.com/vibes-developers/vibes/-/blob/master/vibes/phonopy/wrapper.py?ref_type=heads

    compute_arg = pdict["phonon"].get("compute", {})
    band_structure_arg = compute_arg.get("band_structure", {})
    path_str = band_structure_arg.get("path_str", "")
    npoints = band_structure_arg.get("npoints", 61)

    ### Read phonon file
    phonon = phonopy.load(f"{work_dir}/{K.FILE_PHONOPYwFORCES}")

    if path_str == "auto":
        phonon.auto_band_structure(npoints=npoints)
    else:
        atoms = convert_phonopy2ase(phonon.primitive)
        qpoints, labels, connections = get_band_path(atoms, path_str, npoints)
        phonon.run_band_structure(qpoints, path_connections=connections, labels=labels)

    ### plot band structure
    phonon.write_yaml_band_structure(filename=f"{work_dir}/band_structure.yml")
    plt = phonon.plot_band_structure()
    # plt.tight_layout()
    plt.savefig(f"{work_dir}/band_structure.pdf", dpi=300)
    # plt.show()
    return


def get_DOS_n_PDOS(work_dir, pdict):
    compute_arg = pdict["phonon"].get("compute", {})
    mesh = compute_arg.get("mesh", [20, 20, 20])

    phonon = phonopy.load(f"{work_dir}/{K.FILE_PHONOPYwFORCES}")
    # phonon.auto_band_structure()
    if compute_arg.get("dos", False):
        phonon.run_mesh(mesh)
        phonon.run_total_dos()
        phonon.write_total_dos(filename=f"{work_dir}/total_dos.txt")
        plt = phonon.plot_total_dos()
        plt.tight_layout()
        plt.savefig(f"{work_dir}/total_dos.pdf", dpi=300)
        # plt = phonon.plot_band_structure_and_dos()
        # plt.tight_layout()
        # plt.savefig(f"{work_dir}/band_structure_and_dos.pdf", dpi=300)
    if compute_arg.get("pdos", False):
        phonon.run_mesh(mesh, with_eigenvectors=True, is_mesh_symmetry=False)
        phonon.run_projected_dos()
        phonon.write_projected_dos(filename=f"{work_dir}/projected_dos.txt")
        plt = phonon.plot_projected_dos()
        plt.tight_layout()
        plt.savefig(f"{work_dir}/projected_dos.pdf", dpi=300)
        # plt = phonon.plot_band_structure_and_dos(pdos_indices=[[0], [1]])
        # plt.tight_layout()
        # plt.savefig(f"{work_dir}/band_structure_and_pdos.pdf", dpi=300)
    return


def get_thermal_properties(work_dir, pdict):
    compute_arg = pdict["phonon"].get("compute", {})
    mesh = compute_arg.get("mesh", [20, 20, 20])
    thermal_arg = compute_arg.get("thermal_properties", {})
    t_min = thermal_arg.get("t_min", 0)
    t_max = thermal_arg.get("t_max", 1000)
    t_step = thermal_arg.get("t_step", 10)

    phonon = phonopy.load(f"{work_dir}/{K.FILE_PHONOPYwFORCES}")
    phonon.run_mesh(mesh)
    phonon.run_thermal_properties(t_min, t_max, t_step)

    ### Save text file
    tp_dict = phonon.get_thermal_properties_dict()
    temperatures = tp_dict["temperatures"]
    free_energy = tp_dict["free_energy"]
    entropy = tp_dict["entropy"]
    heat_capacity = tp_dict["heat_capacity"]

    arr = np.array([temperatures, free_energy, entropy, heat_capacity]).T
    np.savetxt(
        f"{work_dir}/thermal_properties.txt",
        arr,
        fmt="%.8f",
        header="temperatures free_energy entropy heat_capacity",
    )

    ### Plot
    plt = phonon.plot_thermal_properties()
    plt.tight_layout()
    plt.savefig(f"{work_dir}/thermal_properties.pdf", dpi=300)
    return
