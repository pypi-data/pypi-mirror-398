"""General utility functions for ALFF."""

from pathlib import Path

import pyfiglet

from alff import ALFF_ROOT, __author__, __contact__, __version__
from thkit.markup import TextDecor
from thkit.pkg import dependency_info


#####ANCHOR pkg info
def alff_logo():
    text = pyfiglet.figlet_format("ALFF", justify="center", width=70, font="slant")
    return text


def alff_info_text(
    packages=["ase", "numpy", "scipy", "sevenn", "phonopy", "thkit", "asext"],
):
    text = "{}\n".format(TextDecor(" ALFF ").fill_center(fill="=", length=70))
    text += "{:>12}  {:13} {}\n".format("Ver", __version__, Path(ALFF_ROOT).as_posix())
    text += dependency_info(packages)
    text += "{}\n{}\n".format(
        TextDecor(f" {__author__} ").fill_center(fill="-", length=70),
        TextDecor(f" {__contact__} ").fill_center(fill="-", length=70),
    )
    # text += "{}\n{}\n".format(
    #     TextDecor(f"Author: {__author__}").fill_left(margin=15, length=70),
    #     TextDecor(f"Contact: {__contact__}").fill_left(margin=15, length=70),
    # )
    text += f"\n{alff_logo()}"
    return text


def alff_info_shorttext():
    text = "{}\n{}\n{}\n{}\n{}\n".format(
        TextDecor("").fill_box(fill="=", sp="", length=70),
        TextDecor(f"ALFF {__version__}").fill_box(fill=" ", sp="\u2016", length=70),
        TextDecor(f" {__author__} ").fill_box(fill=" ", sp="\u2016", length=70),
        TextDecor(f" {__contact__} ").fill_box(fill=" ", sp="\u2016", length=70),
        TextDecor("").fill_box(fill="=", sp="", length=70),
    )
    text += f"\n{alff_logo()}"
    return text


#####SECTION functinons for calculator processes
def check_supported_calculator(calculator: str):
    """Check if the calculator is supported."""
    supported_calculators = ["gpaw", "lammps"]
    if calculator not in supported_calculators:
        raise ValueError(
            f"Unsupported calculator: {calculator}. Available calculators: {supported_calculators}"
        )
    return


#####!SECTION


#####SECTION functinons for data_generation process
def mk_struct_dir(pdict):
    """Create the directory name for the structure."""
    structure = pdict["structure"]
    from_extxyz = structure.get("from_extxyz", None)
    if from_extxyz is not None:
        if isinstance(from_extxyz, list):
            dir_name = Path(from_extxyz[0]).stem
        elif isinstance(from_extxyz, str):
            dir_name = Path(from_extxyz).stem
    else:
        struct_args = structure.get("from_scratch", None)
        supercell = struct_args.get("supercell", [1, 1, 1])
        cell_str = "x".join([f"{a:02d}" for a in supercell])
        symbols = struct_args["chem_formula"]
        # symbol_str = "".join([e.lower() for e in symbols])
        symbol_str = symbols
        structure_type = struct_args["structure_type"]
        if structure_type == "bulk":
            crystal = struct_args["ase_build_arg"].get("crystalstructure", "sc")
            structure_type = f"{structure_type}_{crystal}"
        elif structure_type == "mx2":
            kind = struct_args["ase_build_arg"].get("kind", "2H")
            structure_type = f"{structure_type}_{kind}"

        dir_name = f"{symbol_str}_{structure_type}_{cell_str}"
    return dir_name  # type: ignore[unbound]


#####!SECTION


#####SECTION functinons for plot
