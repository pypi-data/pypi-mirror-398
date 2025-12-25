"""Utility functions for PES scans and analysis."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ase import Atoms

import re
from pathlib import Path

import numpy as np
import polars as pl

from alff.base import KEY as K
from asext.io.readwrite import read_extxyz, write_extxyz


#####SECTION Helper functions
#####ANCHOR scanning
def scan_x_dim(struct_files: list, idxs: list, scan_dx_list: list):
    """Scan in the x dimension."""
    new_struct_files = struct_files.copy()
    for dx in scan_dx_list:
        for struct_file in struct_files:
            struct_list = read_extxyz(struct_file)
            struct_list_displaced = [
                displace_group_atoms_2d(struct, idxs, dx=dx) for struct in struct_list
            ]
            new_filename = f"{Path(struct_file).parent}_dx{dx}/{K.FILE_FRAME_UNLABEL}"
            write_extxyz(new_filename, struct_list_displaced)
            new_struct_files.append(new_filename)
    return new_struct_files


def scan_y_dim(struct_files: list, idxs: list, scan_dy_list: list):
    """Scan in the y dimension."""
    new_struct_files = struct_files.copy()
    for dy in scan_dy_list:
        for struct_file in struct_files:
            struct_list = read_extxyz(struct_file)
            struct_list_displaced = [
                displace_group_atoms_2d(struct, idxs, dy=dy) for struct in struct_list
            ]
            new_filename = f"{Path(struct_file).parent}_dy{dy}/{K.FILE_FRAME_UNLABEL}"
            write_extxyz(new_filename, struct_list_displaced)
            new_struct_files.append(new_filename)
    return new_struct_files


def scan_z_dim(struct_files: list, idxs: list, scan_dz_list: list):
    """Scan in the z dimension."""
    new_struct_files = struct_files.copy()
    for dz in scan_dz_list:
        for struct_file in struct_files:
            struct_list = read_extxyz(struct_file)
            struct_list_displaced = [
                displace_group_atoms_2d(struct, idxs, dz=dz) for struct in struct_list
            ]
            new_filename = f"{Path(struct_file).parent}_dz{dz}/{K.FILE_FRAME_UNLABEL}"
            write_extxyz(new_filename, struct_list_displaced)
            new_struct_files.append(new_filename)
    return new_struct_files


def displace_group_atoms_2d(
    struct: Atoms,
    idxs: list[int],
    dx: float = 0.0,
    dy: float = 0.0,
    dz: float = 0.0,
) -> Atoms:
    """Displace a selected group of atoms by (dx, dy, dz).

    Args:
        struct: ASE Atoms object.
        idxs: List of atom indices to displace.
        dx: Displacement in x direction (Å).
        dy: Displacement in y direction (Å).
        dz: Displacement in z direction (Å).

    Returns:
        A new Atoms with updated positions and cell (positions are NOT affinely scaled).

    Notes:
        - This function assumes the structure is 2D, and the cell is orthogonal in z direction.
        - After displacement, if any atom move outside the current boundaries, it will be wrapped to the cell.
        - The displacement of atoms may broke the periodicity at cell's boundaries. A minimization step
        is needed update the cell correctly.
    """
    idxs = sorted(set(idxs))
    assert len(idxs) > 0, "No atoms to displace. Please provide a list of atom indices."

    n = len(struct)
    if any(i < 0 or i >= n for i in idxs):
        raise IndexError("Some indices are out of range for this structure.")

    struct = struct.copy()

    ## Displace atoms
    disp = np.array([dx, dy, dz], dtype=float)
    positions = struct.get_positions()
    positions[idxs] += disp
    struct.set_positions(positions)

    ## Preserve the vacuum in z direction
    cell = struct.cell.array
    new_cell = cell.copy()
    new_cell[2, 2] += disp[2]  # only change the z length (preserving sign)
    struct.set_cell(new_cell, scale_atoms=False)

    ## wrap positions to the cell
    struct.wrap()
    return struct


#####ANCHOR filter atoms
def _filter_atoms(struct: Atoms, filters: dict) -> list[int]:
    """Get atom indices from structure based on filters (intersection of all filters).

    Args:
        struct (Atoms): ASE Atoms object.
        filters (dict): Supported keys:
            - "elements": list[str], e.g., ['Mg', 'O']
            - "above_mean_z": bool
            - "below_mean_z": bool
            - "min_z": float (keep atoms with z > min_z)
            - "max_z": float (keep atoms with z < max_z)

    Returns:
        list[int]: Atom indices satisfying all filters.

    Raises:
        ValueError: If no filters are provided, or no atoms match.
    """
    positions = struct.positions
    symbols = struct.get_chemical_symbols()

    filter_sets = []
    if "elements" in filters:
        elements = set(filters["elements"])
        filter_sets.append({i for i, ele in enumerate(symbols) if ele in elements})

    if filters.get("above_mean_z", False):
        mean_z = np.mean(positions[:, 2])
        filter_sets.append({i for i, pos in enumerate(positions) if pos[2] > mean_z})

    if filters.get("below_mean_z", False):
        mean_z = np.mean(positions[:, 2])
        filter_sets.append({i for i, pos in enumerate(positions) if pos[2] < mean_z})

    if "min_z" in filters:
        min_z = float(filters["min_z"])
        filter_sets.append({i for i, pos in enumerate(positions) if pos[2] > min_z})

    if "max_z" in filters:
        max_z = float(filters["max_z"])
        filter_sets.append({i for i, pos in enumerate(positions) if pos[2] < max_z})

    if not filter_sets:
        raise ValueError("No filters provided.")

    ### strict intersection of all filters
    idxs = list(set.intersection(*filter_sets))

    if not idxs:
        raise ValueError(f"No atoms found matching all filters: {filters}")
    return idxs


def _extract_dxdydz(mystring: str) -> tuple[float, float, float]:
    """Extract dx, dy, dz from a string like xxx_dx0.1_dy-0.2_dz0.3."""
    # `[-+]?` matches -/+ or nothing. `[]` is character class matches one of the characters inside; `?` make it optional (0 or 1 occurrence).
    # `\d*\.?\d+` matches a float number. `\.` a literal dot `.` (escaped, since `.` alone means "any character"). `*` 0 or more occurrences. `+` 1 or more occurrences.
    match = re.search(r"_dx([-+]?\d*\.?\d+)", mystring)
    dx = float(match.group(1)) if match else 0.0
    match = re.search(r"_dy([-+]?\d*\.?\d+)", mystring)
    dy = float(match.group(1)) if match else 0.0
    match = re.search(r"_dz([-+]?\d*\.?\d+)", mystring)
    dz = float(match.group(1)) if match else 0.0
    return dx, dy, dz


def _extract_interlayer_distance(struct: Atoms, fix_idxs: list[int]) -> float:
    """Extract interlayer distance from fix_atoms list."""
    pos = struct.positions[fix_idxs]
    assert pos.shape[0] >= 2, (
        f"At least two fixed atoms are needed to compute interlayer distance, but only {pos.shape[0]} found."
    )
    mean_z = np.mean(pos[:, 2])
    upper_z = np.mean(pos[pos[:, 2] > mean_z][:, 2])
    lower_z = np.mean(pos[pos[:, 2] < mean_z][:, 2])
    distance = upper_z - lower_z
    return distance.astype(float)


#####ANCHOR interpolate and plot PES
def mapping_dxdydz_to_cartesian(
    dxdydz: np.ndarray,
    struct_cell: np.ndarray,
):
    """Sampling points are in (u,v) coordinates along cell vectors that may not orthogonal.

    This function transform sampling points to real Cartesian coordinates

    Args:
        dxdydz: array (N,3) containing (dx, dy, dz) for N sampling points
        struct_cell: array (3,3) containing cell vectors
    """
    from asext.cell import CellTransform

    a, b, c = struct_cell[0], struct_cell[1], struct_cell[2]
    unit_cell = np.asarray((a / np.linalg.norm(a), b / np.linalg.norm(b), c / np.linalg.norm(c)))
    normal_cell = np.asarray([[1, 0, 0], [0, 1, 0], [0, 0, 1]])
    rot = CellTransform(old_cell=normal_cell, new_cell=unit_cell, pure_rotation=False)
    xyz = rot.vectors_forward(dxdydz)
    return xyz


def interp_pes_xy(df: pl.DataFrame, grid_size: float = 0.05) -> pl.DataFrame:
    """Interpolate PES surface in the xy plane.

    Args:
        df: PES raw data file with columns: dx dy energy
        grid_size: grid size (Å) for interpolation
    Returns:
        df: DataFrame with columns: grid_x, grid_y, energy/atom
    """
    from scipy.interpolate import RegularGridInterpolator

    ### PES data
    dx, dy, E = df.select(["dx", "dy", "energy/atom"]).to_numpy().T

    ### Turn Array into 2D grid
    uni_x = np.unique(dx)
    uni_y = np.unique(dy)
    values = E.reshape(len(uni_y), len(uni_x))  # Grid form, shape=(len(uni_y), len(uni_x))

    ### Interpolate
    Xpoints = np.linspace(uni_x.min(), uni_x.max(), int((uni_x.max() - uni_x.min()) / grid_size))
    Ypoints = np.linspace(uni_y.min(), uni_y.max(), int((uni_y.max() - uni_y.min()) / grid_size))
    Xg, Yg = np.meshgrid(Xpoints, Ypoints)  # Grid form, shape=(len(Ypoints), len(Xpoints))

    interp = RegularGridInterpolator((uni_x, uni_y), values, method="cubic")
    E = interp((Xg, Yg))  # shape=(len(Ypoints), len(Xpoints))

    ### Output in flattened form
    XgYgE = np.column_stack((Xg.ravel(), Yg.ravel(), E.ravel()))
    df = pl.DataFrame(XgYgE, schema=["grid_x", "grid_y", "energy/atom"])
    df = df.with_columns((pl.col("energy/atom") - pl.min("energy/atom")).alias("delta_e"))
    return df


def interp_pes_z(df: pl.DataFrame, grid_size: float = 0.05) -> pl.DataFrame:
    """Interpolate PES curve in the z direction.

    Args:
        df: PES raw data with columns: dz energy
        grid_size: grid size (Å) for interpolation
    Returns:
        df: DataFrame with columns: grid_z, energy/atom
    """
    from scipy.interpolate import make_interp_spline

    ### PES data
    df = df.sort("dz")
    dz, E = df.select(["dz", "energy/atom"]).to_numpy().T

    ### Interpolate
    Zpoints = np.linspace(dz.min(), dz.max(), int((dz.max() - dz.min()) / grid_size))
    interp = make_interp_spline(dz, E, k=3)  # Cubic spline
    E_interp = interp(Zpoints)  # shape=(len(Zpoints),)
    ZgE = np.column_stack((Zpoints, E_interp))
    df = pl.DataFrame(ZgE, schema=["grid_z", "energy/atom"])
    df = df.with_columns((pl.col("energy/atom") - pl.min("energy/atom")).alias("delta_e"))
    return df


def plot_pes_xy(file_pes_grid: str, file_pes_raw: str | None = None):
    """Plot PES surface in the xy plane.

    Args:
        file_pes_grid: file containing PES data interpolated on a grid
        file_pes_raw: file containing raw PES data (optional, to plot input data points)
    """
    import matplotlib.pyplot as plt
    from mpl_toolkits.axes_grid1 import make_axes_locatable

    ### PES data
    df = pl.read_csv(file_pes_grid)
    x, y, delta_e = df.select(["grid_x", "grid_y", "delta_e"]).to_numpy().T

    ### Turn Array into 2D grid
    uni_x = np.unique(x)
    uni_y = np.unique(y)
    E = delta_e.reshape(len(uni_y), len(uni_x))  # Grid form, shape=(len(uni_y), len(uni_x))
    Xg, Yg = np.meshgrid(uni_x, uni_y)  # Grid form, shape=(len(uni_y), len(uni_x))

    ### Plot
    fig, ax = plt.subplots(1, 1, figsize=(3.4, 3.4))
    cf = ax.pcolormesh(Xg, Yg, E * 1e3, shading="gouraud", cmap="rainbow")
    # ax.plot(dx, dy, "ok", ms=2, label="input data")
    ax.set(
        xlabel="dx (Å)",
        ylabel="dy (Å)",
        title="PES",
        xlim=(x.min(), x.max()),
        ylim=(y.min(), y.max()),
        aspect="equal",
    )
    ## Make colorbar the same height as y-axis
    divider = make_axes_locatable(ax)
    cax = divider.append_axes("right", size="5%", pad=0.1)
    cbar = fig.colorbar(cf, cax=cax, label=r"$\Delta E$ (meV/atom)")  # noqa: F841

    ## Plot rawdata points
    if file_pes_raw is not None:
        dfraw = pl.read_csv(file_pes_raw, separator=" ")
        ax.plot(dfraw["dx"], dfraw["dy"], "ok", ms=2, label="input data")
        ax.legend(loc="upper right", fontsize=8)

    fig.tight_layout()
    fig.savefig(Path(file_pes_grid).parent / "pes_xy.pdf", dpi=300, bbox_inches="tight")
    return


def plot_pes_z(file_pes_grid: str, file_pes_raw: str | None = None):
    """Plot PES surface in the xy plane.

    Args:
        file_pes_grid: file containing PES data interpolated on a grid
        file_pes_raw: file containing raw PES data (optional, to plot input data points)
    """
    import matplotlib.pyplot as plt

    ### PES data
    df = pl.read_csv(file_pes_grid)
    z, delta_e = df.select(["grid_z", "delta_e"]).to_numpy().T

    ### Plot
    fig, ax = plt.subplots(1, 1, figsize=(3.4, 2.7))
    ax.plot(z, delta_e * 1e3, "-")
    ax.set(
        xlabel="dz (Å)",
        ylabel=r"$\Delta E$ (meV/atom)",
        title="PES along z",
        xlim=(z.min(), z.max()),
    )
    ## Plot rawdata points
    if file_pes_raw is not None:
        dfraw = pl.read_csv(file_pes_raw)
        energy_min = df.select(pl.min("energy/atom")).item()
        dfraw = dfraw.with_columns((pl.col("energy/atom") - pl.lit(energy_min)).alias("delta_e"))
        ax.plot(dfraw["dz"], dfraw["delta_e"] * 1e3, "ok", ms=3, label="input data")

    fig.tight_layout()
    fig.savefig(Path(file_pes_grid).parent / "pes_curve_z.pdf", dpi=300, bbox_inches="tight")
    return


def plot_pes_3d():
    # to consider later
    return
