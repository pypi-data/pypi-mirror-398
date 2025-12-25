import numpy as np
from ase import Atoms
from ase.parallel import paropen
from phonopy import Phonopy
from phonopy.file_IO import parse_BORN

from alff.phonon.utilpho import convert_ase2phonopy


#####ANCHOR from gpaw_tools
### https://github.com/lrgresearch/gpaw-tools
def _ref_phonon_calc(
    atoms: Atoms,
    calc: object,
    supercell_matrix=[[2, 0, 0], [0, 2, 0], [0, 0, 2]],
    displacement=0.01,
    NAC: bool = False,
) -> object:
    ### https://github.com/lrgresearch/gpaw-tools/blob/main/gpawsolve.py#L1086
    # References:
    # - [1] https://phonopy.github.io/phonopy/
    # - [2] https://github.com/abelcarreras/phonolammps
    # - [3] https://github.com/lrgresearch/gpaw-tools
    """
    NOTE: this function is note be used. just for reference.

    Args:
        atoms (Atoms): ASE's structure object which is already optimized/relaxed as the ground state.
        calc (object): ASE calculator object.
        supercell_matrix (list): The supercell matrix for the phonon calculation.
        displacement (float): The atomic displacement distance in Angstrom.
        NAC (bool): Whether to use non-analytical corrections (NAC) for the phonon calculation.


    NOTE: not yet finished
    """
    atoms.calc = calc

    ### Pre-process
    atoms_ph = convert_ase2phonopy(atoms)
    phonon = Phonopy(atoms_ph, supercell_matrix, log_level=1)
    phonon.generate_displacements(distance=displacement)
    with paropen("log_phonon_displacement.txt", "a") as f:
        print("[Phonopy] Atomic displacements:", end="\n", file=f)
        disps = phonon.get_displacements()
        for d in disps:
            print(f"[Phonopy] {d[0]} {d[1:]}", end="\n", file=f)

    # FIX THIS PART
    # path = get_band_path(atoms, Phonon_path, Phonon_npoints)

    # phonon_path = "5-Results-force-constants.npy"
    # sum_rule = Phonon_acoustic_sum_rule

    # if os.path.exists(phonon_path):
    #     with paropen("-5-Log-Phonon-Phonopy.txt", "a") as f2:
    #         print("Reading FCs from {!r}".format(phonon_path), end="\n", file=f2)
    #     phonon.force_constants = np.load(phonon_path)
    # else:
    #     with paropen("-5-Log-Phonon-Phonopy.txt", "a") as f2:
    #         print("Computing FCs", end="\n", file=f2)
    #         # os.makedirs('force-sets', exist_ok=True)
    #     supercells = list(phonon.get_supercells_with_displacements())
    #     fnames = ["5-Results-sc-{:04}.npy".format(i) for i in range(len(supercells))]
    #     set_of_forces = [
    #         load_or_compute_force(fname, calc, supercell)
    #         for (fname, supercell) in zip(fnames, supercells)
    #     ]
    #     with paropen("-5-Log-Phonon-Phonopy.txt", "a") as f2:
    #         print("Building FC matrix", end="\n", file=f2)
    #     phonon.produce_force_constants(forces=set_of_forces, calculate_full_force_constants=False)
    #     if sum_rule:
    #         phonon.symmetrize_force_constants()
    #     with paropen("-5-Log-Phonon-Phonopy.txt", "a") as f2:
    #         print("Writing FCs to {!r}".format(phonon_path), end="\n", file=f2)
    #     np.save(phonon_path, phonon.get_force_constants())
    #     # shutil.rmtree('force-sets')

    with paropen("-5-Log-Phonon-Phonopy.txt", "a") as f2:
        print("", end="\n", file=f2)
        print("[Phonopy] Phonon frequencies at Gamma:", end="\n", file=f2)
        for i, freq in enumerate(phonon.get_frequencies((0, 0, 0))):
            print("[Phonopy] %3d: %10.5f THz" % (i + 1, freq), end="\n", file=f2)  # THz

        # DOS
        phonon.set_mesh([21, 21, 21])
        phonon.set_total_DOS(tetrahedron_method=True)
        print("", end="\n", file=f2)
        print("[Phonopy] Phonon DOS:", end="\n", file=f2)
        for omega, dos in np.array(phonon.get_total_DOS()).T:
            print("%15.7f%15.7f" % (omega, dos), end="\n", file=f2)

    # qpoints, labels, connections = path
    # phonon.run_band_structure(qpoints, path_connections=connections, labels=labels)

    if NAC:  # https://github.com/abelcarreras/phonolammps/blob/master/phonolammps/phonopy_link.py
        print("Using non-analytical corrections")
        primitive = phonon.get_primitive()
        try:
            nac_params = parse_BORN(primitive, is_symmetry=True)
            phonon.set_nac_params(nac_params=nac_params)
        except OSError:
            print("Required BORN file not found!")
            exit()

    return phonon
