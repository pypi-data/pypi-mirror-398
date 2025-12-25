from thkit.pkg import check_package

try:
    check_package("spglib", auto_install=True)
except Exception as e:
    print(e)

from copy import deepcopy

import numpy as np
import spglib
from ase import Atoms, units
from scipy import optimize


#####ANCHOR Elastic tensor and related properties
class Elasticity:
    ### Ref: https://github.com/jochym/Elastic/blob/master/elastic/elastic.py
    ### Derive based on the Elastic library by Paweł T. Jochym
    """Main class to compute the elastic stiffness tensor of the crystal.
    Steps to compute the elastic tensor:
        - Initialize the class with the reference structure.
        - Generate deformed structures with 'elementary deformations'
        - Compute stress for each deformed structure by DFT/MD.
        - Input the deformed structures with stress tensors to the method `fit_elastic_tensor`
    """

    def __init__(self, ref_cryst: Atoms, symprec: float = 1e-5):
        """
        Args:
            ref_cryst (Atoms): ASE Atoms object, reference structure (relaxed/optimized structure)
            symprec (float): symmetry precision to check the symmetry of the crystal
        """
        self.ref_cryst = ref_cryst
        self.symprec = symprec
        self.bravais = get_lattice_type(self.ref_cryst, self.symprec)[0]
        ### Results
        self.strain_list = None  # list[array]
        self.stress_list = None  # list[array]
        self.pressure = None  # float
        self.Cij = None  # dict
        return

    def generate_deformations(self, delta: float = 0.01, n: int = 5):
        """Generate deformed structures with 'elementary deformations' for elastic tensor calculation.
        The deformations are created based on the symmetry of the crystal.

        Args:
            delta (float): the `maximum magnitude` of deformation in Angstrom and degrees.
            n (int): number of deformations on each non-equivalent axis (number of deformations in each direction)

        Returns:
            list[Atoms]: list of deformed structures. Number of structures = (n * number_of_axes). These structures are then used in MD/DFT to compute the stress tensor.
        """
        raw_crysts = generate_elementary_deformations(
            self.ref_cryst, delta=delta, n=n, bravais_lattice=self.bravais
        )
        return raw_crysts

    def fit_elastic_tensor(self, deform_crysts: list[Atoms]) -> tuple[np.array, np.array]:
        """Calculate elastic tensor from the stress-strain relation by fitting this relation to the set of linear equations, strains and stresses.
        The number of linear equations is computed depends on the symmetry of the crystal.

        It is assumed that the crystal is converged (relaxed/optimized) under intended pressure/stress. The geometry and stress
        on this crystal is taken as the reference point. No additional optimization will be run.
        Then, the strain and stress tensor is computed for each of the deformed structures (exactly, the stress difference from the reference point).

        This function returns tuple of Cij elastic tensor, and the fitting results returned by `numpy.linalg.lstsq`: Birch coefficients, residuals, solution rank, singular values.

        Args:
            deform_crysts (list[Atoms]): list of Atoms objects with calculated deformed structures

        Returns:
            tuple: tuple of Cij elastic tensor and fitting results.
                - Cij: in vector form of Voigt notation.
                - Bij: float vector, residuals, solution rank, singular values
        """
        ### Compute strain and stress tensors for each deformed structure
        ref_cryst = self.ref_cryst
        strain_list = [None] * len(deform_crysts)
        stress_list = [None] * len(deform_crysts)
        p = self.get_pressure(ref_cryst.get_stress())
        for i, cryst in enumerate(deform_crysts):
            strain_list[i] = get_voigt_strain_vector(cryst, ref_cryst)
            stress_list[i] = cryst.get_stress() - np.array([p, p, p, 0, 0, 0])
        ### convert the strain vector to the symmetry matrix
        bravais_lattice = self.bravais
        u_mat = np.array([strain_voigt_to_symmetry_matrix(u, bravais_lattice) for u in strain_list])
        ### Reshape
        u_mat = np.reshape(u_mat, (u_mat.shape[0] * u_mat.shape[1], u_mat.shape[2]))
        # print(u_mat.shape)
        s_mat = np.reshape(np.array(stress_list), (-1,))
        # print(s_mat)

        ### Solve the linear equation to get the Birch coefficients
        Bij = np.linalg.lstsq(u_mat, s_mat, rcond=None)

        ### Calculate elastic constants from Birch coeff.
        if bravais_lattice == "Triclinic":  # Note: verify this pressure array
            Cij = Bij[0] - np.array([-p, -p, -p, p, p, p, -p, -p, -p, p, p, p, p, p, p, p, p, p])
        elif bravais_lattice == "Monoclinic":  # Note: verify this pressure array
            Cij = Bij[0] - np.array([-p, -p, -p, p, p, p, -p, -p, -p, p, p, p, p])
        elif bravais_lattice == "Orthorhombic":
            Cij = Bij[0] - np.array([-p, -p, -p, p, p, p, -p, -p, -p])
        elif bravais_lattice == "Tetragonal":
            Cij = Bij[0] - np.array([-p, -p, p, p, -p, -p])
        elif bravais_lattice == "Trigonal":
            Cij = Bij[0] - np.array([-p, -p, p, p, -p, p])
        elif bravais_lattice == "Hexagonal":
            Cij = Bij[0] - np.array([-p, -p, p, p, -p])
        elif bravais_lattice == "Cubic":
            Cij = Bij[0] - np.array([-p, p, -p])

        ### Save results
        self.strain_list = strain_list
        self.stress_list = stress_list
        self.pressure = p
        self.raw_fit_results = Bij
        Cij = Cij / units.GPa  # convert to GPa
        Cij_dict = {k: v for k, v in zip(get_cij_list(bravais_lattice), Cij)}
        self.Cij = Cij_dict
        return

    def get_pressure(self, stress) -> float:
        """Return *external* isotropic (hydrostatic) pressure in ASE units.
        If the pressure is positive the system is under external pressure.
        This is a convenience function to convert output of get_stress function into external pressure.

        Args:
            stress(np.array: stress tensor in Voight (vector) notation as returned by the `.get_stress()` method.

        Return:
            float: external hydrostatic pressure in ASE units.
        """
        p = -np.mean(stress[:3])
        return p

    def write_cij(self, filename: str = "cij.txt"):
        """Write the elastic constants to a text file.

        Args:
            filename (str): output file name
        """
        key_string = " ".join(get_cij_list(self.bravais))
        val_string = " ".join([f"{v:.7f}" for v in self.Cij.values()])
        text = f"{key_string}\n{val_string}"
        with open(filename, "w") as f:
            f.write(text)
        return

    def fit_BM_EOS(
        self,
        deform_crysts: list[Atoms],
    ):
        """Calculate Birch-Murnaghan Equation of State for the crystal.

        $$ P(V) = \\frac{B_0}{B'_0}\\left[\\left({\\frac{V}{V_0}}\\right)^{-B'_0} - 1\\right] $$

        It's coefficients are estimated using n single-point structures ganerated from the crystal (cryst)
        by the scan_volumes function between two relative volumes. The BM EOS is fitted to the computed points by
        least squares method.

        Args:
            cryst (Atoms): Atoms object, reference structure (relaxed/optimized structure)
            deform_crysts (list[Atoms]): list of Atoms objects with calculated deformed structures

        Returns:
            tuple: tuple of EOS parameters ([V0, B0, B0p], pv data)'.
        """
        pv_2dlist = [
            [
                atoms.get_volume(),
                self.get_pressure(atoms.get_stress()),
            ]
            for atoms in deform_crysts
        ]
        pv = np.array(pv_2dlist)
        pv = pv[pv[:, 0].argsort(), :]  # sort by first column
        pv = pv.T

        ### Limiting volumes
        v1 = min(pv[0])
        v2 = max(pv[0])

        ### The pressure is falling with the growing volume
        p2 = min(pv[1])
        p1 = max(pv[1])
        b0 = (p1 * v1 - p2 * v2) / (v2 - v1)
        v0 = v1 * (p1 + b0) / b0

        ### Initial guess, assuming b0p=1
        p0 = [v0, b0, 1]

        ### Fitting
        try:
            par, succ = optimize.curve_fit(func_BMEOS, pv[0], pv[1], p0)
        except (ValueError, RuntimeError, optimize.OptimizeWarning) as e:
            raise RuntimeError(f"BM EOS fitting failed {e}")

        ### Save the results
        self.bm_eos = par
        self.pv_data = pv.T
        return

    def get_bulk_modulus(
        self,
        deform_crysts: list[Atoms],
    ):
        """Calculate bulk modulus using the Birch-Murnaghan equation of state.
        The bulk modulus is the `B_0` coefficient of the B-M EOS.
        The units of the result are defined by ASE. To get the result in
        any particular units (e.g. GPa) you need to divide it by
        ase.units.<unit name>::

            get_bulk_modulus(cryst)/ase.units.GPa

        Args:
            cryst (Atoms): Atoms object, reference structure (relaxed/optimized structure)
            deform_crysts (list[Atoms]): list of Atoms objects with calculated deformed structures

        Returns:
            float: bulk modulus `B_0` in ASE units.
        """
        self.fit_BM_EOS(deform_crysts)
        B0 = self.bm_eos[1]
        return B0

    def write_MB_EOS(self, filename: str = "BMeos.txt"):
        """Write the Birch-Murnaghan EOS parameters to a text file.

        Args:
            filename (str): output file name
        """
        header = "V0 B0 B0p"
        value = " ".join([f"{v:.7f}" for v in self.bm_eos])
        with open(filename, "w") as f:
            f.write(f"{header}\n{value}")
        return

    def write_MB_EOS_pv_data(self, filename: str = "BMeos_pv_data.txt"):
        """Write the volume-pressure data to a text file.

        Args:
            filename (str): output file name
        """
        header = "vol press"
        value = "\n".join([f"{v[0]:.7f} {v[1]:.7f}" for v in self.pv_data])
        with open(filename, "w") as f:
            f.write(f"{header}\n{value}")
        return


class ElasticConstant:
    ### https://github.com/usnistgov/atomman/blob/master/atomman/core/ElasticConstants2.py
    """Class to manage elastic constants and compute elastic properties."""

    def __init__(
        self,
        cij_mat: np.array = None,
        cij_dict: dict = None,
        bravais_lattice: str = "Cubic",
    ):
        """
        Args:
            Cij (np.array): (6, 6) array of Voigt representation of elastic stiffness.
            bravais_lattice (str): Bravais lattice name of the crystal.
            **kwargs: dictionary of elastic constants `Cij`. Where C11, C12, ... C66 : float,
        """
        if cij_mat is not None:
            if cij_mat.shape != (6, 6):
                raise ValueError("The shape of the Cij matrix must be (6, 6)")
            Cij = cij_mat
        elif cij_dict is not None:
            Cij = get_cij_6x6matrix(cij_dict, bravais_lattice)
        else:
            raise ValueError(
                "Must provide a fully elastic constants Cij 6x6 matrix, or few of its compoments based on bravais lattice."
            )
        self.Cij = Cij

        self.bravais = bravais_lattice
        ### Attributes

        return

    def Cij(self) -> np.ndarray:
        """The elastic stiffness constants in Voigt 6x6 format"""
        return self.Cij

    def Sij(self) -> np.ndarray:
        """The compliance constants in Voigt 6x6 format"""
        return np.linalg.inv(self.Cij)

    def bulk(self, style: str = "Hill") -> float:
        """
        Returns a bulk modulus estimate.

        Args:
            style(str): style of bulk modulus. Default value is 'Hill'.
                - 'Voigt': Voigt estimate. Uses Cij.
                - 'Reuss': Reuss estimate. Uses Sij.
                - 'Hill': Hill estimate (average of Voigt and Reuss).
        """
        if style == "Voigt":
            c = self.Cij
            bulk = ((c[0, 0] + c[1, 1] + c[2, 2]) + 2 * (c[0, 1] + c[1, 2] + c[0, 2])) / 9
        elif style == "Reuss":
            s = self.Sij
            bulk = 1 / ((s[0, 0] + s[1, 1] + s[2, 2]) + 2 * (s[0, 1] + s[1, 2] + s[0, 2]))
        elif style == "Hill":
            bulk = (self.bulk("Voigt") + self.bulk("Reuss")) / 2
        else:
            raise ValueError("Unknown estimate style")
        return bulk

    def shear(self, style: str = "Hill") -> float:
        """
        Returns a shear modulus estimate.

        Args:
            style(str): style of bulk modulus. Default value is 'Hill'.
                - 'Voigt': Voigt estimate. Uses Cij.
                - 'Reuss': Reuss estimate. Uses Sij.
                - 'Hill': Hill estimate (average of Voigt and Reuss).
        """
        if style == "Voigt":
            c = self.Cij
            shear = (
                (c[0, 0] + c[1, 1] + c[2, 2])
                - (c[0, 1] + c[1, 2] + c[0, 2])
                + 3 * (c[3, 3] + c[4, 4] + c[5, 5])
            ) / 15

        elif style == "Reuss":
            s = self.Sij
            shear = 15 / (
                4 * (s[0, 0] + s[1, 1] + s[2, 2])
                - 4 * (s[0, 1] + s[1, 2] + s[0, 2])
                + 3 * (s[3, 3] + s[4, 4] + s[5, 5])
            )
        elif style == "Hill":
            shear = (self.shear("Voigt") + self.shear("Reuss")) / 2
        else:
            raise ValueError("Unknown estimate style")
        return shear


#####ANCHOR Equation of State
def func_MEOS(v, v0, b0, b0p):
    """Murnaghan equation of state: https://en.wikipedia.org/wiki/Murnaghan_equation_of_state"""
    p = (b0 / b0p) * (pow(v0 / v, b0p) - 1)
    return p


def func_BMEOS(v, v0, b0, b0p):
    """Birch-Murnaghan equation of state: https://en.wikipedia.org/wiki/Birch-Murnaghan_equation_of_state"""
    p = (
        (3 / 2)
        * b0
        * ((v0 / v) ** (7 / 3) - (v0 / v) ** (5 / 3))
        * (1 + (3 / 4) * (b0p - 4) * ((v0 / v) ** (2 / 3) - 1))
    )
    return p


#####ANCHOR Generate deformed structures
def get_lattice_type(cryst: Atoms, symprec=1e-5) -> tuple[int, str, str, int]:
    """Identify the lattice type and the Bravais lattice of the crystal.
    The lattice type numbers are (numbering starts from 1):
    Triclinic (1), Monoclinic (2), Orthorhombic (3), Tetragonal (4), Trigonal (5), Hexagonal (6), Cubic (7)

    Args:
        cryst (Atoms): ASE Atoms object
        symprec (float): symmetry precision to check the symmetry of the crystal

    Returns:
        tuple: Bravais name, lattice type number (1-7), space-group name, space-group number
    """
    ### Table of lattice types and correcponding group numbers dividing the ranges.
    lattice_types = [
        [3, "Triclinic"],
        [16, "Monoclinic"],
        [75, "Orthorhombic"],
        [143, "Tetragonal"],
        [168, "Trigonal"],
        [195, "Hexagonal"],
        [231, "Cubic"],
    ]

    cell = (cryst.cell, cryst.get_scaled_positions(), cryst.numbers)
    dataset = spglib.get_symmetry_dataset(cell, symprec)
    sg_name = dataset.international
    sg_num = dataset.number

    for i, latt in enumerate(lattice_types):
        if sg_num < latt[0]:
            bravais_name = latt[1]
            latt_type = i + 1
            break
    return (bravais_name, latt_type, sg_name, sg_num)


def generate_elementary_deformations(
    cryst: Atoms,
    delta: float = 0.01,
    n: int = 5,
    bravais_lattice: str = "Cubic",
) -> list[Atoms]:
    """Generate deformed structures with 'elementary deformations' for elastic tensor calculation.
    The deformations are created based on the symmetry of the crystal and are limited to the non-equivalent axes of the crystal.

    Args:
        cryst (ase.Atoms): Atoms object, reference structure (relaxed/optimized structure)
        delta (float): the `maximum magnitude` of deformation in Angstrom and degrees.
        n (int): number of deformations on each non-equivalent axis (number of deformations in each direction)
        symprec (float): symmetry precision to check the symmetry of the crystal

    Returns:
        list[Atoms] list of deformed structures. Number of structures = (n * number_of_axes)
    """
    ### Deformation axis based on the symmetry
    deform_axis_map = {
        "Cubic": [0, 3],
        "Hexagonal": [0, 2, 3, 5],
        "Trigonal": [0, 1, 2, 3, 4, 5],
        "Tetragonal": [0, 2, 3, 5],
        "Orthorhombic": [0, 1, 2, 3, 4, 5],
        "Monoclinic": [0, 1, 2, 3, 4, 5],
        "Triclinic": [0, 1, 2, 3, 4, 5],
    }

    ### Decide which axes should be deformed
    deform_axes = deform_axis_map[bravais_lattice]
    structures = []
    for axis in deform_axes:
        if axis < 3:  # tetragonal deformation
            for dx in np.linspace(-delta, delta, n):
                structures.append(deform_1axis(cryst, axis=axis, delta=dx))
        elif axis < 6:  # sheer deformation (skip the zero angle)
            for dx in np.linspace(delta / 10.0, delta, n):
                structures.append(deform_1axis(cryst, axis=axis, delta=dx))
    return structures


def deform_1axis(
    cryst: Atoms,
    axis: int = 0,
    delta: float = 0.01,
) -> Atoms:
    """Return the deformed structure along one of the cartesian directions.
    The axis is specified as follows:

        - tetragonal deformation: 0,1,2 = x,y,z.
        - shear deformation: 3,4,5 = yz, xz, xy.

    Args:
        cryst (ase.Atoms): reference structure (structure to be deformed)
        axis (int): direction of deformation. 0,1,2 = x,y,z; 3,4,5 = yz, xz, xy.
        delta (float): magnitude of the deformation. Angstrom and degrees.

    Return:
        ase.Atoms: deformed structure
    """
    old_cell = cryst.get_cell()
    L = np.identity(3)
    if axis < 3:
        L[axis, axis] += delta
    else:
        if axis == 3:
            L[1, 2] += delta
        elif axis == 4:
            L[0, 2] += delta
        else:
            L[0, 1] += delta

    deform_cell = np.dot(old_cell, L)
    deform_cryst = deepcopy(cryst)
    deform_cryst.set_cell(deform_cell, scale_atoms=True)
    return deform_cryst


#####ANCHOR Strain matrix based on the symmetry
### Strain vector in Voight notation: [ u_xx, u_yy, u_zz, u_yz, u_xz, u_xy ]
def strain_voigt_to_symmetry_matrix(u: list, bravais_lattice: str = "Cubic") -> np.array:
    """Return the strain matrix to be used in stress-strain equation, to compute elastic tensor.
    The number of Cij constants depends on the symmetry of the crystal. This strain matrix is computed based on the symmetry to reduce the necessary number of equations to be used in the fitting procedure (also reduce the necessary calculations). Refer Landau's textbook for the details.

        - Triclinic: C11, C22, C33, C12, C13, C23, C44, C55, C66, C16, C26, C36, C46, C56, C14, C15, C25, C45
        - Monoclinic: C11, C22, C33, C12, C13, C23, C44, C55, C66, C16, C26, C36, C45
        - Orthorhombic: C11, C22, C33, C12, C13, C23, C44, C55, C66
        - Tetragonal: C11, C33, C12, C13, C44, C66
        - Trigonal: C11, C33, C12, C13, C44, C14
        - Hexagonal: C11, C33, C12, C13, C44
        - Cubic: C11, C12, C44

    Args:
        u (list): vector of strain in Voigt notation [ u_xx, u_yy, u_zz, u_yz, u_xz, u_xy ]
        bravais_lattice (str): Bravais lattice name of the lattice

    Returns:
        np.array: Symmetry defined stress-strain equation matrix
    """
    uxx, uyy, uzz, uyz, uxz, uxy = u[0], u[1], u[2], u[3], u[4], u[5]
    if bravais_lattice == "Triclinic":
        u_mat = np.array(
            [
                [uxx, 0, 0, uyy, uzz, 0, 0, 0, 0, uxy, 0, 0, 0, 0, uyz, uxz, 0, 0],
                [0, uyy, 0, uxx, 0, uzz, 0, 0, 0, 0, uxy, 0, 0, 0, 0, 0, uxz, 0],
                [0, 0, uzz, 0, uxx, uyy, 0, 0, 0, 0, 0, uxy, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 2 * uyz, 0, 0, 0, 0, 0, uxy, 0, uxx, 0, 0, uxz],
                [0, 0, 0, 0, 0, 0, 0, 2 * uxz, 0, 0, 0, 0, 0, uxy, 0, uxx, uyy, uyz],
                [0, 0, 0, 0, 0, 0, 0, 0, 2 * uxy, uxx, uyy, uzz, uyz, uxz, 0, 0, 0, 0],
            ]
        )
    elif bravais_lattice == "Monoclinic":
        u_mat = np.array(
            [
                [uxx, 0, 0, uyy, uzz, 0, 0, 0, 0, uxy, 0, 0, 0],
                [0, uyy, 0, uxx, 0, uzz, 0, 0, 0, 0, uxy, 0, 0],
                [0, 0, uzz, 0, uxx, uyy, 0, 0, 0, 0, 0, uxy, 0],
                [0, 0, 0, 0, 0, 0, 2 * uyz, 0, 0, 0, 0, 0, uxz],
                [0, 0, 0, 0, 0, 0, 0, 2 * uxz, 0, 0, 0, 0, uyz],
                [0, 0, 0, 0, 0, 0, 0, 0, 2 * uxy, uxx, uyy, uzz, 0],
            ]
        )
    elif bravais_lattice == "Orthorhombic":
        u_mat = np.array(
            [
                [uxx, 0, 0, uyy, uzz, 0, 0, 0, 0],
                [0, uyy, 0, uxx, 0, uzz, 0, 0, 0],
                [0, 0, uzz, 0, uxx, uyy, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 2 * uyz, 0, 0],
                [0, 0, 0, 0, 0, 0, 0, 2 * uxz, 0],
                [0, 0, 0, 0, 0, 0, 0, 0, 2 * uxy],
            ]
        )
    elif bravais_lattice == "Tetragonal":
        u_mat = np.array(
            [
                [uxx, 0, uyy, uzz, 0, 0],
                [uyy, 0, uxx, uzz, 0, 0],
                [0, uzz, 0, uxx + uyy, 0, 0],
                [0, 0, 0, 0, 2 * uxz, 0],
                [0, 0, 0, 0, 2 * uyz, 0],
                [0, 0, 0, 0, 0, 2 * uxy],
            ]
        )
    elif bravais_lattice == "Trigonal":
        # Note: Not tested yet. There is still some doubt about the C14 constant.
        u_mat = np.array(
            [
                [uxx, 0, uyy, uzz, 0, 2 * uxz],
                [uyy, 0, uxx, uzz, 0, -2 * uxz],
                [0, uzz, 0, uxx + uyy, 0, 0],
                [0, 0, 0, 0, 2 * uyz, -4 * uxy],
                [0, 0, 0, 0, 2 * uxz, 2 * (uxx - uyy)],
                [2 * uxy, 0, -2 * uxy, 0, 0, -4 * uyz],
            ]
        )
    elif bravais_lattice == "Hexagonal":
        # Note: still need check.
        u_mat = np.array(
            [
                [uxx, 0, uyy, uzz, 0],
                [uyy, 0, uxx, uzz, 0],
                [0, uzz, 0, uxx + uyy, 0],
                [0, 0, 0, 0, 2 * uyz],
                [0, 0, 0, 0, 2 * uxz],
                [uxy, 0, -uxy, 0, 0],
            ]
        )
    elif bravais_lattice == "Cubic":
        u_mat = np.array(
            [
                [uxx, uyy + uzz, 0],
                [uyy, uxx + uzz, 0],
                [uzz, uxx + uyy, 0],
                [0, 0, 2 * uyz],
                [0, 0, 2 * uxz],
                [0, 0, 2 * uxy],
            ]
        )
    else:
        raise ValueError(f"Unknown Bravais lattice name: {bravais_lattice}")
    return u_mat


def get_cij_list(bravais_lattice: str = "Cubic") -> list[str]:
    """Return the order of elastic constants for the structure

    Args:
        bravais_lattice (str): Bravais lattice name of the lattice

    Return:
        list: list of strings `C_ij` the order of elastic constants
    """
    # fmt: off
    cij_map = {
        "Triclinic": [
            "C11", "C22", "C33", "C12", "C13", "C23", "C44", "C55", "C66",
            "C16", "C26", "C36", "C46", "C56", "C14", "C15", "C25", "C45"],
        "Monoclinic": [
            "C11", "C22", "C33", "C12", "C13", "C23",
            "C44", "C55", "C66", "C16", "C26", "C36", "C45"],
        "Orthorhombic": [ "C11", "C22", "C33", "C12", "C13", "C23", "C44", "C55", "C66"],
        "Tetragonal": ["C11", "C33", "C12", "C13", "C44", "C66"],
        "Trigonal": ["C11", "C33", "C12", "C13", "C44", "C14"],
        "Hexagonal": ["C11", "C33", "C12", "C13", "C44"],
        "Cubic": ["C11", "C12", "C44"],
    }
    # fmt: on
    cij = cij_map[bravais_lattice]
    return cij


def get_cij_6x6matrix(cij_dict: dict[float], bravais_lattice: str = "Cubic") -> np.array:
    ### Ref: https://github.com/usnistgov/atomman/blob/master/atomman/core/ElasticConstants2.py
    ### Nye: Physical Properties of Crystals: Their Representation by Tensors and Matrices (page 140)
    """Return the Cij matrix for the structure based on the symmetry of the crystal.

    Args:
        cij_dict (dict): dictionary of elastic constants `Cij`. Where C11, C12, ... C66 : float, Individual components of Cij for a standardized representation:

            - Triclinic: all Cij where i <= j
            - Monoclinic: C11, C12, C13, C15, C22, C23, C25, C33, C35, C44, C46, C55, C66
            - Orthorhombic: C11, C12, C13, C22, C23, C33, C44, C55, C66
            - Tetragonal: C11, C12, C13, C16, C33, C44, C66 (C16 optional)
            - Trigonal: C11, C12, C13, C14, C33, C44
            - Hexagonal: C11, C12, C13, C33, C44, C66 (2*C66=C11-C12)
            - Cubic: C11, C12, C44
            - Isotropic: C11, C12, C44 (2*C44=C11-C12)

        bravais_lattice (str): Bravais lattice name of the lattice
    """

    cij_list = get_cij_list(bravais_lattice)
    cij_keys = list(cij_dict.keys())
    if not set(cij_keys).issubset(cij_list):
        raise ValueError(f"Lattice type {bravais_lattice} requires list of Cij: {cij_list}")
    else:
        c = cij_dict
    # fmt: off
    if bravais_lattice == "Triclinic":
        C11, C12, C13, C14, C15, C16 = c["C11"], c["C12"], c["C13"], c["C14"], c["C15"], c["C16"]
        C22, C23, C24, C25, C26 = c["C22"], c["C23"], c["C24"], c["C25"], c["C26"]
        C33, C34, C35, C36 = c["C33"], c["C34"], c["C35"], c["C36"]
        C44, C45, C46, C55, C56, C66 = c["C44"], c["C45"], c["C46"], c["C55"], c["C56"], c["C66"]
        cij_mat = np.array([
                            [C11, C12, C13, C14, C15, C16],
                            [C12, C22, C23, C24, C25, C26],
                            [C13, C23, C33, C34, C35, C36],
                            [C14, C24, C34, C44, C45, C46],
                            [C15, C25, C35, C45, C55, C56],
                            [C16, C26, C36, C46, C56, C66]])

    elif bravais_lattice == "Monoclinic":
        C11, C12, C13, C15, C22, C23, C25 = c["C11"], c["C12"], c["C13"], c["C15"], c["C22"], c["C23"], c["C25"]
        C33, C35, C44, C46, C55, C66 = c["C33"], c["C35"], c["C44"], c["C46"], c["C55"], c["C66"]
        cij_mat = np.array([
                            [C11, C12, C13, 0.0, C15, 0.0],
                            [C12, C22, C23, 0.0, C25, 0.0],
                            [C13, C23, C33, 0.0, C35, 0.0],
                            [0.0, 0.0, 0.0, C44, 0.0, C46],
                            [C15, C25, C35, 0.0, C55, 0.0],
                            [0.0, 0.0, 0.0, C46, 0.0, C66]])

    elif bravais_lattice == "Orthorhombic":
        C11, C12, C13, C22, C23 = c["C11"], c["C12"], c["C13"], c["C22"], c["C23"]
        C33, C44, C55, C66 = c["C33"], c["C44"], c["C55"], c["C66"]
        cij_mat = np.array([
                            [C11, C12, C13, 0.0, 0.0, 0.0],
                            [C12, C22, C23, 0.0, 0.0, 0.0],
                            [C13, C23, C33, 0.0, 0.0, 0.0],
                            [0.0, 0.0, 0.0, C44, 0.0, 0.0],
                            [0.0, 0.0, 0.0, 0.0, C55, 0.0],
                            [0.0, 0.0, 0.0, 0.0, 0.0, C66]])

    elif bravais_lattice == "Tetragonal":
        C11, C12, C13, C33, C44, C66 = c["C11"], c["C12"], c["C13"], c["C33"], c["C44"], c["C66"]
        C16 = 0.0
        if "C16" in cij_list:
            C16 = c["C16"]
        cij_mat = np.array([
                            [C11, C12, C13, 0.0, 0.0, C16],
                            [C12, C11, C13, 0.0, 0.0,-C16],
                            [C13, C13, C33, 0.0, 0.0, 0.0],
                            [0.0, 0.0, 0.0, C44, 0.0, 0.0],
                            [0.0, 0.0, 0.0, 0.0, C44, 0.0],
                            [C16,-C16, 0.0, 0.0, 0.0, C66]])

    elif bravais_lattice == "Trigonal":
        C11, C12, C13, C14, C33, C44 = c["C11"], c["C12"], c["C13"], c["C14"], c["C33"], c["C44"]
        C15 = 0.0
        if "C15" in cij_list:
            C15 = c["C15"]
        C66 = (C11 - C12) / 2
        cij_mat = np.array([
                            [C11, C12, C13, C14, C15, 0.0],
                            [C12, C11, C13,-C14,-C15, 0.0],
                            [C13, C13, C33, 0.0, 0.0, 0.0],
                            [C14,-C14, 0.0, C44, 0.0,-C15],
                            [C15,-C15, 0.0, 0.0, C44, C14],
                            [0.0, 0.0, 0.0,-C15, C14, C66]])

    elif bravais_lattice == "Hexagonal":
        C11, C12, C13, C33, C44 = c["C11"], c["C12"], c["C13"], c["C33"], c["C44"]
        C66 = (C11 - C12) / 2
        cij_mat = np.array([
                            [C11, C12, C13, 0, 0, 0],
                            [C12, C11, C13, 0, 0, 0],
                            [C13, C13, C33, 0, 0, 0],
                            [0, 0, 0, C44, 0, 0],
                            [0, 0, 0, 0, C44, 0],
                            [0, 0, 0, 0, 0, C66]])

    elif bravais_lattice == "Cubic":
        C11, C12, C44 = c["C11"], c["C12"], c["C44"]
        cij_mat = np.array([
                            [C11, C12, C12, 0, 0, 0],
                            [C12, C11, C12, 0, 0, 0],
                            [C12, C12, C11, 0, 0, 0],
                            [0, 0, 0, C44, 0, 0],
                            [0, 0, 0, 0, C44, 0],
                            [0, 0, 0, 0, 0, C44]])
    # fmt: on
    else:
        raise ValueError(f"Unknown Bravais lattice name: {bravais_lattice}")
    return cij_mat


#####ANCHOR Compute strain tensor
def get_voigt_strain_vector(cryst: Atoms, ref_cryst: Atoms = None) -> np.array:
    """Calculate the strain tensor between the deformed structure and the reference structure.
    Return strain in vector form of Voigt notation, component order: u_{xx}, u_{yy}, u_{zz}, u_{yz}, u_{xz}, u_{xy}.

    Args:
        cryst (ase.Atoms): deformed structure
        ref_cryst (ase.Atoms): reference, undeformed structure

    Returns:
        np.array: vector of strain in Voigt notation.
    """
    if ref_cryst is None:
        ref_cryst = cryst
    deform_cell = cryst.get_cell()
    ref_cell = ref_cryst.get_cell()
    du = deform_cell - ref_cell
    m = np.linalg.inv(ref_cell)
    u = np.dot(m, du)  # strain tensor
    u = (u + u.T) / 2
    u_vect = np.array([u[0, 0], u[1, 1], u[2, 2], u[2, 1], u[2, 0], u[1, 0]])
    return u_vect
