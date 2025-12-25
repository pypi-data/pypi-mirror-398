"""Utilities for uncertainty estimation using models committee.
- DO NOT import any `alff` libs in this file, since this file will be used remotely.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Generator, Sequence

    from ase.calculators.calculator import Calculator
    from sevenn.sevennet_calculator import SevenNetCalculator

from pathlib import Path

import numpy as np
from ase import Atoms
from ase.io import read, write
from rich.progress import track


class ModelCommittee:
    """A class to manage a committee of models for uncertainty estimation."""

    def __init__(
        self,
        mlp_model: str,
        model_files: list[str],
        calc_kwargs: dict | None = None,
        compute_stress: bool = False,
        rel_force: float | None = None,
        rel_stress: float | None = None,
        e_std_lo: float = 0.05,
        e_std_hi: float = 0.1,
        f_std_lo: float = 0.05,
        f_std_hi: float = 0.1,
        s_std_lo: float = 0.05,
        s_std_hi: float = 0.1,
        block_size: int = 1000,
    ):
        """Initialize the ModelCommittee.

        Args:
            mlp_model (str): MLP model engine, e.g., 'sevenn'.
            model_files (list[str]): List of model files for the committee.
            calc_kwargs (dict, optional): Additional arguments for the MLP calculator. Defaults to {}.
            compute_stress (bool, optional): Whether to compute stress. Defaults to False.
            rel_force (float, optional): Relative force to normalize force std. Defaults to None.
            rel_stress (float, optional): Relative stress to normalize stress std. Defaults to None.

            e_std_lo (float, optional): energy std low. Defaults to 0.05.
            e_std_hi (float, optional): energy std high. Defaults to 0.1.
            f_std_lo (float, optional): force std low. Defaults to 0.05.
            f_std_hi (float, optional): force std high. Defaults to 0.1.
            s_std_lo (float, optional): stress std low. Defaults to 0.05.
            s_std_hi (float, optional): stress std high. Defaults to 0.1.
            block_size (int, optional): Block size of configurations to compute 'committee error' at once, just to avoid flooding memory. Defaults to 1000.

        Notes:
            - Consider using `@staticmethod` for some functions to avoid recursive messing.
        """
        self.mlp_model = mlp_model
        self.model_files = model_files
        self.calc_kwargs = calc_kwargs or {}
        self.compute_stress = compute_stress
        self.rel_force = rel_force
        self.rel_stress = rel_stress
        self.block_size = block_size
        ### Committee Standard criteria
        self.e_std_lo = e_std_lo
        self.e_std_hi = e_std_hi
        self.f_std_lo = f_std_lo
        self.f_std_hi = f_std_hi
        self.s_std_lo = s_std_lo
        self.s_std_hi = s_std_hi
        ### internal variables
        self.calc_list = self._get_calc_list()
        self.committee_error_file: str = "committee_error.txt"
        self.committee_judge_file: str = "committee_judge_summary.yml"
        ### Will be assigned later

    ######ANCHOR Calculators
    def _get_calc_list(self) -> Sequence[Calculator]:
        """Get the list of calculators based on the MLP model."""
        supported_mlp = ["sevenn"]
        if self.mlp_model.lower() not in supported_mlp:
            raise NotImplementedError(f"MLP model '{self.mlp_model}' not supported yet.")

        model_files, calc_kwargs = self.model_files, self.calc_kwargs
        assert len(model_files) > 1, "At least two model files are required for committee."

        if self.mlp_model.lower() == "sevenn":
            calc_list = self._calc_list_sevenn(model_files, calc_kwargs)
        return calc_list  # type: ignore[unbounded]

    @staticmethod
    def _calc_list_sevenn(model_files: list[str], calc_kwargs: dict) -> list[SevenNetCalculator]:
        """Get the list of SevenNet calculators."""
        from sevenn.sevennet_calculator import SevenNetCalculator

        calc_list = [SevenNetCalculator(model_file, **calc_kwargs) for model_file in model_files]
        return calc_list

    ######ANCHOR Committee error
    @staticmethod
    def _ensemble_predict(
        calc_list: Sequence[Calculator],
        structs: list[Atoms],
        compute_stress: bool,
    ) -> tuple:  # tuple of np.ndarray
        """Predicted energy, forces, and stress from all models in the committee for multiple configurations.

        Args:
            calc_list (list[Calculator]): List of calculators.
            structs (list[Atoms]): List of Atoms objects.
            compute_stress (bool): Whether to compute stress.

        Returns:
            energies (np.ndarray): Shape (n_models, n_structs)
            forces (np.ndarray): Shape (n_models, n_structs, n_atoms, 3)
            stresses (np.ndarray): Shape (n_models, n_structs, n_stress_components)

        Notes:
            - This function computes for multiple configurations, but it is not a true batching inference as in some MLP models like DeepMD-kit. It is just to avoid repeatedly assigning calculators and calling numpy functions multiple times (more vectorized). Therefore, it maybe 5-10% faster the old naive implementation, but not significantly faster as true batching inference.
            - Note that, batching inference requires all configurations have the same number of atoms. Similarly, - this `blockwise` functions requires all configurations in block have the same number of atoms. So if the input extxyz file contains configurations with different number of atoms, must use block_size=1 when initializing `ModelCommittee` class.
            - Define this function as `staticmethod` to avoid recursive messing when compute stresses in next functions.
            - Work with structures with pre-existing calculators and results:
                - Should make `struct_copy = struct.copy()` before calling `struct.get_*()` to avoid the result from `get_*()` being affected by previous calculators's results.
                - Should call `struct_copy.calc = None` to clean up previous calculator (e.g., SinglePointCalculator) before assigning new calculator. This is important when the input `structs` already had `results` stored in `struct.calc.results`, new results may try to be stored in the existing `results` dict, causing shape messing or unexpected values.
        """
        energies = [None] * len(calc_list)
        forces = [None] * len(calc_list)
        stresses = [None] * len(calc_list)
        for i, calc in enumerate(calc_list):
            e = [None] * len(structs)
            f = [None] * len(structs)
            s = [None] * len(structs)
            for j, struct in enumerate(structs):
                struct_copy = struct.copy()  # avoid messing with original struct
                struct_copy.calc = None  # clean up previous calculator
                struct_copy.calc = calc
                e[j] = struct_copy.get_potential_energy()
                f[j] = struct_copy.get_forces()
                if compute_stress:
                    s[j] = struct_copy.get_stress(voigt=True)  # type: ignore

            energies[i] = e  # type: ignore
            forces[i] = f  # type: ignore
            stresses[i] = s  # type: ignore

        energies_np = np.asarray(energies, dtype=float)  # (n_models, n_structs)
        forces_np = np.asarray(forces, dtype=float)  # (n_models, n_structs, n_atoms, 3)
        if compute_stress:
            stresses_np = np.asarray(stresses, dtype=float)  # (n_models, n_structs, n_components)
        else:
            stresses_np = None
        return (energies_np, forces_np, stresses_np)

    def _compute_committee_error(self, structs: list[Atoms]) -> np.ndarray:
        """Compute committee error for energy, forces, and stress for a multiple configurations.

        Args:
            structs (list[Atoms]): List of Atoms objects.

        Returns:
            outdata (np.ndarray): shape (n_structs, n_metrics)

        Notes:
            - `mag_s[:, None]` is used to keep the 2D shape (column vector) when normalizing stress std.
            - Define this function as `staticmethod` to avoid recursive messing when compute stresses in next functions.
        """
        calc_list = self.calc_list
        compute_stress = self.compute_stress
        rel_force = self.rel_force
        rel_stress = self.rel_stress

        energies, forces, stresses = self._ensemble_predict(calc_list, structs, compute_stress)

        e_std = np.std(energies, axis=0)  # (n_structs,)
        f_std = np.linalg.norm(np.std(forces, axis=0), axis=-1)
        # (n_models, n_structs, n_atoms, 3) -> (n_structs, n_atoms, 3) --> (n_structs, n_atoms)
        if rel_force is not None:
            mag_f = np.linalg.norm(np.mean(forces, axis=0), axis=-1)  # (n_structs, n_atoms)
            f_std /= mag_f + rel_force  # (n_structs, n_atoms)

        f_std_max = np.max(f_std, axis=-1)  # (n_structs,)
        f_std_min = np.min(f_std, axis=-1)
        f_std_mean = np.mean(f_std, axis=-1)

        if compute_stress:
            s_std = np.std(stresses, axis=0)  # (n_structs, n_components)
            if rel_stress is not None:
                mag_s = np.linalg.norm(np.mean(stresses, axis=0), axis=-1)  # (n_structs,)
                s_std /= mag_s[:, None] + rel_stress  # (n_structs, n_components)

            s_std_max = np.max(s_std, axis=-1)  # (n_structs,)
            s_std_min = np.min(s_std, axis=-1)
            n_components = s_std.shape[-1]
            s_std_mean = np.linalg.norm(s_std, axis=-1) / float(n_components)  # (n_structs,)

            outdata = np.column_stack(
                (e_std, f_std_max, f_std_min, f_std_mean, s_std_max, s_std_min, s_std_mean)
            )
        else:
            outdata = np.column_stack((e_std, f_std_max, f_std_min, f_std_mean))
        return outdata

    def compute_committee_error_blockwise(self, struct_list: list[Atoms]):
        """Compute committee error for energy, forces, and stress for a multiple configurations in a block-wise manner.

        Args:
            struct_list (list[Atoms]): List of Atoms objects.

        Notes:
            The output file is controlled by the class attribute `self.committee_error_file`.
        """
        header = "e_std f_std_max f_std_min f_std_mean"
        header += " s_std_max s_std_min s_std_mean" if self.compute_stress else ""

        with open(self.committee_error_file, "w") as f:
            f.write(f"{header}\n")

            chunks = chunk_list(struct_list, self.block_size)
            for structs in track(
                chunks,
                total=int(np.ceil(len(struct_list) / self.block_size)),
                refresh_per_second=0.1,
            ):
                outdata = self._compute_committee_error(structs)
                np.savetxt(f, outdata, fmt="%.6f")
        return

    def committee_judge(self) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Decide whether a configuration is candidate, accurate, or inaccurate based on committee error.

        Returns:
            committee_judge_file(s): files contain candidate, accurate and inaccurate configurations

        Note:
            - If need to select candidates based on only `energy`, just set `f_std_hi` and `s_std_hi` to a very large values. By this way, the criterion for those terms will always meet.
            - Similarly, if need to select candidates based on only `energy` and `force`, set `s_std_hi` to a very large value. E.g., `s_std_hi=1e6` for selecting candidates based on energy and force.
        """
        e_std_lo = self.e_std_lo
        e_std_hi = self.e_std_hi
        f_std_lo = self.f_std_lo
        f_std_hi = self.f_std_hi
        s_std_lo = self.s_std_lo
        s_std_hi = self.s_std_hi

        if self.committee_error_file is None:
            raise ValueError(
                "No committee error data found. Please run method `compute_committee_error_blockwise()` first."
            )

        arr = np.loadtxt(self.committee_error_file, skiprows=1, ndmin=2)

        ### Indexing candidate, accurate, inaccurate structures
        if self.compute_stress:
            e_std, f_std_max, s_std_max = arr[:, 0], arr[:, 1], arr[:, 4]
            accurate_mask = (e_std < e_std_lo) & (f_std_max < f_std_lo) & (s_std_max < s_std_lo)
            inaccurate_mask = (e_std > e_std_hi) | (f_std_max > f_std_hi) | (s_std_max > s_std_hi)
            arr_reduce = np.hstack((e_std[:, None], f_std_max[:, None], s_std_max[:, None]))
        else:
            e_std, f_std_max = arr[:, 0], arr[:, 1]
            accurate_mask = (e_std < e_std_lo) & (f_std_max < f_std_lo)
            inaccurate_mask = (e_std > e_std_hi) | (f_std_max > f_std_hi)
            arr_reduce = np.hstack((e_std[:, None], f_std_max[:, None]))

        candidate_mask = ~(accurate_mask | inaccurate_mask)

        candidate_idx = np.where(candidate_mask)[0]
        accurate_idx = np.where(accurate_mask)[0]
        inaccurate_idx = np.where(inaccurate_mask)[0]

        ### Write outputs
        def _save_group(suffix: str, idx: np.ndarray):
            if len(idx) > 0:
                data = np.hstack((idx[:, None], arr_reduce[idx]))
                header = "idx e_std f_std_max" + (" s_std_max" if self.compute_stress else "")
                fmt_str = " ".join(["%d"] + ["%.6f"] * (data.shape[1] - 1))
                filename = f"committee_judge_{suffix}.txt"
                np.savetxt(filename, data, fmt=fmt_str, header=header, comments="")
            return

        _save_group("candidate", candidate_idx)
        _save_group("accurate", accurate_idx)
        _save_group("inaccurate", inaccurate_idx)

        with open(self.committee_judge_file, "w") as f:
            f.write(f"total_frames: {arr_reduce.shape[0]}\n")
            f.write(f"candidates: {len(candidate_idx)}\n")
            f.write(f"accurates: {len(accurate_idx)}\n")
            f.write(f"inaccurates: {len(inaccurate_idx)}\n")
            f.write("criteria:\n")
            f.write(f"  e_std_lo: {e_std_lo}\n  e_std_hi: {e_std_hi}\n")
            f.write(f"  f_std_lo: {f_std_lo}\n  f_std_hi: {f_std_hi}\n")
            if self.compute_stress:
                f.write(f"  s_std_lo: {s_std_lo}\n  s_std_hi: {s_std_hi}\n")
        return candidate_idx, accurate_idx, inaccurate_idx

    #####ANCHOR Select configurations
    def select_candidate(self, extxyz_file: str):
        """Select candidate configurations for DFT calculation.

        Returns:
            extxyz_file (str): candidate configurations

        Note: See parameters in functions `committee_error` and `committee_judge`.
        """
        structs = read(extxyz_file, format="extxyz", index=":")
        if isinstance(structs, Atoms):
            structs = [structs]

        self.compute_committee_error_blockwise(structs)
        candidate_idx, *_ = self.committee_judge()

        ### Select candidates from the extxyz file
        if len(candidate_idx) > 0:
            select_structs = [structs[i] for i in candidate_idx]
            write(f"{Path(extxyz_file).stem}_candidate.extxyz", select_structs, format="extxyz")
        return

    def remove_inaccurate(self, extxyz_file: str):
        """Remove inaccurate configurations based on committee error. This is used to revise the dataset.

        Returns:
            extxyz_file (str): revise configurations

        Notes:
            - `blockwise` functions requires all configurations in block have the same number of atoms. So if the input extxyz file contains configurations with different number of atoms, must use block_size=1 when initializing `ModelCommittee` class.
        """
        structs = read(extxyz_file, format="extxyz", index=":")
        if isinstance(structs, Atoms):
            structs = [structs]

        self.compute_committee_error_blockwise(structs)
        candidate_idx, accurate_idx, inaccurate_idx = self.committee_judge()
        select_idx = np.concatenate((candidate_idx, accurate_idx))

        ### Eliminate inaccurate confs from the extxyz file
        if len(select_idx) > 0:
            select_structs = [structs[i] for i in select_idx]
            write(f"{Path(extxyz_file).stem}_rest.extxyz", select_structs, format="extxyz")

        if len(inaccurate_idx) > 0:
            inacc_structs = [structs[i] for i in inaccurate_idx]
            write(f"{Path(extxyz_file).stem}_inaccurate.extxyz", inacc_structs, format="extxyz")

        Path(extxyz_file).unlink()  # remove the original file
        return


#####ANCHOR convert format
def simple_lmpdump2extxyz(lmpdump_file: str, extxyz_file: str):
    """Convert LAMMPS dump file to extended xyz file. This is very simple version, only convert atomic positions, but not stress tensor."""
    struct_list = read(lmpdump_file, format="lammps-dump-text", index=":")
    write(extxyz_file, struct_list, format="extxyz")
    return


def chunk_list(input_list: list, chunk_size: int) -> Generator[list, None, None]:
    """Yield successive n-sized chunks from `input_list`.

    Args:
        input_list (list): Input list to be chunked.
        chunk_size (int): Chunk size (number of elements per chunk).
    """
    for i in range(0, len(input_list), chunk_size):
        yield input_list[i : i + chunk_size]
