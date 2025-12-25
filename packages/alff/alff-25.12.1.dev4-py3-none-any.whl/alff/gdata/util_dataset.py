"""Utility functions for handling dataset files."""

### REF:
# - https://github.com/janosh/matbench-discovery/blob/main/models/sevennet/train_sevennet/convert_mptrj_to_xyz.py

import random
import shutil
from math import ceil
from pathlib import Path

import numpy as np
from ase import Atoms

from asext.io.readwrite import read_extxyz, write_extxyz


### ANCHOR: Processing extxyz files
def _divide_idx_list(
    idx_list: list[int],
    train_ratio: float,
    valid_ratio: float,
) -> tuple[list[int], list[int], list[int]]:
    """Divide list of ints based on given ratios.
    Resolve any floating point issues.
    """
    ### Revise ratios
    total_ratio = train_ratio + valid_ratio
    assert total_ratio >= 0 and total_ratio <= 1, "Split total ratio must be between 0 and 1."
    test_ratio = (1 - (train_ratio + valid_ratio)) if total_ratio < 1 else 0
    ratios = [train_ratio, valid_ratio, test_ratio]

    ### Devide list
    n_total = len(idx_list)
    nums = [ceil(r * n_total) for r in ratios]
    exceed = sum(nums) - n_total
    if exceed > 0:
        nums[-1] -= exceed  # adjust test set to ensure total consistency

    ### Distribute indices
    divided_list = []
    start = 0
    for n in nums:
        divided_list.append(idx_list[start : start + n])
        start += n
    train_idxs, valid_idxs, test_idxs = divided_list
    return train_idxs, valid_idxs, test_idxs


def split_extxyz_dataset(
    extxyz_files: list[str],
    train_ratio: float = 0.9,
    valid_ratio: float = 0.1,
    seed: int | None = None,
    outfile_prefix: str = "dataset",
):
    ### ref: https://github.com/janosh/matbench-discovery/blob/main/models/sevennet/train_sevennet/convert_mptrj_to_xyz.py
    """Split a dataset into training, validation, and test sets.

    If input (train_ratio + valid_ratio) < 1, the remaining data will be used as the test set.

    Args:
        extxyz_files (list[str]): List of file paths in EXTXYZ format.
        train_ratio (float): Ratio of training set. Defaults to 0.9.
        valid_ratio (float): Ratio of validation set. Defaults to 0.1.
        seed (Optional[int]): Random seed. Defaults to None.
        outfile_prefix (str): Prefix for output file names. Defaults to "dataset".
    """
    if isinstance(extxyz_files, str):
        extxyz_files = [extxyz_files]

    ### read data
    struct_list = read_list_extxyz(extxyz_files)

    ### Divide indices
    n_total = len(struct_list)
    indices = list(range(n_total))
    random.Random(seed).shuffle(indices)
    train_idxs, valid_idxs, test_idxs = _divide_idx_list(indices, train_ratio, valid_ratio)

    ### split
    if len(train_idxs) > 0:
        train_data = [struct_list[i] for i in train_idxs]
        write_extxyz(f"{outfile_prefix}_trainset.extxyz", train_data)
    if len(valid_idxs) > 0:
        valid_data = [struct_list[i] for i in valid_idxs]
        write_extxyz(f"{outfile_prefix}_validset.extxyz", valid_data)
    if len(test_idxs) > 0:
        test_data = [struct_list[i] for i in test_idxs]
        write_extxyz(f"{outfile_prefix}_testset.extxyz", test_data)
    return


def read_list_extxyz(extxyz_files: list[str]) -> list[Atoms]:
    """Read a list of EXTXYZ files and return a list of ASE Atoms objects."""
    struct_list = []
    for file in extxyz_files:
        struct_list.extend(read_extxyz(file))
    return struct_list


def merge_extxyz_files(
    extxyz_files: list[str],
    outfile: str,
    sort_natoms: bool = False,
    sort_composition: bool = False,
    sort_pbc_len: bool = False,
):
    """Unify multiple EXTXYZ files into a single file.

    Args:
        extxyz_files (list[str]): List of EXTXYZ file paths.
        outfile (str): Output file path.
        sort_natoms (bool): Sort by number of atoms. Defaults to True.
        sort_composition (bool): Sort by chemical composition. Defaults to True.
        sort_pbc_len (bool): Sort by periodic length. Defaults to True.

    Note:
        - `np.lexsort` is used to sort by multiple criteria. `np.argsort` is used to sort by a single criterion.
        - `np.lexsort` does not support descending order, so we reverse the sorted indices using `idx[::-1]`.
    """
    if len(extxyz_files) < 1:
        print("Must provide at least 2 `.extxyz` files for merging.")
        return

    ### support funcs
    def calc_atoms_num(struct_list: list[Atoms]):  # -> np.array[int]
        return np.array([len(atoms) for atoms in struct_list])

    def calc_composition(struct_list: list[Atoms]):  # -> np.array[str]
        return np.array([atoms.get_chemical_formula() for atoms in struct_list])

    def calc_periodic_length(struct_list: list[Atoms]):  # -> np.array[int]
        periodic_len = [
            sum(length for length, pbc in zip(atoms.cell.lengths(), atoms.pbc) if pbc)
            for atoms in struct_list
        ]
        return np.array(periodic_len)

    ### Main function
    struct_list = read_list_extxyz(extxyz_files)

    if sort_natoms and sort_composition and sort_pbc_len:
        atoms_num = calc_atoms_num(struct_list)
        composition = calc_composition(struct_list)
        periodic_len = calc_periodic_length(struct_list)
        ### Sort indices: first by 'atoms_num', then by 'composition', then by 'periodic_len
        sorted_indices = np.lexsort((periodic_len, composition, atoms_num))
    elif sort_natoms and sort_composition:
        atoms_num = calc_atoms_num(struct_list)
        composition = calc_composition(struct_list)
        sorted_indices = np.lexsort((composition, atoms_num))
    elif sort_natoms and sort_pbc_len:
        atoms_num = calc_atoms_num(struct_list)
        periodic_len = calc_periodic_length(struct_list)
        sorted_indices = np.lexsort((periodic_len, atoms_num))
    elif sort_composition and sort_pbc_len:
        composition = calc_composition(struct_list)
        periodic_len = calc_periodic_length(struct_list)
        sorted_indices = np.lexsort((periodic_len, composition))
    elif sort_natoms:
        sorted_indices = np.argsort(calc_atoms_num(struct_list))
    elif sort_composition:
        sorted_indices = np.argsort(calc_composition(struct_list))
    elif sort_pbc_len:
        sorted_indices = np.argsort(calc_periodic_length(struct_list))
    else:  # No sorting; keep original order
        sorted_indices = range(len(struct_list))

    indices_descending = sorted_indices[::-1]
    sorted_struct_list = [struct_list[i] for i in indices_descending]

    ### Write output file
    Path(outfile).parent.mkdir(parents=True, exist_ok=True)
    write_extxyz(outfile, sorted_struct_list)
    return


#####ANCHOR Processing extxyz's atoms properties
def change_key_in_extxyz(extxyz_file: str, key_pairs: dict[str, str]):
    """Change keys in extxyz file.

    Args:
        extxyz_file (str): Path to the extxyz file.
        key_pairs (dict): Dictionary of key pairs {"old_key": "new_key"} to change. Example: `{"old_key": "new_key", "forces": "ref_forces", "stress": "ref_stress"}`

    Note:
        - If Atoms contains internal-keys (e.g., `energy`, `forces`, `stress`, `momenta`, `free_energy`,...), there will be a `SinglePointCalculator` object included to the Atoms, and these keys are stored in dict `atoms.calc.results` or can be accessed using `.get_()` methods.
        - These internal-keys are not stored in `atoms.arrays` or `atoms.info`. If we want to store (and access) these properties in `atoms.arrays` or `atoms.info`, we need to change these internal-keys to custom-keys (e.g., `ref_energy`, `ref_forces`, `ref_stress`, `ref_momenta`, `ref_free_energy`,...).
    """
    from ase.calculators.singlepoint import SinglePointCalculator

    info_keys = ["stress", "energy", "free_energy", "dipole", "magmom"]
    arrays_keys = ["forces", "magmoms"]
    internal_keys = info_keys + arrays_keys

    struct_list = read_extxyz(extxyz_file)
    for atoms in struct_list:
        ### find if atoms has keys
        found_keys = {
            k: v
            for k, v in key_pairs.items()
            if k in atoms.arrays
            or k in atoms.info
            or (atoms.calc is not None and k in atoms.calc.results)
        }
        ### Change keys
        for k, v in found_keys.items():
            if k in internal_keys:
                ### change from internal_keys to custom_keys
                if atoms.calc is not None:
                    if k in arrays_keys:
                        atoms.arrays[v] = atoms.calc.results[k]
                    elif k in info_keys:
                        atoms.info[v] = atoms.calc.results[k]
                    atoms.calc.results.pop(k, None)
            elif v in internal_keys:
                if atoms.calc is not None:
                    atoms.calc = SinglePointCalculator(atoms, **atoms.calc.results)
                else:
                    atoms.calc = SinglePointCalculator(atoms)
                ### change from custom_keys to internal_keys
                if v in arrays_keys:
                    atoms.calc.results[v] = atoms.arrays[k]
                    atoms.arrays.pop(k, None)
                elif v in info_keys:
                    atoms.calc.results[v] = atoms.info[k]
                    atoms.info.pop(k, None)
            else:
                ### change from custom_keys to custom_keys
                if k in atoms.arrays:
                    atoms.arrays[v] = atoms.arrays.pop(k)
                if k in atoms.info:
                    atoms.info[v] = atoms.info.pop(k)

    write_extxyz(extxyz_file, struct_list)
    return


def remove_key_in_extxyz(extxyz_file: str, key_list: list[str]):
    """Remove unwanted keys from extxyz file to keep it clean."""
    internal_keys = [
        "forces",
        "stress",
        "energy",
        "free_energy",
        "dipole",
        "magmom",
        "magmoms",
    ]
    struct_list = read_extxyz(extxyz_file)
    for atoms in struct_list:
        for key in key_list:
            if key in internal_keys:  # internal-keys
                if atoms.calc is not None:
                    atoms.calc.results.pop(key, None)
            else:  # other custom-keys
                atoms.arrays.pop(key, None)
                atoms.info.pop(key, None)

    write_extxyz(extxyz_file, struct_list)
    return


#####ANCHOR Select frames in extxyz files
def _struct_selection_fingerprint(struct: Atoms, tol: float = 1e-6) -> dict:
    """Build a fingerprint dict with relevant info for selection filters."""
    # Chemical symbols
    symbols = set(struct.get_chemical_symbols())

    # Properties (frame-level info)
    properties = set(struct.info.keys())
    natoms = len(struct)

    # Columns (per-atom arrays)
    columns = set(struct.arrays.keys())

    # Extra: structural fingerprint (geometry) if needed later
    # s = sort_atoms_by_position(struct)
    # geom_fp = (
    #     tuple(s.get_pbc().tolist()),
    #     tuple(map(tuple, np.round(s.get_cell() / tol).astype(int))),
    #     tuple(map(tuple, np.round(s.get_scaled_positions() / tol).astype(int))),
    # )

    return {
        "symbols": symbols,
        "natoms": natoms,
        "properties": properties,
        "columns": columns,
        # "geom_fp": geom_fp,
    }


def select_structs_from_extxyz(
    extxyz_file: str,
    has_symbols: list | None = None,
    only_symbols: list | None = None,
    exact_symbols: list | None = None,
    has_properties: list | None = None,
    only_properties: list | None = None,
    has_columns: list | None = None,
    only_columns: list | None = None,
    natoms: int | None = None,
    tol: float = 1e-6,
):
    ### https://github.com/ACEsuit/mace/blob/main/mace/data/utils.py
    """Choose frames from a extxyz trajectory file, based on some criteria.

    Args:
        extxyz_file (str): Path to the extxyz file.
        has_symbols (list): List of symbols that each frame must have at least one of them.
        only_symbols (list): List of symbols that each frame must have only these symbols.
        exact_symbols (list): List of symbols that each frame must have exactly these symbols.
        has_properties (list): List of properties that each frame must have at least one of them.
        only_properties (list): List of properties that each frame must have only these properties.
        has_columns (list): List of columns that each frame must have at least one of them.
        only_columns (list): List of columns that each frame must have only these columns.
        natoms (int): total number of atoms in frame.
        tol (float): Tolerance for comparing floating point numbers.
    """
    struct_list = read_extxyz(extxyz_file)
    selected_index = []

    ### Apply all filters in one pass
    for i, struct in enumerate(struct_list):
        fp = _struct_selection_fingerprint(struct, tol=tol)

        if has_symbols is not None and not (fp["symbols"] & set(has_symbols)):
            continue
        if only_symbols is not None and not fp["symbols"].issubset(set(only_symbols)):
            continue
        if exact_symbols is not None and not (fp["symbols"] == set(exact_symbols)):
            continue

        if has_properties is not None and not (fp["properties"] & set(has_properties)):
            continue
        if only_properties is not None and not (fp["properties"] == set(only_properties)):
            continue

        if has_columns is not None and not (fp["columns"] & set(has_columns)):
            continue
        if only_columns is not None and not (fp["columns"] == set(only_columns)):
            continue

        if natoms is not None and fp["natoms"] != natoms:
            continue

        selected_index.append(i)

    ### Collect selected structures
    if len(selected_index) > 0:
        selected_structs = [struct_list[i] for i in selected_index]
        unselected_structs = [
            struct_list[i] for i in range(len(struct_list)) if i not in selected_index
        ]
        write_extxyz(extxyz_file.replace(".extxyz", "_selected.extxyz"), selected_structs)

        if len(unselected_structs) > 0:
            write_extxyz(
                extxyz_file.replace(".extxyz", "_unselected.extxyz"),
                unselected_structs,
            )
    else:
        print("No structures matched the selection criteria.")
    return


#####SECTION Remove duplicate structures in extxyz files
#####ANCHOR Pairwise comparison approach (O(N^2))
def sort_atoms_by_position(struct: Atoms) -> Atoms:
    """Sorts the atoms in an Atoms object based on their Cartesian positions."""
    pos = struct.get_positions()
    sorted_indices = np.lexsort((pos[:, 2], pos[:, 1], pos[:, 0]))  # sort x, then y, then z
    return struct[sorted_indices]


def are_structs_identical(input_struct1: Atoms, input_struct2: Atoms, tol=1.0e-6) -> bool:
    """Checks if two Atoms objects are identical by first sorting them and then comparing their attributes.

    Args:
        input_struct1 (Atoms): First Atoms object.
        input_struct2 (Atoms): Second Atoms object.
        tol (float): Tolerance for position comparison.

    Returns:
        bool: True if the structures are identical, False otherwise.
    """
    struct1 = sort_atoms_by_position(input_struct1)
    struct2 = sort_atoms_by_position(input_struct2)

    ### Check if the number of atoms is the same
    if len(struct1) != len(struct2):
        return False

    ### Check if the chemical symbols are the same and in the same order
    if struct1.get_chemical_symbols() != struct2.get_chemical_symbols():
        return False

    ### Check if the cell and boundary conditions are the same
    if not np.array_equal(struct1.get_pbc(), struct2.get_pbc()):
        return False
    if not np.allclose(struct1.get_cell(), struct2.get_cell(), atol=tol):
        return False

    ### Check if the atomic positions are the same (with tolerance)
    if not np.allclose(struct1.get_scaled_positions(), struct2.get_scaled_positions(), atol=tol):
        return False

    return True


def are_structs_equivalent(struct1: Atoms, struct2: Atoms) -> bool:
    """Check if two Atoms objects are equivalent using `ase.utils.structure_comparator.SymmetryEquivalenceCheck.compare()`.

    Args:
        struct1 (Atoms): First Atoms object.
        struct2 (Atoms): Second Atoms object.

    Returns:
        bool: True if the structures are equivalent, False otherwise.

    Notes:
        - It is not clear what is "equivalent"?
    """
    from ase.utils.structure_comparator import SymmetryEquivalenceCheck

    comp = SymmetryEquivalenceCheck(stol=0.068)
    return comp.compare(struct1, struct2)


def remove_duplicate_structs_serial(extxyz_file: str, tol=1e-6) -> None:
    """Check if there are duplicate structs in a extxyz file.

    Args:
        extxyz_file (str): Path to the extxyz file.
        tol (float): Tolerance for comparing atomic positions. Defaults to 1e-6.

    Returns:
        extxyz_file without duplicate structs.
    """
    struct_list = read_extxyz(extxyz_file)
    unique_structs = []
    for struct in struct_list:
        # check if struct matches any existing unique_structures
        if not any(are_structs_identical(struct, u, tol=tol) for u in unique_structs):
            unique_structs.append(struct)

    if len(unique_structs) < len(struct_list):
        out_file = extxyz_file.replace(".extxyz", "_unique.extxyz")
        write_extxyz(out_file, unique_structs)
        num_removed = len(struct_list) - len(unique_structs)
        print(f"Removed {num_removed} duplicates from {len(struct_list)} structures.")
    else:
        print("No duplicate structures found.")
    return


def _compare_with_uniques(struct, uniques, tol):
    """Helper: check if struct matches any in uniques."""
    for u in uniques:
        if are_structs_identical(struct, u, tol=tol):
            return True
    return False


def remove_duplicate_structs_parallel(extxyz_file: str, tol=1e-6, n_jobs=None) -> None:
    """Remove duplicate structures from an extxyz file using built-in parallelism.

    Args:
        extxyz_file (str): Path to the extxyz file.
        tol (float): Tolerance for comparing atomic positions. Defaults to 1e-6.
        n_jobs (int): Number of worker processes. Defaults to None (use all cores).

    Returns:
        None. Writes a new file with unique structures.

    Notes:
        - This approach is the O(N²) pairwise checks, so it scales badly as the number of structures grows.
        - This parallel version has not helped much in practice. Use the hashing approach instead.
    """
    from concurrent.futures import ProcessPoolExecutor

    ###
    struct_list = read_extxyz(extxyz_file)
    unique_structs = []

    with ProcessPoolExecutor(max_workers=n_jobs) as executor:
        for struct in struct_list:
            # submit comparison of this struct vs current unique set
            future = executor.submit(_compare_with_uniques, struct, unique_structs, tol)
            is_dup = future.result()
            if not is_dup:
                unique_structs.append(struct)

    if len(unique_structs) < len(struct_list):
        out_file = extxyz_file.replace(".extxyz", "_unique.extxyz")
        write_extxyz(out_file, unique_structs)
        num_removed = len(struct_list) - len(unique_structs)
        print(f"Removed {num_removed} duplicates from {len(struct_list)} structures.")
    else:
        print("No duplicate structures found.")
    return


#####ANCHOR Structure hashing approach (O(N))
### The pairwise comparison approach (O(N^2)) is too slow for large datasets.
def _struct_unique_fingerprint(struct, tol=1e-6):
    """Create a hashable fingerprint consistent with `are_structs_identical` logic.

    Notes:
        - The `map(tuple, …)` trick is a quick way to turn a 2D NumPy array into something hashable (since plain NumPy arrays aren't)

    Example:
        ```python
        # If call tuple() on 2D NumPy array of shape (3, 3) (the cell matrix): tuple(np.array([[1,2,3],[4,5,6],[7,8,9]]))
        # Output gives a tuple of rows as arrays: (array([1, 2, 3]), array([4, 5, 6]), array([7, 8, 9]))
        # But `array([...])` objects aren't hashable → can't go in a `set`.
        # `map(tuple, ...)` converts each row into a plain tuple of ints: ((1,2,3), (4,5,6), (7,8,9))
        # So the purpose of `map(tuple, …)` = "turn each row (which is an array) into a tuple".
        ```
    """
    ### Sort atoms to make order deterministic
    s = sort_atoms_by_position(struct)

    ### Chemical symbols (order matters after sorting)
    symbols = tuple(s.get_chemical_symbols())

    ### Periodic boundary conditions
    pbc = tuple(s.get_pbc().tolist())

    ### Cell matrix (rounded to tolerance)
    cell = tuple(map(tuple, np.round(s.cell.array / tol).astype(int)))

    ### Scaled positions (rounded to tolerance)
    spos = tuple(map(tuple, np.round(s.get_scaled_positions() / tol).astype(int)))

    return (symbols, pbc, cell, spos)


def remove_duplicate_structs_hash(extxyz_file: str, tol=1e-6, backup=True) -> None:
    """Remove duplicate structures using hashing (very fast).

    Notes:
        - Much less memory overhead compared to pairwise `are_structs_identical` calls.
        - This reduces duplicate checking to O(N) instead of O(N²). No parallelism needed — it's already O(N)
    """
    struct_list = read_extxyz(extxyz_file)
    seen = set()
    unique_structs = []

    for struct in struct_list:
        fp = _struct_unique_fingerprint(struct, tol=tol)
        if fp not in seen:
            seen.add(fp)
            unique_structs.append(struct)

    if len(unique_structs) < len(struct_list):
        if backup:
            shutil.copy2(extxyz_file, extxyz_file.replace(".extxyz", "_bak.extxyz"))  # bak file
        write_extxyz(extxyz_file, unique_structs)
        num_removed = len(struct_list) - len(unique_structs)
        print(f"Removed {num_removed} duplicates from {len(struct_list)} structures.")
    else:
        print("No duplicate structures found.")
    return


#####!SECTION
