import io
import copy
import json
import numpy as np
import ase
import itertools

from collections import namedtuple
from collections.abc import Callable
from typing import Self

from ase.optimize import FIRE

from rdkit import Chem
from rdkit.Chem import rdMolTransforms, rdmolops, rdFreeSASA
from PIL import Image

from rdworks.std import clean_2d
from rdworks.torsion import get_torsion_angle_atom_indices, create_torsion_fragment
from rdworks.xtb.wrapper import GFN2xTB
from rdworks.view import render_png, render_svg

import rdworks.units
import rdworks.utils

ptable = Chem.GetPeriodicTable()


class Conf:
    """Container for 3D conformers."""

    def __init__(
        self,
        molecule: str | Chem.Mol | None = None,
        name: str = "",
        compressed: bool = False,
    ) -> None:
        """Initialize.

        Args:
            molecule (Chem.Mol | MolBlock string): Molecule for 3D conformer.
            name (str): Name prefix of the generated conformers. Defaults to ''.
            compressed (bool): whether the MolBlock string is compressed or not.
                Defaults to False.

        Raises:
            ValueError: if `molecule` is not rdkit.Chem.Mol object.
        """
        assert isinstance(molecule, str | Chem.Mol) or molecule is None

        self.name = name
        self.rdmol = None  # must contain one and only one rdkit conformer
        self.natoms = 0
        self.charge = 0  # molecular formal charge
        self.spin = 1  # molecular spin multiplicity for ASE
        # Molecular spin multiplicity describes the number of possible orientations of
        # spin angular momentum for a given molecule, essentially indicating the total
        # number of unpaired electrons.
        # Spin Angular Momentum (S): up (+1/2) or down (-1/2)
        # Spin Multiplicity (2S + 1)
        # 0 unpaired electron  has S = 0,   2S + 1 = 0, called a singlet.
        # 1 unpaired electron  has S = 1/2, 2S + 1 = 2, called a doublet (radical).
        # 2 unpaired electrons has S = 1,   2S + 1 = 3, called a triplet.
        self.smiles = ""
        self.molblock = ""
        self.symbols = []
        self.numbers = []
        self.positions = np.array([])  # (natoms, 3)
        self.props = {}

        if molecule is None:
            return

        if isinstance(molecule, str):  # 3-D MolBLock string
            if compressed:
                molecule = rdworks.utils.decompress_string(molecule)
            try:
                self.rdmol = Chem.MolFromMolBlock(
                    molecule, sanitize=False, removeHs=False, strictParsing=True
                )
            except:
                ValueError(f"Conf() Error: invalid MolBlock string")

        elif isinstance(molecule, Chem.Mol):  # 3-D
            try:
                self.rdmol = molecule
            except:
                ValueError(f"Conf() Error: invalid Chem.Mol object")

        self._update()

    def _update(self) -> None:
        self.smiles = Chem.MolToSmiles(self.rdmol)
        self.molblock = Chem.MolToMolBlock(self.rdmol)
        self.symbols = [a.GetSymbol() for a in self.rdmol.GetAtoms()]
        self.numbers = [a.GetAtomicNum() for a in self.rdmol.GetAtoms()]
        self.positions = self.rdmol.GetConformer().GetPositions()  # np.ndarray
        # check hydrogens
        num_atoms = self.rdmol.GetNumAtoms()
        tot_atoms = self.rdmol.GetNumAtoms(onlyExplicit=False)
        assert num_atoms == tot_atoms, "Conf() Error: missing hydrogens"
        self.natoms = num_atoms
        self.charge = rdmolops.GetFormalCharge(self.rdmol)
        self.props.update(
            {
                "atoms": self.natoms,
                "charge": self.charge,
            }
        )

        assert self.rdmol.GetConformer().Is3D(), "Conf() Error: not 3D"

    def __str__(self) -> str:
        """Returns a string representation.

        Returns:
            str: string representation.
        """
        return f"<rdworks.Conf({self.rdmol} name={self.name} atoms={self.natoms})>"

    ##################################################
    ### Properties
    ##################################################

    @property
    def COG(self) -> np.array:
        """Returns the center of geometry (COG).

        Returns:
            np.array: the center of geometry.
        """
        xyz = []
        for i in range(0, self.natoms):
            pos = self.rdmol.GetConformer().GetAtomPositions(i)
            xyz.append([pos.x, pos.y, pos.z])
        return np.mean(xyz, axis=0)

    @property
    def Rg(self) -> float:
        """Returns the radius of gyration (Rg).

        Returns:
            float: the radius of gyration.
        """
        xyz = []
        for i in range(0, self.natoms):
            pos = self.rdmol.GetConformer().GetAtomPositions(i)
            xyz.append([pos.x, pos.y, pos.z])
        xyz = np.array(xyz)
        cog = np.mean(xyz, axis=0)
        a = xyz - cog
        b = np.einsum("ij,ij->i", a, a)
        return np.sqrt(np.mean(b))

    @property
    def SASA(self) -> dict:
        """Calculate Solvent Accessible Surface Area (total, polar, apolar).

        Returns:
            tuple[float, float, float]: (total, polar, apolar)
        """
        radii = [ptable.GetRvdw(atom.GetAtomicNum()) for atom in self.rdmol.GetAtoms()]

        # CalcSASA signature: CalcSASA(mol, radii, confId=conf_id) in modern RDKit
        total_sasa = rdFreeSASA.CalcSASA(self.rdmol, radii=radii, confIdx=-1)

        # try to read per-atom SASA values set by CalcSASA into atoms
        atom_sasas = [atom.GetDoubleProp("SASA") for atom in self.rdmol.GetAtoms()]

        # Now compute polar/apolar sums: polar = N,O and Hs attached to them
        polar_idx = set()
        for atom in self.rdmol.GetAtoms():
            if atom.GetAtomicNum() in (7, 8):  # N or O
                polar_idx.add(atom.GetIdx())
                # include attached hydrogens
                for nbr in atom.GetNeighbors():
                    if nbr.GetAtomicNum() == 1:
                        polar_idx.add(nbr.GetIdx())

        # default numeric 0 for None entries (defensive)
        numeric_atom_sasas = [0.0 if v is None else float(v) for v in atom_sasas]
        sasa_polar = sum(numeric_atom_sasas[i] for i in polar_idx)
        sasa_total = sum(numeric_atom_sasas)
        sasa_apolar = sasa_total - sasa_polar

        return rdworks.utils.recursive_round(
            {
                "sasa_total": sasa_total,
                "sasa_polar": sasa_polar,
                "sasa_apolar": sasa_apolar,
            },
            decimals=2,
        )

    def copy(self) -> Self:
        """Returns a copy of self.

        Returns:
            Self: `rdworks.Conf` object.
        """
        return copy.deepcopy(self)

    def rename(self, name: str) -> Self:
        """Rename and returns self.

        Args:
            name (str): a new name for conformers.

        Raises:
            ValueError: if `name` is not given.

        Returns:
            Self: `rdworks.Conf` object.
        """
        if not name:
            raise ValueError("rdworks.Conf.rename() expects a name")
        self.name = name
        self.rdmol.SetProp("_Name", name)
        return self

    def sync(self, coord: np.ndarray | list) -> Self:
        """Synchronize the conformer coordinates with the provided `coord`.

        Args:
            coord (np.array): 3D coordinates.

        Raises:
            ValueError: if `coord` does not have the correct shape (natoms, 3).

        Returns:
            Self: `rdworks.Conf` object.
        """
        if isinstance(coord, np.ndarray) and coord.shape != (self.natoms, 3):
            raise ValueError(f"`coord.shape` should be ({self.natoms},3)")
        elif isinstance(coord, list) and len(coord) != self.natoms:
            raise ValueError(f"`coord` should be length of {self.natoms}")
        for i, a in enumerate(self.rdmol.GetAtoms()):
            self.rdmol.GetConformer().SetAtomPosition(a.GetIdx(), coord[i])

        return self

    def get_torsion_angle_atoms(self, strict: bool = True) -> list[tuple]:
        """Determine torsion/dihedral angle atoms (i-j-k-l) and rotating group for each rotatable bond (j-k).

        Args:
            strict (bool): whether to exclude amide/imide/ester/acid bonds.

        Returns:
            [(i, j, k, l), ...]
        """
        return [d[:4] for d in get_torsion_angle_atom_indices(self.rdmol, strict)]

    def get_torsion_angle(self, i: int, j: int, k: int, l: int) -> float:
        """Get dihedral angle (i-j-k-l) in degrees.

        Args:
            i (int): atom index
            j (int): atom index
            k (int): atom index
            l (int): atom index

        Returns:
            float: dihedral angle in degrees.
        """
        degree = rdMolTransforms.GetDihedralDeg(self.rdmol.GetConformer(), i, j, k, l)

        return degree

    def set_torsion_angle(self, i: int, j: int, k: int, l: int, degree: float) -> Self:
        """Set dihedral angle (i-j-k-l) in degrees.

        Args:
            i (int): atom index
            j (int): atom index
            k (int): atom index
            l (int): atom index
            degree (float): dihedral angle in degrees

        Returns:
            Self: modified Conf object
        """
        rdMolTransforms.SetDihedralDeg(self.rdmol.GetConformer(), i, j, k, l, degree)

        return self

    def protonate(self, atom_indices: list[int]) -> Self:
        """Protonate given non-hydrogen atoms.

        Args:
            atom_indices (list[int]): atom indices of non-hydrogen atoms to protonate.

        Returns:
            Self: self.
        """
        for idx in atom_indices:
            atom = self.rdmol.GetAtomWithIdx(idx)
            h = atom.GetNumExplicitHs()
            c = atom.GetFormalCharge()
            atom.SetNumExplicitHs(h + 1)
            atom.SetFormalCharge(c + 1)
            Chem.SanitizeMol(self.rdmol)
            self.rdmol = Chem.AddHs(self.rdmol, addCoords=True)
            # The Chem.AddHs function in RDKit returns a new Mol object with hydrogens added to the molecule.
            # It modifies the input molecule by adding hydrogens,
            # but the original molecule remains unchanged.

        self._update()

        return self

    def deprotonate(self, atom_indices: list[int]) -> Self:
        """Deprotonate given non-hydrogen atoms.

        Args:
            atom_indices (list[int]): atom indices of non-hydrogen atoms to deprotonate.

        Returns:
            Self: self.
        """
        for idx in atom_indices:
            bonded_H_idx = None
            atom = self.rdmol.GetAtomWithIdx(idx)
            h = atom.GetNumExplicitHs()
            if h - 1 >= 0:
                atom.SetNumExplicitHs(h - 1)  # (h-1) must be unsigned int
            c = atom.GetFormalCharge()
            atom.SetFormalCharge(c - 1)
            neighbors = atom.GetNeighbors()

            for neighbor in neighbors:
                if neighbor.GetAtomicNum() == 1:
                    bonded_H_idx = neighbor.GetIdx()
                    break

            if bonded_H_idx is not None:
                edit_mol = Chem.EditableMol(self.rdmol)
                edit_mol.RemoveAtom(bonded_H_idx)
                self.rdmol = edit_mol.GetMol()
                Chem.SanitizeMol(self.rdmol)

        self._update()

        return self

    ##################################################
    ### Endpoint methods
    ##################################################

    def has_acceptable_bond_lengths(self, tolerance: float = 0.25) -> bool:
        """Check bond length.

        Args:
            tolerance (float, optional): tolerance from the sum of
                van der Waals radii of bonded atoms. Defaults to 0.25 (A).

        Returns:
            bool: True if all bond lengths are accceptable.
        """

        pt = Chem.GetPeriodicTable()

        for bond in self.rdmol.GetBonds():
            idx1 = bond.GetBeginAtomIdx()
            idx2 = bond.GetEndAtomIdx()
            nuc1 = self.rdmol.GetAtomWithIdx(idx1).GetAtomicNum()
            nuc2 = self.rdmol.GetAtomWithIdx(idx2).GetAtomicNum()
            sum_radii = pt.GetRvdw(nuc1) + pt.GetRvdw(nuc2)  # (A)
            # from mendeleev import element
            # sum_radii = (element(nuc1).vdw_radius + element(nuc2).vdw_radius) * pm2angstrom
            bond_length = rdMolTransforms.GetBondLength(
                self.rdmol.GetConformer(), idx1, idx2
            )
            if abs(bond_length - sum_radii) > tolerance:
                return False

        return True

    def singlepoint(
        self, calculator: str | Callable = "MMFF94", water: str | None = None
    ) -> Self:
        """Get potential energy and set `E_tot(kcal/mol)` in the self.props.

        Args:
            calculator (str | Callable): MMFF94 (= MMFF), MMFF94s, UFF, xTB, or ASE calculator.
                `MMFF94` or `MMFF` - Intended for general use, including organic molecules and proteins,
                    and primarily relies on data from quantum mechanical calculations.
                    It's often used in molecular dynamics simulations.
                `MMFF94s` - A "static" variant of MMFF94, with adjusted parameters for out-of-plane
                    bending and dihedral torsions to favor planar geometries for specific nitrogen atoms.
                    This makes it better suited for geometry optimization studies where a static,
                    time-averaged structure is desired. The "s" stands for "static".
                `UFF` - UFF refers to the "Universal Force Field," a force field model used for
                    molecular mechanics calculations. It's a tool for geometry optimization,
                    energy minimization, and exploring molecular conformations in 3D space.
                    UFF is often used to refine conformers generated by other methods,
                    such as random conformer generation, to produce more physically plausible
                    and stable structures.
                'xTB' - GFN2-xTB

        Args for xTB:
            water (str, optional): water solvation model (choose 'gbsa' or 'alpb')
                alpb: ALPB solvation model (Analytical Linearized Poisson-Boltzmann).
                gbsa: generalized Born (GB) model with Surface Area contributions.
                Defaults to None.

        Returns:
            float | None: potential energy in kcal/mol or None.
        """
        if isinstance(calculator, str):
            if calculator.lower() == "xTB".lower():
                results = GFN2xTB(self.rdmol).singlepoint(water=water)
                # results = SimpleNamespace(
                #     PE = datadict['total energy'] * hartree2kcalpermol,
                #     Gsolv = Gsolv,
                #     charges = datadict['partial charges'],
                #     wbo = Wiberg_bond_orders,
                #     )
                PE = results.PE

            elif (
                calculator.lower() == "MMFF94".lower()
                or calculator.lower() == "MMFF".lower()
            ):
                mp = Chem.rdForceFieldHelpers.MMFFGetMoleculeProperties(
                    self.rdmol, mmffVariant="MMFF94"
                )
                ff = Chem.rdForceFieldHelpers.MMFFGetMoleculeForceField(self.rdmol, mp)
                PE = ff.CalcEnergy()

            elif calculator.lower() == "MMFF94s".lower():
                mp = Chem.rdForceFieldHelpers.MMFFGetMoleculeProperties(
                    self.rdmol, mmffVariant="MMFF94s"
                )
                ff = Chem.rdForceFieldHelpers.MMFFGetMoleculeForceField(self.rdmol, mp)
                PE = ff.CalcEnergy()

            elif calculator.lower() == "UFF".lower():
                ff = Chem.rdForceFieldHelpers.UFFGetMoleculeForceField(self.rdmol)
                PE = ff.CalcEnergy()

            else:
                raise ValueError("Unsupported calculator")

            self.props.update({"E_tot(kcal/mol)": PE})

            return self

        else:
            try:
                ase_atoms = ase.Atoms(symbols=self.symbols, positions=self.positions)
                ase_atoms.info["charge"] = self.charge
                ase_atoms.info["spin"] = self.spin
                ase_atoms.calc = calculator
                PE = ase_atoms.get_potential_energy()  # np.array
                if isinstance(PE, float):
                    PE = rdworks.units.ev2kcalpermol * PE
                elif isinstance(PE, np.ndarray | list):
                    PE = rdworks.units.ev2kcalpermol * float(
                        PE[0]
                    )  # np.float64 to float
                self.props.update({"E_tot(kcal/mol)": PE})

                return self

            except:
                raise RuntimeError("ASE calculator error")

    def optimize(
        self,
        calculator: str | Callable = "MMFF94",
        fmax: float = 0.05,
        max_iter: int = 1000,
        water: str | None = None,
    ) -> Self:
        """Optimize 3D geometry.

        Args:
            calculator (str | Callable): MMFF94 (= MMFF), MMFF94s, UFF, xTB or ASE calculator.
                `MMFF94` or `MMFF` - Intended for general use, including organic molecules and proteins,
                    and primarily relies on data from quantum mechanical calculations.
                    It's often used in molecular dynamics simulations.
                `MMFF94s` - A "static" variant of MMFF94, with adjusted parameters for out-of-plane
                    bending and dihedral torsions to favor planar geometries for specific nitrogen atoms.
                    This makes it better suited for geometry optimization studies where a static,
                    time-averaged structure is desired. The "s" stands for "static".
                `UFF` - UFF refers to the "Universal Force Field," a force field model used for
                    molecular mechanics calculations. It's a tool for geometry optimization,
                    energy minimization, and exploring molecular conformations in 3D space.
                    UFF is often used to refine conformers generated by other methods,
                    such as random conformer generation, to produce more physically plausible
                    and stable structures.
            fmax (float, optional): fmax for the calculator convergence. Defaults to 0.05.
            max_iter (int, optional): max iterations for the calculator. Defaults to 1000.

        Args for xTB calculator:
            water (str, optional): water solvation model (choose 'gbsa' or 'alpb')
                alpb: ALPB solvation model (Analytical Linearized Poisson-Boltzmann).
                gbsa: generalized Born (GB) model with Surface Area contributions.
                Defaults to None.

        Returns:
            Self: self
        """
        if isinstance(calculator, str):
            PE_start = self.singlepoint(calculator).props.get("E_tot(kcal/mol)")
            PE_final = None

            if calculator.lower() == "xTB".lower():
                results = GFN2xTB(self.rdmol).optimize(water=water)
                # results = SimpleNamespace(
                #         PE = datadict['total energy'] * hartree2kcalpermol,
                #         charges = datadict['partial charges'],
                #         wbo = Wiberg_bond_orders,
                #         geometry = rdmol_opt,
                # )
                try:
                    self.rdmol = results.geometry
                    PE_final = results.PE
                    retcode = 0
                except:
                    retcode = 1

            elif (
                calculator.lower() == "MMFF94".lower()
                or calculator.lower() == "MMFF".lower()
            ):
                retcode = Chem.rdForceFieldHelpers.MMFFOptimizeMolecule(
                    self.rdmol, mmffVariant="MMFF94", maxIters=max_iter
                )
                # returns 0 if the optimization converged
            elif calculator.lower() == "MMFF94s".lower():
                retcode = Chem.rdForceFieldHelpers.MMFFOptimizeMolecule(
                    self.rdmol, mmffVariant="MMFF94s", maxIters=max_iter
                )
                # returns 0 if the optimization converged
            elif calculator.lower() == "UFF".lower():
                retcode = Chem.rdForceFieldHelpers.UFFOptimizeMolecule(
                    self.rdmol, maxIters=max_iter
                )
                # returns 0 if the optimization converged

            if PE_final is None:
                PE_final = self.singlepoint(calculator).props.get("E_tot(kcal/mol)")

            self.props.update(
                {
                    "E_tot_init(kcal/mol)": PE_start,  # energy before optimization
                    "E_tot(kcal/mol)": PE_final,  # energy after optimization
                    "Converged": retcode == 0,  # True or False
                }
            )

            return self

        else:
            # assuming ASE calculator
            with io.StringIO() as logfile:
                ase_atoms = ase.Atoms(symbols=self.symbols, positions=self.positions)
                ase_atoms.info["charge"] = self.charge
                ase_atoms.info["spin"] = self.spin
                ase_atoms.calc = calculator
                FIRE(ase_atoms, logfile=logfile).run(fmax=fmax)
                lines = [
                    l.strip().split()[1:]
                    for l in logfile.getvalue().split("\n")
                    if l.startswith("FIRE")
                ]
                data = [(float(e), float(f)) for (_, _, e, f) in lines]
                self.props.update(
                    {
                        "E_tot_init(kcal/mol)": data[0][0]
                        * rdworks.units.ev2kcalpermol,  # energy before optimization
                        "E_tot(kcal/mol)": data[-1][0]
                        * rdworks.units.ev2kcalpermol,  # energy after optimization
                        "Converged": data[-1][1] < fmax,  # True or False
                    }
                )

                # update atomic coordinates
                return self.sync(ase_atoms.get_positions())

    def calculate_torsion_energies_one(
        self,
        calculator: str | Callable,
        indices: tuple[int],
        simplify: bool = True,
        fmax: float = 0.05,
        interval: float = 20.0,
        use_converged_only: bool = True,
        water: str | None = None,
    ) -> Self:
        """Calculate potential energy profile for one torsion angle.

        Args:
            calculator (str | Callable): 'MMFF', 'UFF', 'xTB' or ASE calculator.
            indices (tuple[int]): atom indices (i,j,k,l) for a torsion angle
            simplify (bool, optional): whether to use fragementation. Defaults to True.
            fmax (float, optional): convergence limit for optimize. Defaults to 0.05.
            interval (float, optional): angle intervals. Defaults to 20.0.
            use_converged_only (bool, optional): whether to use only converged data. Defaults to True.

        Args for xTB calculator:
            water (str, optional): water solvation model (choose 'gbsa' or 'alpb')
                alpb: ALPB solvation model (Analytical Linearized Poisson-Boltzmann).
                gbsa: generalized Born (GB) model with Surface Area contributions.
                Defaults to None.

        Returns:
            Self: modified self.
        """
        ref_conf = self.copy()

        data = {
            "indices": indices,
            "angle": [],
            "init": [],
            "last": [],
            "Converged": [],
        }

        if simplify:
            (frag, frag_ijkl, frag_created, wbo_filtered) = create_torsion_fragment(
                ref_conf.rdmol, indices
            )
            frag_conf = Conf(frag)
            for angle in np.arange(-180.0, 180.0, interval):
                # Iterated numpy.ndarray does not contain the last 180: -180., ..., (180).
                conf = frag_conf.copy()
                conf.set_torsion_angle(*frag_ijkl, angle)  # atoms bonded to `l` move.
                conf = conf.optimize(calculator, fmax=fmax, water=water)
                data["angle"].append(angle)
                # conf.optimize() updates coordinates and conf.props:
                #   `E_tot_init(kcal/mol)`, `E_tot(kcal/mol)`, `Converged`.
                data["init"].append(conf.props["E_tot_init(kcal/mol)"])
                data["last"].append(conf.props["E_tot(kcal/mol)"])
                data["Converged"].append(conf.props["Converged"])
                frag_cleaned, _ = clean_2d(frag, reset_isotope=True, remove_H=True)
                # to serialize the molecule
                data["frag"] = Chem.MolToMolBlock(frag_cleaned)
                data["frag_indices"] = frag_ijkl
        else:
            for angle in np.arange(-180.0, 180.0, interval):
                # Iterated numpy.ndarray does not contain the last 180: -180., ..., (180).
                conf = ref_conf.copy()
                conf.set_torsion_angle(*indices, angle)  # atoms bonded to `l` move.
                conf = conf.optimize(calculator, fmax=fmax, water=water)
                data["angle"].append(angle)
                # conf.optimize() updates coordinates and conf.props:
                #   `E_tot_init(kcal/mol)`, `E_tot(kcal/mol)`, `Converged`.
                data["init"].append(conf.props["E_tot_init(kcal/mol)"])
                data["last"].append(conf.props["E_tot(kcal/mol)"])
                data["Converged"].append(conf.props["Converged"])

        # Post-processing
        if use_converged_only:
            data["angle"] = list(itertools.compress(data["angle"], data["Converged"]))
            data["init"] = list(itertools.compress(data["init"], data["Converged"]))
            data["last"] = list(itertools.compress(data["last"], data["Converged"]))

        relax = np.array(data["init"]) - np.median(data["last"])
        E_rel = relax - np.min(relax)

        torsion_energy_profile = {
            "indices": data["indices"],
            "angle": np.round(
                np.array(data["angle"]), 1
            ).tolist(),  # np.ndarray -> list for serialization
            "E_rel(kcal/mol)": np.round(
                E_rel, 2
            ).tolist(),  # np.ndarray -> list for serialization
        }

        if simplify:
            torsion_energy_profile.update(
                {
                    "frag": data.get("frag", None),
                    "frag_indices": data.get("frag_indices", None),
                }
            )

        self.props["torsion"] = torsion_energy_profile

        return self

    def __calculate_torsion_energies_batch(
        self,
        batchoptimizer: Callable,
        indices: tuple,
        simplify: bool = True,
        fmax: float = 0.05,
        interval: float = 20.0,
        use_converged_only: bool = True,
        batchsize_atoms: int = 16 * 1024,
    ) -> Self:
        """Calculate potential energy profile for torsion angles in a batch.

        Args:
            batchoptimizer (Callable): BatchOptimizer.
            indices (tuple): atom indices (i,j,k,l) for a torsion angle
            simplify (bool, optional): whether to use fragementation. Defaults to True.
            fmax (float, optional): convergence limit for optimize. Defaults to 0.05.
            interval (float, optional): angle intervals. Defaults to 20.0.
            use_converged_only (bool, optional): whether to use only converged data. Defaults to True.

        Returns:
            Self: modified self.
        """
        ref_conf = self.copy()

        data = {
            "indices": indices,
            "angle": [],
            "init": [],
            "last": [],
            "Converged": [],
        }

        confs = []
        if simplify:
            (frag, frag_ijkl, frag_created, wbo_filtered) = create_torsion_fragment(
                ref_conf.rdmol, indices
            )
            frag_conf = Conf(frag)
            for angle in np.arange(-180.0, 180.0, interval):
                # Iterated numpy.ndarray does not contain the last 180: -180., ..., (180).
                conf = frag_conf.copy()
                conf.set_torsion_angle(*frag_ijkl, angle)  # atoms bonded to `l` move.
                frag_cleaned, _ = clean_2d(frag, reset_isotope=True, remove_H=True)
                # to serialize the molecule
                data["frag"] = Chem.MolToMolBlock(frag_cleaned)
                data["frag_indices"] = frag_ijkl
                data["angle"].append(angle)
                confs.append(conf)

        else:
            for angle in np.arange(-180.0, 180.0, interval):
                # Iterated numpy.ndarray does not contain the last 180: -180., ..., (180).
                conf = ref_conf.copy()
                conf.set_torsion_angle(*indices, angle)  # atoms bonded to `l` move.
                data["angle"].append(angle)
                confs.append(conf)

        batches = prepare_batches(confs, batchsize_atoms)

        for batch in batches:
            optimized = batchoptimizer(batch.rdmols).run()
            for rdmol in optimized.mols:
                # conf.optimize() updates coordinates and conf.props:
                #   `E_tot_init(kcal/mol)`, `E_tot(kcal/mol)`, `Converged`.
                data["init"].append(float(rdmol.GetProp("E_tot_init(kcal/mol)")))
                data["last"].append(float(rdmol.GetProp("E_tot(kcal/mol)")))
                data["Converged"].append(
                    True if rdmol.GetProp("Converged") == "True" else False
                )

        # Post-processing
        if use_converged_only:
            data["angle"] = list(itertools.compress(data["angle"], data["Converged"]))
            data["init"] = list(itertools.compress(data["init"], data["Converged"]))
            data["last"] = list(itertools.compress(data["last"], data["Converged"]))

        relax = np.array(data["init"]) - np.median(data["last"])
        E_rel = relax - np.min(relax)

        torsion_energy_profile = {
            "indices": data["indices"],
            "angle": np.round(
                np.array(data["angle"]), 1
            ).tolist(),  # np.ndarray -> list for serialization
            "E_rel(kcal/mol)": np.round(
                E_rel, 2
            ).tolist(),  # np.ndarray -> list for serialization
        }

        if simplify:
            torsion_energy_profile.update(
                {
                    "frag": data.get("frag", None),
                    "frag_indices": data.get("frag_indices", None),
                }
            )

        self.props["torsion"] = torsion_energy_profile

        return self

    def calculate_torsion_energies(
        self,
        calculator: str | Callable,
        torsion_angle_idx: int | None = None,
        simplify: bool = True,
        fmax: float = 0.05,
        interval: float = 20.0,
        use_converged_only: bool = True,
        batchsize_atoms: int = 0,
        water: str | None = None,
    ) -> Self:
        """Calculates potential energy profiles for each torsion angle using ASE or BatchOptimizer.

        Args:
            calculator (str | Callable): 'MMFF', 'UFF', 'xTB', ASE calculator, or BatchOptimizer.
            torsion_angle_idx (int | None): key to the torsion indices to calculate. Defaults to None (all).
            simplify (bool, optional): whether to use fragment surrogate. Defaults to True.
            fmax (float, optional): fmax of ASE optimizer. Defaults to 0.05.
            interval (float, optional): interval of torsion angles in degree. Defaults to 15.0.
            use_converged_only (bool, optional): whether to use only converged data. Defaults to True.
            batchsize_atoms (int, optional): maximum number of atoms in a single batch.
                Setting any number smaller than conf.natoms to disable batch optimization.
                Defaults to 0.

        Args for xTB calculator:
            water (str, optional): water solvation model (choose 'gbsa' or 'alpb')
                alpb: ALPB solvation model (Analytical Linearized Poisson-Boltzmann).
                gbsa: generalized Born (GB) model with Surface Area contributions.
                Defaults to None.

        Returns:
            Self: modified self.
        """

        torsion_angle_atom_indices_list = self.get_torsion_angle_atoms()
        # [(5, 4, 3, 1), ...]

        if isinstance(torsion_angle_idx, int) and torsion_angle_idx < len(
            torsion_angle_atom_indices_list
        ):
            indices = {
                torsion_angle_idx: torsion_angle_atom_indices_list[torsion_angle_idx]
            }
            # atom indices for a single torsion angle
            # ex. {0: (5,4,3,1)}
        else:
            indices = {k: v for k, v in enumerate(torsion_angle_atom_indices_list)}
            # atom indices for all torsion angles
            # ex. {0: (5,4,3,1), 1: ...}

        conf = self.copy()
        torsion_energies = []
        if batchsize_atoms >= conf.natoms:
            for torsion_angle_idx, ijkl in indices.items():
                conf = conf.__calculate_torsion_energies_batch(
                    calculator,
                    ijkl,
                    simplify,
                    fmax,
                    interval,
                    use_converged_only,
                    batchsize_atoms=batchsize_atoms,
                )
                conf.props["torsion"].update({"torsion_angle_idx": torsion_angle_idx})
                torsion_energies.append(conf.props["torsion"])
        else:
            for torsion_angle_idx, ijkl in indices.items():
                conf = conf.calculate_torsion_energies_one(
                    calculator,
                    ijkl,
                    simplify,
                    fmax,
                    interval,
                    use_converged_only,
                    water=water,
                )
                conf.props["torsion"].update({"torsion_angle_idx": torsion_angle_idx})
                torsion_energies.append(conf.props["torsion"])

        self.props["torsion"] = torsion_energies

        return self

    def __sp_torsion_energies(
        self,
        calculator: str | Callable,
        indices: tuple[int],
        simplify: bool = True,
        interval: float = 20.0,
        water: str | None = None,
    ) -> Self:
        """Single-Point based potential energy profile for one torsion angle.

        Args:
            calculator (str | Callable): 'MMFF', 'UFF', 'xTB' or ASE calculator.
            indices (tuple[int]): atom indices (i,j,k,l) for a torsion angle
            simplify (bool, optional): whether to use fragementation. Defaults to True.
            interval (float, optional): angle intervals. Defaults to 20.0.

        Args for xTB calculator:
            water (str, optional): water solvation model (choose 'gbsa', 'alpb', 'cpcmx')
                alpb: ALPB solvation model (Analytical Linearized Poisson-Boltzmann).
                gbsa: generalized Born (GB) model with Surface Area contributions.
                cpcmx: Extended Conductor-like Polarizable Continuum Solvation Model (CPCM-X).
                Defaults to None.

        Returns:
            Self: modified self.
        """
        ref_conf = self.copy()  # optimized reference conformer
        ref_conf = ref_conf.singlepoint(calculator, water=water)

        data = {
            "indices": indices,
            "angle": [],
            "init": [],
            "last": [],
            "Converged": [],
        }

        if simplify:
            (frag, frag_ijkl, frag_created, wbo_filtered) = create_torsion_fragment(
                ref_conf.rdmol, indices
            )
            frag_conf = Conf(frag)
            for angle in np.arange(-180.0, 180.0, interval):
                # Iterated numpy.ndarray does not contain the last 180: -180., ..., (180).
                conf = frag_conf.copy()
                conf.set_torsion_angle(*frag_ijkl, angle)  # atoms bonded to `l` move.
                conf = conf.singlepoint(calculator, water=water)
                data["angle"].append(angle)
                # conf.singlepoint() sets `E_tot(kcal/mol)`
                # conf.optimize() updates coordinates and conf.props:
                #   `E_tot_init(kcal/mol)`, `E_tot(kcal/mol)`, `Converged`.
                data["init"].append(conf.props["E_tot(kcal/mol)"])
                data["last"].append(ref_conf.props["E_tot(kcal/mol)"])
                frag_cleaned, _ = clean_2d(frag, reset_isotope=True, remove_H=True)
                # to serialize the molecule
                data["frag"] = Chem.MolToMolBlock(frag_cleaned)
                data["frag_indices"] = frag_ijkl
        else:
            for angle in np.arange(-180.0, 180.0, interval):
                # Iterated numpy.ndarray does not contain the last 180: -180., ..., (180).
                conf = ref_conf.copy()
                conf.set_torsion_angle(*indices, angle)  # atoms bonded to `l` move.
                conf = conf.singlepoint(calculator, water=water)
                data["angle"].append(angle)
                # conf.optimize() updates coordinates and conf.props:
                #   `E_tot_init(kcal/mol)`, `E_tot(kcal/mol)`, `Converged`.
                data["init"].append(conf.props["E_tot(kcal/mol)"])
                data["last"].append(ref_conf.props["E_tot(kcal/mol)"])

        relax = np.array(data["init"]) - np.median(data["last"])
        E_rel = relax - np.min(relax)

        torsion_energy_profile = {
            "indices": data["indices"],
            "angle": np.round(
                np.array(data["angle"]), 1
            ).tolist(),  # np.ndarray -> list for serialization
            "E_rel(kcal/mol)": np.round(
                E_rel, 2
            ).tolist(),  # np.ndarray -> list for serialization
        }

        if simplify:
            torsion_energy_profile.update(
                {
                    "frag": data.get("frag", None),
                    "frag_indices": data.get("frag_indices", None),
                }
            )

        self.props["torsion"] = torsion_energy_profile

        return self

    def __sp_torsion_energies_batch(
        self,
        batch_calculator: Callable,
        indices: tuple,
        simplify: bool = True,
        interval: float = 20.0,
        water: str | None = None,
        batchsize_atoms: int = 16 * 1024,
    ) -> Self:
        """Calculate Single-Point potential energy profile for torsion angles in a batch.

        Args:
            calculator (Callable): BatchSinglePoint calculator.
            indices (tuple): atom indices (i,j,k,l) for a torsion angle
            simplify (bool, optional): whether to use fragementation. Defaults to True.
            interval (float, optional): angle intervals. Defaults to 20.0.

        Args for xTB calculator:
            water (str, optional): water solvation model (choose 'gbsa', 'alpb', 'cpcmx')
                alpb: ALPB solvation model (Analytical Linearized Poisson-Boltzmann).
                gbsa: generalized Born (GB) model with Surface Area contributions.
                cpcmx: Extended Conductor-like Polarizable Continuum Solvation Model (CPCM-X).
                Defaults to None.

        Returns:
            Self: modified self.
        """
        ref_conf = self.copy()  # optimized reference conformer
        evaluated_batch = batch_calculator([ref_conf.rdmol]).run()
        for rdmol in evaluated_batch.mols:
            ref_conf.props["E_tot(kcal/mol)"] = float(rdmol.GetProp("E_tot(kcal/mol)"))

        data = {
            "indices": indices,
            "angle": [],
            "init": [],
            "last": [],
            "Converged": [],
        }

        confs = []
        if simplify:
            (frag, frag_ijkl, frag_created, wbo_filtered) = create_torsion_fragment(
                ref_conf.rdmol, indices
            )
            frag_conf = Conf(frag)
            for angle in np.arange(-180.0, 180.0, interval):
                # Iterated numpy.ndarray does not contain the last 180: -180., ..., (180).
                conf = frag_conf.copy()
                conf.set_torsion_angle(*frag_ijkl, angle)  # atoms bonded to `l` move.
                frag_cleaned, _ = clean_2d(frag, reset_isotope=True, remove_H=True)
                # to serialize the molecule
                data["frag"] = Chem.MolToMolBlock(frag_cleaned)
                data["frag_indices"] = frag_ijkl
                data["angle"].append(angle)
                confs.append(conf)

        else:
            for angle in np.arange(-180.0, 180.0, interval):
                # Iterated numpy.ndarray does not contain the last 180: -180., ..., (180).
                conf = ref_conf.copy()
                conf.set_torsion_angle(*indices, angle)  # atoms bonded to `l` move.
                data["angle"].append(angle)
                confs.append(conf)

        batches = prepare_batches(confs, batchsize_atoms)

        for batch in batches:
            evaluated_batch = batch_calculator(batch.rdmols).run()
            for rdmol in evaluated_batch.mols:
                # batch single point calculator sets 'E_tot(kcal/mol)'
                # batch optimizer updates coordinates and conf.props:
                #   `E_tot_init(kcal/mol)`, `E_tot(kcal/mol)`, `Converged`.
                data["init"].append(float(rdmol.GetProp("E_tot(kcal/mol)")))
                data["last"].append(ref_conf.props["E_tot(kcal/mol)"])

        relax = np.array(data["init"]) - np.median(data["last"])
        E_rel = relax - np.min(relax)

        torsion_energy_profile = {
            "indices": data["indices"],
            "angle": np.round(
                np.array(data["angle"]), 1
            ).tolist(),  # np.ndarray -> list for serialization
            "E_rel(kcal/mol)": np.round(
                E_rel, 2
            ).tolist(),  # np.ndarray -> list for serialization
        }

        if simplify:
            torsion_energy_profile.update(
                {
                    "frag": data.get("frag", None),
                    "frag_indices": data.get("frag_indices", None),
                }
            )

        self.props["torsion"] = torsion_energy_profile

        return self

    def calculate_sp_torsion_energies(
        self,
        calculator: str | Callable,
        torsion_angle_idx: int | None = None,
        simplify: bool = True,
        interval: float = 20.0,
        water: str | None = None,
        batchsize_atoms: int = 0,
    ) -> Self:
        """Calculates Single-Point potential energy profiles for each torsion angle using ASE or BatchSinglePoint.

        Args:
            calculator (str | Callable): 'MMFF', 'UFF', 'xTB', ASE calculator, or BatchOptimizer.
            torsion_angle_idx (int | None): key to the torsion indices to calculate. Defaults to None (all).
            simplify (bool, optional): whether to use fragment surrogate. Defaults to True.
            fmax (float, optional): fmax of ASE optimizer. Defaults to 0.05.
            interval (float, optional): interval of torsion angles in degree. Defaults to 15.0.
            use_converged_only (bool, optional): whether to use only converged data. Defaults to True.
            batchsize_atoms (int, optional): maximum number of atoms in a single batch.
                Setting any number smaller than conf.natoms to disable batch optimization.
                Defaults to 0.

        Args for xTB calculator:
            water (str, optional): water solvation model (choose 'gbsa' or 'alpb')
                alpb: ALPB solvation model (Analytical Linearized Poisson-Boltzmann).
                gbsa: generalized Born (GB) model with Surface Area contributions.
                cpcmx: Extended Conductor-like Polarizable Continuum Solvation Model (CPCM-X).
                Defaults to None.

        Returns:
            Self: modified self.
        """

        torsion_angle_atom_indices_list = self.get_torsion_angle_atoms()
        # [(5, 4, 3, 1), ...]

        if isinstance(torsion_angle_idx, int) and torsion_angle_idx < len(
            torsion_angle_atom_indices_list
        ):
            indices = {
                torsion_angle_idx: torsion_angle_atom_indices_list[torsion_angle_idx]
            }
            # atom indices for a single torsion angle
            # ex. {0: (5,4,3,1)}
        else:
            indices = {k: v for k, v in enumerate(torsion_angle_atom_indices_list)}
            # atom indices for all torsion angles
            # ex. {0: (5,4,3,1), 1: ...}

        conf = self.copy()
        torsion_energies = []
        if batchsize_atoms >= conf.natoms:
            for torsion_angle_idx, ijkl in indices.items():
                conf = conf.__sp_torsion_energies_batch(
                    calculator,
                    ijkl,
                    simplify,
                    interval,
                    water=water,
                    batchsize_atoms=batchsize_atoms,
                )
                conf.props["torsion"].update({"torsion_angle_idx": torsion_angle_idx})
                torsion_energies.append(conf.props["torsion"])
        else:
            for torsion_angle_idx, ijkl in indices.items():
                conf = conf.__sp_torsion_energies(
                    calculator, ijkl, simplify, interval, water
                )
                conf.props["torsion"].update({"torsion_angle_idx": torsion_angle_idx})
                torsion_energies.append(conf.props["torsion"])

        self.props["torsion"] = torsion_energies

        return self

    def dumps(self, key: str = "") -> str:
        """Returns JSON dumps of the `props`.

        Args:
            key (str): a key for the `props` dictionary. Defaults to '' (all).

        Returns:
            str: JSON dumps.
        """
        if key:
            return json.dumps({key: self.props[key]})
        else:
            return json.dumps(self.props)

    def serialize(self, decimals: int = 3) -> str:
        """Serialize information necessary to rebuild a Conf object.

        Args:
            decimals (int, optional): number of decimal places for float data type. Defaults to 3.

        Examples:
            ```python
            serialized = conf1.serialize()
            conf2 = Conf().deserialize(serialized)
            assert conf1 == conf2
            ```

        Returns:
            str: serialized string for json.loads()
        """
        serialized = rdworks.utils.serialize(
            {
                "name": self.name,
                "natoms": self.natoms,
                "charge": self.charge,
                "spin": self.spin,
                "props": rdworks.utils.recursive_round(self.props, decimals),
                "molblock": self.molblock,
            }
        )

        return serialized

    def deserialize(self, serialized: str) -> Self:
        """De-serialize information and rebuild a Conf object.

        Examples:
            ```python
            serialized = conf1.serialize()
            conf2 = Conf().deserialize(serialized)
            assert conf1 == conf2
            ```
        Args:
            serialized (str): serialized string.

        Returns:
            Self: modified self.
        """

        data = rdworks.utils.deserialize(serialized)

        self.name = data["name"]
        self.natoms = int(data["natoms"])
        self.charge = int(data["charge"])
        self.spin = int(data["spin"])
        self.props = data["props"]
        self.rdmol = Chem.MolFromMolBlock(
            data["molblock"], sanitize=False, removeHs=False
        )
        self._update()

        return self

    def to_geometry(self) -> str:
        """Returns geometry input for psi4 or other quantum chemistry software.

        Each line has atom symbol and its X, Y, and Z coordinates.
        Unit is Angstrom.

        O  0.0  0.0  0.0
        H  0.757  0.586  0.0
        H -0.757  0.586  0.0

        Example:
            import psi4
            geometry = conf.to_geometry()
            mol = psi4.geometry(geometry)

        Returns:
            str: geometry input for psi4 or other quantum chemistry software.
        """
        lines = [
            f"{e:5} {x:.3f} {y:.3f} {z:.3f}"
            for e, (x, y, z) in zip(self.symbols, self.positions)
        ]
        return "\n".join(lines)

    def to_xyz(self) -> str:
        """Returns XYZ formatted strings.

        Returns:
            str: XYZ formatted strings.
        """
        lines = [f"{self.natoms}", " "]
        for e, (x, y, z) in zip(self.symbols, self.positions):
            lines.append(f"{e:5} {x:23.14f} {y:23.14f} {z:23.14f}")
        return "\n".join(lines)

    def to_turbomole(self, bohr: bool = False) -> str:
        """Returns TURBOMOLE coord file formatted strings.

        Turbomole coord file format:

            - It starts with the keyword `$coord`.
            - Each line after the $coord line specifies an atom, consisting of:
                - Three real numbers representing the Cartesian coordinates (x, y, z).
                - A string for the element name.
                - Optional: an "f" label at the end to indicate that the atom's coordinates are frozen during optimization.
            - Coordinates can be given in Bohr (default), Ångström (`$coord angs`), or fractional coordinates (`$coord frac`).
            - Optional data groups like periodicity (`$periodic`), lattice parameters (`$lattice`), and cell parameters (`$cell`) can also be included.
            - Regarding precision:
                The precision of the coordinates is crucial for accurate calculations, especially geometry optimizations.
                Tools like the TURBOMOLEOptimizer might check for differences in atomic positions with a tolerance of 1e-13.

        Args:
            bohr (bool): whether to use Bohr units of the coordinates. Defaults to False.
                Otherwise, Angstrom units will be used.

        Returns:
            str: TURBOMOLE coord formatted file.
        """
        if bohr:
            lines = ["$coord"]
        else:
            lines = ["$coord angs"]

        for (x, y, z), e in zip(self.positions, self.symbols):
            lines.append(f"{x:20.15f} {y:20.15f} {z:20.15f} {e}")

        lines.append("$end")

        return "\n".join(lines)

    def to_sdf(self, props: bool = True) -> str:
        """Returns the SDF-formatted strings.

        Args:
            props (bool, optional): include `props as SDF properties. Defaults to True.

        Returns:
            str: strings in the SDF format.
        """
        in_memory = io.StringIO()
        with Chem.SDWriter(in_memory) as f:
            rdmol = Chem.Mol(self.rdmol)
            rdmol.SetProp("_Name", self.name)
            if props:
                for k, v in self.props.items():
                    rdmol.SetProp(k, str(v))
            f.write(rdmol)
        return in_memory.getvalue()

    def to_png(
        self,
        width: int = 300,
        height: int = 300,
        legend: str = "",
        atom_index: bool = False,
        highlight_atoms: list[int] | None = None,
        highlight_bonds: list[int] | None = None,
        redraw: bool = False,
        coordgen: bool = False,
        trim: bool = True,
    ) -> Image.Image:
        """Draw 2D molecule in PNG format.

        Args:
            width (int, optional): width. Defaults to 300.
            height (int, optional): height. Defaults to 300.
            legend (str, optional): legend. Defaults to ''.
            atom_index (bool, optional): whether to show atom index. Defaults to False.
            highlight_atoms (list[int] | None, optional): atom(s) to highlight. Defaults to None.
            highlight_bonds (list[int] | None, optional): bond(s) to highlight. Defaults to None.
            redraw (bool, optional): whether to redraw. Defaults to False.
            coordgen (bool, optional): whether to use coordgen. Defaults to False.
            trim (bool, optional): whether to trim white margins. Default to True.

        Returns:
            Image.Image: output PIL Image object.
        """

        return render_png(
            self.rdmol,
            width=width,
            height=height,
            legend=legend,
            atom_index=atom_index,
            highlight_atoms=highlight_atoms,
            highlight_bonds=highlight_bonds,
            redraw=redraw,
            coordgen=coordgen,
            trim=trim,
        )

    def to_svg(
        self,
        width: int = 300,
        height: int = 300,
        legend: str = "",
        atom_index: bool = False,
        highlight_atoms: list[int] | None = None,
        highlight_bonds: list[int] | None = None,
        redraw: bool = False,
        coordgen: bool = False,
        optimize: bool = True,
    ) -> str:
        """Draw 2D molecule in SVG format.

        Examples:
            For Jupyternotebook, wrap the output with SVG:

            >>> from IPython.display import SVG
            >>> SVG(libr[0].to_svg())

        Args:
            width (int, optional): width. Defaults to 300.
            height (int, optional): height. Defaults to 300.
            legend (str, optional): legend. Defaults to ''.
            atom_index (bool, optional): whether to show atom index. Defaults to False.
            highlight_atoms (list[int] | None, optional): atom(s) to highlight. Defaults to None.
            highlight_bonds (list[int] | None, optional): bond(s) to highlight. Defaults to None.
            redraw (bool, optional): whether to redraw. Defaults to False.
            coordgen (bool, optional): whether to use coordgen. Defaults to False.
            optimize (bool, optional): whether to optimize SVG string. Defaults to True.

        Returns:
            str: SVG string
        """
        return render_svg(
            self.rdmol,
            width=width,
            height=height,
            legend=legend,
            atom_index=atom_index,
            highlight_atoms=highlight_atoms,
            highlight_bonds=highlight_bonds,
            redraw=redraw,
            coordgen=coordgen,
            optimize=optimize,
        )


class DummyBatchSinglePointer:
    """Example of batch singlepointer"""

    def __init__(self, rdmols, **kwargs):
        self.rdmols = rdmols

    def __str__(self):
        return "Dummy_BatchSinglePoint"

    def run(self):
        Calculated = namedtuple(
            "Calculated",
            [
                "mols",
            ],
        )
        for rdmol in self.rdmols:
            rdmol.SetProp("E_tot(kcal/mol)", "1.0")
        return Calculated(mols=self.rdmols)


class DummyBatchOptimizer:
    """Example of batch optimizer"""

    def __init__(self, rdmols, **kwargs):
        self.rdmols = rdmols

    def __str__(self):
        return "Dummy_BatchOptimizer"

    def run(self):
        Optimized = namedtuple(
            "Optimized",
            [
                "mols",
            ],
        )
        for rdmol in self.rdmols:
            rdmol.SetProp("E_tot_init(kcal/mol)", "10.0")
            rdmol.SetProp("E_tot(kcal/mol)", "1.0")
            rdmol.SetProp("Converged", "True")
        return Optimized(mols=self.rdmols)


Batch = namedtuple("Batch", ["rdmols", "size", "num_atoms"])


def prepare_batches(confs: list[Conf], batchsize_atoms: int = 16384) -> list[Batch]:
    """Prepare batches of Chem.Mol conformers for batch optimization.

    - Each batch has up to `batchsize_atoms` number of atoms.
    - Each batch (namedtuple) has `rdmols`, `size`, `num_atoms` attributes.
    - Note that this function is not necessary for torsion energies
        the batch-optimization of torsion energies are performed using internally prepared batches
        of a series of conformers with different dihedral angles.

    Args:
        confs (list[Conf]): confs to be prepared for batch processing.
        batchsize_atoms (int): max number of atoms in one batch. Defaults to 16384(=16*1024).

    Returns:
        list[namedtuple]: list of batches.
            [Batch(rdmols=batch_confs, size=len(batch_confs), num_atoms=batch_atoms),...]
    """
    batches = []
    batch_confs = []
    batch_atoms = 0
    for conf in confs:
        if (batch_atoms + conf.natoms) > batchsize_atoms:
            batches.append(
                Batch(rdmols=batch_confs, size=len(batch_confs), num_atoms=batch_atoms)
            )
            # start over a new batch
            batch_confs = [conf.rdmol]
            batch_atoms = conf.natoms
        else:
            batch_confs.append(conf.rdmol)
            batch_atoms += conf.natoms
    if batch_atoms > 0:  # last remaining batch
        batches.append(
            Batch(rdmols=batch_confs, size=len(batch_confs), num_atoms=batch_atoms)
        )

    return batches


def batch_singlepoint(
    confs: list[Conf], batch_calculator: Callable, batchsize_atoms: int = 16384
) -> list[Conf]:
    """Batch singlepoint calculation for a list of Conf objects using a given ASE calculator.

    Args:
        confs (list[Conf]): list of Conf objects to be calculated.
        calculator (Callable): batch calculator.

    Returns:
        list[Conf]: list of Conf objects with updated properties.
    """
    batches = prepare_batches(confs, batchsize_atoms=batchsize_atoms)
    calculated_confs = []
    for batch in batches:
        calculated = batch_calculator(batch.rdmols).run()
        for rdmol in calculated.mols:
            conf = Conf(rdmol)
            conf.props = {
                "E_tot(kcal/mol)": float(rdmol.GetProp("E_tot(kcal/mol)")),
            }
            calculated_confs.append(conf)

    return calculated_confs


def batch_optimize(
    confs: list[Conf], batch_calculator: Callable, batchsize_atoms: int = 16384
) -> list[Conf]:
    """Batch optimize a list of Conf objects using a given batch calculator.

    Args:
        confs (list[Conf]): list of Conf objects to be optimized.
        calculator (Callable): batch optimizer.

    Returns:
        list[Conf]: list of optimized Conf objects.
    """
    batches = prepare_batches(confs, batchsize_atoms=batchsize_atoms)
    optimized_confs = []
    for batch in batches:
        optimized = batch_calculator(batch.rdmols).run()
        for rdmol in optimized.mols:
            conf = Conf(rdmol)
            conf.props = {
                "E_tot_init(kcal/mol)": float(rdmol.GetProp("E_tot_init(kcal/mol)")),
                "E_tot(kcal/mol)": float(rdmol.GetProp("E_tot(kcal/mol)")),
                "Converged": True if rdmol.GetProp("Converged") == "True" else False,
            }
            optimized_confs.append(conf)

    return optimized_confs
