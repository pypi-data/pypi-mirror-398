import math
import itertools
import logging
import importlib.resources
import itertools

import numpy as np
import pandas as pd
import networkx as nx

from scipy import signal

from networkx.readwrite import json_graph

import copy
import json

from collections import deque, defaultdict
from dataclasses import dataclass, asdict
from typing import Self, Iterator
from types import SimpleNamespace

from rdkit import Chem

from rdworks import Mol
from rdworks.tautomerism import ComprehensiveTautomers, RdkTautomers

import rdworks.utils


logger = logging.getLogger(__name__)

ln10 = math.log(10)

# adapted from https://github.com/dptech-corp/Uni-pKa/enumerator
smarts_path = importlib.resources.files("rdworks.data.ionized")
AcidBasePatterns = pd.read_csv(smarts_path / "smarts_pattern.csv")
AcidBasePatternsSimple = pd.read_csv(smarts_path / "simple_smarts_pattern.csv")
UnreasonablePatterns = list(
    map(
        Chem.MolFromSmarts,
        [
            "[#6X5]",
            "[#7X5]",
            "[#8X4]",
            "[*r]=[*r]=[*r]",
            "[#1]-[*+1]~[*-1]",
            "[#1]-[*+1]=,:[*]-,:[*-1]",
            "[#1]-[*+1]-,:[*]=,:[*-1]",
            "[*+2]",
            "[*-2]",
            "[#1]-[#8+1].[#8-1,#7-1,#6-1]",
            "[#1]-[#7+1,#8+1].[#7-1,#6-1]",
            "[#1]-[#8+1].[#8-1,#6-1]",
            "[#1]-[#7+1].[#8-1]-[C](-[C,#1])(-[C,#1])",
            # "[#6;!$([#6]-,:[*]=,:[*]);!$([#6]-,:[#7,#8,#16])]=[C](-[O,N,S]-[#1])",
            # "[#6]-,=[C](-[O,N,S])(-[O,N,S]-[#1])",
            "[OX1]=[C]-[OH2+1]",
            "[NX1,NX2H1,NX3H2]=[C]-[O]-[H]",
            "[#6-1]=[*]-[*]",
            "[cX2-1]",
            "[N+1](=O)-[O]-[H]",
        ],
    )
)


def beta_constant(T: float = 278.15) -> float:
    """Returns the beta constant in Kcal/mol unit at a given temperature (Kelvin).

    The constant \\( \\beta \\) is defined as:

    \\[
    \\beta = \\frac{1}{ k_{B} T }
    \\]


    where \\( k_{B} \\) is the Boltzmann constant and
    T is the absolute temperature of the system in Kelvin.

    \\( k_{B} \\) = 1.987204259e-3 Kcal/(mol K)

    For example, \\( \\beta \\) = 0.5527408646408499 Kcal/(mol K) at 278.15 K

    Args:
        T (float) : temperature in Kelvin unit.
    """
    return 1.987204259e-3 * T


def Boltzmann_weights(
    energies: list[float] | np.ndarray, beta: float = 1.0
) -> np.ndarray:
    """Returns the Boltzmann weights of energies.

    The Boltzmann weight, \\( p_{i} \\) is defined as:

    \\[
    p_{i} = \\frac{exp(- \\beta E_{i}) }{ \\sum_{i} exp(- \\beta E_{i})}
    \\]


    Since the Boltzmann weighted average of any property is taken at a specific temperature,
    changing the temperature means changing the value of \\( \\beta \\).

    Args:
        energies (list[float] | np.ndarray) : energies
        beta (float) : \\( \\beta = \\frac{1}{ k_{B} T } \\) (Kcal/mol)

    Returns:s
        np.ndarray

    """
    if isinstance(energies, list) and isinstance(energies[0], float):
        energies = np.array(energies)
    elif isinstance(energies, np.ndarray):
        pass
    else:
        raise TypeError
    relative_energies = energies - np.min(energies)
    boltzmann_factors = np.exp(-beta * relative_energies)
    # Partition function, Z
    Z = np.sum(boltzmann_factors)

    return boltzmann_factors / Z


def Boltzmann_weighted_average(
    energies: list[float] | np.ndarray, beta: float = 1.0
) -> float:
    """Returns the Boltzmann weighted average of energies.
        \\[
            E_{avg} = \\frac{\\sum_{i} E_{i} exp(-\\beta E_{i})}{\\sum_{i} exp(-\\beta E_{i})}
        \\]

    Args:
        energies (list[float] | np.ndarray) : energies
        beta (float) : \\( \\beta = \\frac{1}{k_{B}T} \\) (Kcal/mol)

    Returns:
        float
    """
    if isinstance(energies, list) and isinstance(energies[0], float):
        energies = np.array(energies)
    elif isinstance(energies, np.ndarray):
        pass
    else:
        raise TypeError
    relative_energies = energies - np.min(energies)
    boltzmann_factors = np.exp(-beta * relative_energies)
    Z = np.sum(boltzmann_factors)
    weights = boltzmann_factors / Z

    return float(np.dot(weights, energies))


class InflectionDetector:
    """Inflection point detection with plateau analysis.
    Distinguishes real inflections from noise by analyzing curve behavior.
    """

    def __init__(self, x, y):
        """
        Parameters:
        -----------
        x : array-like
            Independent variable (e.g., pH values)
        y : array-like
            Dependent variable (e.g., protonation)
        """
        self.x = np.array(x)
        self.y = np.array(y)

        # Sort by x to ensure monotonic increase
        sort_idx = np.argsort(self.x)
        self.x = self.x[sort_idx]
        self.y = self.y[sort_idx]

        self._calculate_derivatives()
        # create self.y_smooth, .dy_dx, .d2y_dx2

        self.plateaus = self.detect_plateaus()
        self.num_plateaus = len(self.plateaus)
        self.num_transitions = 0

        if len(self.plateaus) == 0:
            self.curve_info = "continuous_no_plateaus"
            # Estimate transitions from the second derivative
            zero_crossings = np.where(np.diff(np.sign(self.d2y_dx2)))[0]
            self.num_transitions = len(zero_crossings)

        elif len(self.plateaus) == 1:
            self.curve_info = "single_plateau"
            self.num_transitions = 1

        elif len(self.plateaus) == 2:
            self.curve_info = "two_plateaus_single_transition"
            self.num_transitions = 1

        elif len(self.plateaus) >= 3:
            self.curve_info = "multiple_plateaus"
            self.num_transitions = len(self.plateaus) - 1

    def _calculate_derivatives(self) -> None:
        """Calculate smoothed derivatives for analysis"""
        # Use Savitzky-Golay for smooth derivatives
        window = min(11, len(self.x) if len(self.x) % 2 == 1 else len(self.x) - 1)
        window = max(5, window)
        polyorder = min(3, window - 1)
        self.y_smooth = signal.savgol_filter(self.y, window, polyorder)
        self.dy_dx = signal.savgol_filter(
            self.y, window, polyorder, deriv=1, delta=np.mean(np.diff(self.x))
        )
        self.d2y_dx2 = signal.savgol_filter(
            self.y, window, polyorder, deriv=2, delta=np.mean(np.diff(self.x))
        )

    def detect_plateaus(
        self, derivative_threshold=None, min_plateau_length=5
    ) -> list[dict]:
        """
        Detect plateau regions in the curve.

        Parameters:
        -----------
        derivative_threshold : float or None
            Max abs(dy/dx) to consider as plateau. If None, auto-calculated
        min_plateau_length : int
            Minimum number of consecutive points to consider a plateau

        Returns:
        --------
        plateaus : list of dicts with 'start_idx', 'end_idx', 'mean_y', 'std_y'
        """
        if derivative_threshold is None:
            # Auto-calculate: plateau where derivative < 10% of max change rate
            derivative_threshold = 0.1 * np.max(np.abs(self.dy_dx))

        # Find regions where the derivative is close to zero
        is_plateau = np.abs(self.dy_dx) < derivative_threshold

        # Find consecutive plateau regions
        plateaus = []
        in_plateau = False
        start_idx = 0

        for i, plateau_point in enumerate(is_plateau):
            if plateau_point and not in_plateau:
                # Start of plateau
                start_idx = i
                in_plateau = True
            elif not plateau_point and in_plateau:
                # End of plateau
                if i - start_idx >= min_plateau_length:
                    plateau_y = self.y_smooth[start_idx:i]
                    plateaus.append(
                        {
                            "start_idx": start_idx,
                            "end_idx": i - 1,
                            "start_x": self.x[start_idx],
                            "end_x": self.x[i - 1],
                            "mean_y": np.mean(plateau_y),
                            "std_y": np.std(plateau_y),
                            "length": i - start_idx,
                        }
                    )
                in_plateau = False

        # Check if we ended in a plateau
        if in_plateau and len(self.x) - start_idx >= min_plateau_length:
            plateau_y = self.y_smooth[start_idx:]
            plateaus.append(
                {
                    "start_idx": start_idx,
                    "end_idx": len(self.x) - 1,
                    "start_x": self.x[start_idx],
                    "end_x": self.x[-1],
                    "mean_y": np.mean(plateau_y),
                    "std_y": np.std(plateau_y),
                    "length": len(self.x) - start_idx,
                }
            )

        return plateaus

    def _find_inflections_no_plateaus(self) -> list[dict]:
        """Find inflections when no clear plateaus exist"""
        inflections = []

        # Find zero crossings in the second derivative
        zero_crossings = np.where(np.diff(np.sign(self.d2y_dx2)))[0]

        for idx in zero_crossings:
            if idx < len(self.x) - 1:
                # Interpolate exact position
                x1, x2 = self.x[idx], self.x[idx + 1]
                y1, y2 = self.d2y_dx2[idx], self.d2y_dx2[idx + 1]

                if y1 != y2:
                    x_cross = x1 - y1 * (x2 - x1) / (y2 - y1)
                    y_cross = np.interp(x_cross, self.x, self.y_smooth)
                    dy_cross = np.interp(x_cross, self.x, self.dy_dx)

                    inflections.append(
                        {
                            "x": x_cross,
                            "y": y_cross,
                            "dy_dx": dy_cross,
                            "type": "no_plateau",
                            "confidence": "medium",
                        }
                    )

        return inflections

    def _find_inflections_between_plateaus(self) -> list[dict]:
        """Find inflections in transition regions between plateaus"""
        inflections = []
        plateaus = self.plateaus
        for i in range(len(plateaus) - 1):
            plateau1 = plateaus[i]
            plateau2 = plateaus[i + 1]

            # Transition region between plateaus
            trans_start_idx = plateau1["end_idx"]
            trans_end_idx = plateau2["start_idx"]

            if trans_end_idx <= trans_start_idx + 1:
                continue

            # Find inflection in transition region
            trans_slice = slice(trans_start_idx, trans_end_idx + 1)
            x_trans = self.x[trans_slice]
            d2y_trans = self.d2y_dx2[trans_slice]

            # Find zero crossing of second derivative
            zero_crossings = np.where(np.diff(np.sign(d2y_trans)))[0]

            if len(zero_crossings) > 0:
                # Take the middle crossing if multiple
                idx_local = zero_crossings[len(zero_crossings) // 2]
                idx_global = trans_start_idx + idx_local

                # Interpolate exact position
                if idx_global < len(self.x) - 1:
                    x1, x2 = self.x[idx_global], self.x[idx_global + 1]
                    y1, y2 = self.d2y_dx2[idx_global], self.d2y_dx2[idx_global + 1]

                    if y1 != y2:
                        x_cross = x1 - y1 * (x2 - x1) / (y2 - y1)
                        y_cross = np.interp(x_cross, self.x, self.y_smooth)
                        dy_cross = np.interp(x_cross, self.x, self.dy_dx)

                        # Calculate confidence based on plateau separation
                        plateau_separation = abs(
                            plateau2["mean_y"] - plateau1["mean_y"]
                        )
                        noise_level = max(plateau1["std_y"], plateau2["std_y"])

                        if noise_level > 0:
                            signal_to_noise = plateau_separation / noise_level
                            confidence = "high" if signal_to_noise > 5 else "medium"
                        else:
                            confidence = "high"

                        inflections.append(
                            {
                                "x": x_cross,
                                "y": y_cross,
                                "dy_dx": dy_cross,
                                "type": "between_plateaus",
                                "plateau_before": plateau1,
                                "plateau_after": plateau2,
                                "plateau_separation": plateau_separation,
                                "confidence": confidence,
                            }
                        )
            else:
                # No clear inflection - use midpoint of steepest change
                dy_trans = self.dy_dx[trans_slice]
                max_deriv_idx = np.argmax(np.abs(dy_trans))
                idx_global = trans_start_idx + max_deriv_idx

                inflections.append(
                    {
                        "x": self.x[idx_global],
                        "y": self.y_smooth[idx_global],
                        "dy_dx": self.dy_dx[idx_global],
                        "type": "steepest_point",
                        "plateau_before": plateau1,
                        "plateau_after": plateau2,
                        "confidence": "low",
                    }
                )

        return inflections

    def _find_inflections_with_single_plateau(self):
        """Handle case with only one plateau"""
        inflections = []
        plateau = self.plateaus[0]

        # Check before plateau
        if plateau["start_idx"] > 5:
            region = slice(0, plateau["start_idx"])
            x_region = self.x[region]
            d2y_region = self.d2y_dx2[region]

            zero_crossings = np.where(np.diff(np.sign(d2y_region)))[0]
            if len(zero_crossings) > 0:
                idx = zero_crossings[-1]  # Take last one before plateau
                inflections.append(
                    {
                        "x": x_region[idx],
                        "y": self.y_smooth[idx],
                        "dy_dx": self.dy_dx[idx],
                        "type": "before_plateau",
                        "confidence": "medium",
                    }
                )

        # Check after plateau
        if plateau["end_idx"] < len(self.x) - 5:
            region = slice(plateau["end_idx"], len(self.x))
            x_region = self.x[region]
            d2y_region = self.d2y_dx2[region]

            zero_crossings = np.where(np.diff(np.sign(d2y_region)))[0]
            if len(zero_crossings) > 0:
                idx = zero_crossings[0]  # Take first one after plateau
                idx_global = plateau["end_idx"] + idx
                inflections.append(
                    {
                        "x": x_region[idx],
                        "y": self.y_smooth[idx_global],
                        "dy_dx": self.dy_dx[idx_global],
                        "type": "after_plateau",
                        "confidence": "medium",
                    }
                )

        return inflections

    def analyze(self, require_plateaus=True, high_confidence=True) -> list:
        """
        Complete analysis with plateau consideration.

        Args:
            require_plateaus (bool): Only report inflections between clear plateaus

        Returns:
            dict: analysis results
        """
        inflections = []
        if self.curve_info == "continuous_no_plateaus":
            if not require_plateaus:
                # Use standard second derivative method
                inflections = self._find_inflections_no_plateaus()

        elif self.num_plateaus >= 2:
            # Find transitions between plateaus
            inflections = self._find_inflections_between_plateaus()

        elif self.num_plateaus == 1:
            # Single plateau - check for transitions before/after
            if not require_plateaus:
                inflections = self._find_inflections_with_single_plateau()

        if high_confidence:
            inflections = [_ for _ in inflections if _["confidence"] == "high"]

        return inflections


@dataclass
class IonizableSite:
    """(de)protonation site information"""

    atom_idx: int
    atom: str
    hs: int  # number of H attached to the atom
    q: int  # formal charge of the atom
    pr: bool  # can be protonated?
    de: bool  # can be deprotonated?
    name: str  # site name
    acid_base: str


class State:
    def __init__(
        self,
        smiles: str | None = None,
        origin: str | None = None,
        transformation: str | None = None,
        min_formal_charge: int = -2,
        max_formal_charge: int = +2,
        min_atomic_charge: int = -1,
        max_atomic_charge: int = +1,
        protomer_rule: str = "default",
        tautomer_rule: str | None = None,
    ) -> None:
        """Molecular state.

        Args:
            smiles (str): SMILES
            origin (str | None, optional): original SMILES before tautomerization or ionization. Defaults to None.
            transformation (str | None, optional): Tautomer, +H, -H, or None. Defaults to None.
            min_formal_charge (int, optional): min formal charge. Defaults to -2.
            max_formal_charge (int, optional): max formal charge. Defaults to +2.
            min_atomic_charge (int, optional): min atomic charge. Defaults to -1.
            max_atomic_charge (int, optional): max atomic charge. Defaults to +1.
            protomer_rule (str, optional):
                Ioniziation patterns ('default' or 'simple').
                Defaults to 'default'.
            tautomer_rule (str, optional):
                Tautomerization patterns ('rdkit' or 'comprehensive').
                Defaults to None.
        """
        self.smiles: str | None = smiles
        self.origin: str | None = origin  # parent or origin
        self.transformation: str | None = (
            transformation  # how this state is generated from origin
        )
        self.min_formal_charge: int = min_formal_charge
        self.max_formal_charge: int = max_formal_charge
        self.min_atomic_charge: int = min_atomic_charge
        self.max_atomic_charge: int = max_atomic_charge
        self.protomer_rule: str = protomer_rule
        self.tautomer_rule: str | None = tautomer_rule

        self.rdmol: Chem.Mol = None
        self.rdmolH: Chem.Mol = None
        self.sites: list = []
        self.charge: int | None = None
        self.energy: float | None = None  # Gibbs free energy (dG)
        self.ref_ph: float | None = None  # reference pH for dG; dG is pH-dependent
        self.update()

    def __str__(self) -> str:
        """String representation.

        Returns:
            str: short description of the state.
        """
        return f"State(smiles={self.smiles}, sites={self.sites}, transformation={self.transformation}, origin={self.origin})"

    def __eq__(self, other: object) -> bool:
        """Operator `==`."""
        if isinstance(other, State):
            return self.smiles == other.smiles

        return False

    def copy(self) -> Self:
        return copy.deepcopy(self)

    def update(self) -> None:
        if isinstance(self.smiles, str) and len(self.smiles) > 0:
            self.rdmol = Chem.MolFromSmiles(self.smiles)
            self.rdmolH = Chem.AddHs(self.rdmol)
            self.find_ionizable_sites()
            self.charge = Chem.GetFormalCharge(self.rdmol)

    def info(self, index: int | None = None) -> None:
        if isinstance(index, int):
            serial = f"[{index:2}] "
        else:
            serial = ""
        print(f"{serial}SMILES: {self.smiles}")
        print(f"{serial}Origin: {self.origin}")
        print(f"{serial}Charge: {self.charge}")
        print(f"{serial}Energy: {self.energy}")
        print(f"{serial}Reference pH: {self.ref_ph}")
        print(f"{serial}Transformation: {self.transformation}")
        print(f"{serial}Ionizable sites:")

        for site in self.sites:
            print(f"{serial}    atom_idx= {site.atom_idx:2},", end=" ")
            print(f"atom= {site.atom:>2},", end=" ")
            print(f"q= {site.q:+2}, hs= {site.hs:1},", end=" ")
            print(f"pr= {site.pr:1}, de= {site.de:1},", end=" ")
            print(f"acid_base= {site.acid_base}, name= {site.name}")
        print()

    def hydrogen_count(self, idx: int) -> int:
        atom = self.rdmolH.GetAtomWithIdx(idx)
        hydrogen_count = 0
        if atom.GetAtomicNum() == 1:
            for bond in atom.GetNeighbors()[0].GetBonds():
                neighbor = bond.GetOtherAtom(atom)
                if neighbor.GetAtomicNum() == 1:
                    hydrogen_count += 1
        else:
            for bond in atom.GetBonds():
                neighbor = bond.GetOtherAtom(atom)
                if neighbor.GetAtomicNum() == 1:
                    hydrogen_count += 1
        return hydrogen_count

    def site_info(self) -> list[tuple]:
        return [
            (site.atom, site.atom_idx, site.q, site.pr, site.de) for site in self.sites
        ]

    def can_be_protonated_at(self, atom_idx: int) -> bool:
        """Check if an atom can potentially be protonated"""
        atom = self.rdmol.GetAtomWithIdx(atom_idx)
        # Check formal charge (negative charge can be protonated)
        if atom.GetFormalCharge() < 0:
            return True

        # Check for atoms with lone pairs (N, O, S, P, etc.)
        # that aren't already fully protonated
        atomic_num = atom.GetAtomicNum()
        total_valence = atom.GetTotalValence()

        # Common protonatable atoms
        if atomic_num == 7:  # N, O, S
            if total_valence < 4:  # Can form NH4+
                return True
        elif atomic_num in [8, 16]:  # O, S
            if total_valence < 3:  # Can form OH3+ or SH3+
                return True

        return False

    def can_be_deprotonated_at(self, atom_idx: int) -> bool:
        """Check if an atom can potentially be deprotonated"""
        atom = self.rdmol.GetAtomWithIdx(atom_idx)
        # Check if atom has a positive formal charge (can lose H+)
        if atom.GetFormalCharge() > 0:
            return True

        # Check if atom has hydrogens that can be removed
        if atom.GetTotalNumHs() == 0:
            return False

        # Common deprotonatable atoms with acidic hydrogens
        if atom.GetAtomicNum() in [7, 8, 15, 16]:  # N, O, P, S
            return True

        return False

    def find_ionizable_sites(self) -> None:
        if self.protomer_rule == "simple":
            template = AcidBasePatternsSimple
        elif self.protomer_rule == "default":
            template = AcidBasePatterns
        else:
            template = AcidBasePatterns
        for idx, name, smarts, index, acid_base in template.itertuples():
            pattern = Chem.MolFromSmarts(smarts)
            match = self.rdmolH.GetSubstructMatches(pattern)
            if len(match) == 0:
                continue
            else:
                index = int(index)
                for m in match:
                    atom_idx = m[index]
                    at = self.rdmol.GetAtomWithIdx(atom_idx)
                    atom = at.GetSymbol()
                    hs = self.hydrogen_count(atom_idx)
                    q = at.GetFormalCharge()
                    pr = self.can_be_protonated_at(atom_idx)
                    de = self.can_be_deprotonated_at(atom_idx)
                    site = IonizableSite(
                        atom_idx=atom_idx,
                        atom=atom,
                        hs=hs,
                        q=q,
                        name=name,
                        acid_base=acid_base,
                        pr=pr,
                        de=de,
                    )
                    exist = False
                    for _ in self.sites:
                        if _.atom_idx == site.atom_idx:
                            exist = True
                            _.acid_base += f":{site.acid_base}"
                            _.name += f":{site.name}"
                    if not exist:
                        self.sites.append(site)
        self.sites = sorted(self.sites, key=lambda x: x.atom_idx)

    def ionize(self, idx: int, mode: str) -> None:
        rwmol = Chem.RWMol(self.rdmol)
        atom = rwmol.GetAtomWithIdx(idx)
        ionized: Chem.Mol | None = None
        if mode == "a2b":
            if atom.GetAtomicNum() == 1:
                atom_X = atom.GetNeighbors()[0]  # only one
                charge = atom_X.GetFormalCharge() - 1
                atom_X.SetFormalCharge(charge)  # <-- change formal charge
                rwmol.RemoveAtom(idx)  # remove the H atom
                rwmol.RemoveBond(idx, atom_X.GetIdx())  # remove the bond
                ionized = rwmol.GetMol()
            else:
                charge = atom.GetFormalCharge() - 1
                numH = atom.GetTotalNumHs() - 1
                atom.SetFormalCharge(charge)  # <-- change formal charge
                atom.SetNumExplicitHs(numH)  # <-- remove one H
                atom.UpdatePropertyCache()  # <-- update the property cache
                ionized = Chem.AddHs(rwmol)

        elif mode == "b2a":
            charge = atom.GetFormalCharge() + 1
            atom.SetFormalCharge(charge)  # <-- change formal charge
            numH = atom.GetNumExplicitHs() + 1
            atom.SetNumExplicitHs(numH)  # <-- add one H
            ionized = Chem.AddHs(rwmol)
            # Add hydrogens, specifying onlyOnAtoms to target the desired atom
            # explicitOnly=True ensures only explicit Hs are added, not implicit ones
            # ionized = Chem.AddHs(mw, explicitOnly=True, onlyOnAtoms=[idx])

        Chem.SanitizeMol(ionized)

        rdmol = Chem.MolFromSmiles(Chem.MolToSmiles(ionized, canonical=False))
        rdmolH = Chem.AddHs(rdmol)
        smiles = Chem.CanonSmiles(Chem.MolToSmiles(Chem.RemoveHs(rdmolH)))

        self.smiles = smiles
        self.sites = []
        self.update()

    def get_protonated(
        self, atom_idx: int | None = None, site_idx: int | None = None
    ) -> list[Self]:
        """Make protonated state(s) from the current state.

        All ionizable sites are considered for protonation unless `atom_idx` or `site_idx` is given.

        Args:
            atom_idx (int | None, optional): atom index. Defaults to None.
            site_idx (int | None, optional): site index. Defaults to None.

        Returns:
            list[Self]: list of protonated States.
        """
        states = []

        if self.charge == self.max_formal_charge:
            return states

        if isinstance(atom_idx, int):
            for site in self.sites:
                if site.pr and (site.atom_idx == atom_idx):
                    new_state = self.copy()
                    new_state.ionize(site.atom_idx, "b2a")
                    new_state.transformation = "+H"
                    new_state.origin = self.smiles
                    states.append(new_state)
        elif isinstance(site_idx, int):
            site = self.sites[site_idx]
            if not site.pr:
                return states
            new_state = self.copy()
            new_state.ionize(site.atom_idx, "b2a")
            new_state.transformation = "+H"
            new_state.origin = self.smiles
            states.append(new_state)
        else:
            for site in self.sites:
                if not site.pr:
                    continue
                new_state = self.copy()
                new_state.ionize(site.atom_idx, "b2a")
                new_state.transformation = "+H"
                new_state.origin = self.smiles
                states.append(new_state)

        return states

    def get_deprotonated(
        self, atom_idx: int | None = None, site_idx: int | None = None
    ) -> list[Self]:
        """Make deprotonated state(s) from the current state.

        Args:
            atom_idx (int | None, optional): atom index. Defaults to None.
            site_idx (int | None, optional): site index. Defaults to None.

        Returns:
            list[Self]: list of deprotonated States.
        """
        states = []

        if self.charge == self.min_formal_charge:
            return states

        if isinstance(atom_idx, int):
            for site in self.sites:
                if site.de and (site.atom_idx == atom_idx):
                    new_state = self.copy()
                    new_state.ionize(atom_idx, "a2b")
                    new_state.transformation = "-H"
                    new_state.origin = self.smiles
                    states.append(new_state)
        elif isinstance(site_idx, int):
            site = self.sites[site_idx]
            if not site.de:
                return states
            new_state = self.copy()
            new_state.ionize(site.atom_idx, "a2b")
            new_state.transformation = "-H"
            new_state.origin = self.smiles
            states.append(new_state)
        else:
            for site in self.sites:
                if not site.de:
                    continue
                new_state = self.copy()
                new_state.ionize(site.atom_idx, "a2b")
                new_state.transformation = "-H"
                new_state.origin = self.smiles
                states.append(new_state)
        return states

    def get_tautomers(self) -> list[Self]:
        if self.tautomer_rule is None:
            return []
        elif self.tautomer_rule == "rdkit":
            t = RdkTautomers(self.smiles).enumerate()
        elif self.tautomer_rule == "comprehensive":
            t = ComprehensiveTautomers(self.smiles).enumerate()
        else:
            return []

        states = []
        for smiles in t.enumerated:
            try:
                assert smiles != self.smiles
                rdmol = Chem.MolFromSmiles(smiles)
                assert rdmol is not None
                charge = Chem.GetFormalCharge(rdmol)
                assert charge == self.charge
                states.append(
                    State(smiles=smiles, origin=self.smiles, transformation="Tautomer")
                )
            except:
                continue

        return states

    def serialize(self) -> str:
        """Serialize the state to a string."""
        data = {
            "smiles": self.smiles,
            "origin": self.origin,
            "transformation": self.transformation,
            "min_formal_charge": self.min_formal_charge,
            "max_formal_charge": self.max_formal_charge,
            "min_atomic_charge": self.min_atomic_charge,
            "max_atomic_charge": self.max_atomic_charge,
            "protomer_rule": self.protomer_rule,
            "tautomer_rule": self.tautomer_rule,
            "charge": self.charge,
            "energy": self.energy,
            "ref_ph": self.ref_ph,
            "sites": [asdict(site) for site in self.sites],
        }
        encoded_str = rdworks.utils.serialize(data)

        return encoded_str

    def deserialize(self, encoded_str: str) -> Self:
        """Deserialize the state from a string."""
        obj = rdworks.utils.deserialize(encoded_str)
        self.smiles = obj["smiles"]
        self.origin = obj["origin"]
        self.transformation = obj["transformation"]
        self.min_formal_charge = obj["min_formal_charge"]
        self.max_formal_charge = obj["max_formal_charge"]
        self.min_atomic_charge = obj["min_atomic_charge"]
        self.max_atomic_charge = obj["max_atomic_charge"]
        self.protomer_rule = obj["protomer_rule"]
        self.tautomer_rule = obj["tautomer_rule"]
        self.charge = obj["charge"]
        self.energy = obj["energy"]
        self.ref_ph = obj["ref_ph"]
        self.sites = [IonizableSite(**site) for site in obj["sites"]]
        self.update()

        return self


class StateEnsemble:
    def __init__(
        self, states: list[State] | None = None, transformation: str | None = None
    ) -> None:
        self.states = []

        if isinstance(states, list) and all(isinstance(_, State) for _ in states):
            self.states = states

        if transformation:
            for state in self.states:
                state.transformation = transformation

    def __str__(self) -> str:
        """String representation.

        Returns:
            str: short description of the state.
        """
        return f"StateEnsemble(n={self.size()}, states={[st.smiles for st in self.states]})"

    def __eq__(self, other: object) -> bool:
        """Operator `==`."""
        if isinstance(other, StateEnsemble):
            return set([st.smiles for st in self.states]) == set(
                [st.smiles for st in other.states]
            )

        return False

    def __iter__(self) -> Iterator:
        """Operator `for ... in ...` or list()"""
        return iter(self.states)

    def __getitem__(self, index: int | slice) -> list[State] | State:
        """Operator `[]`"""
        return self.states[index]

    def __setitem__(self, index: int, state: State) -> Self:
        """Set item."""
        self.states[index] = state
        return self

    def __add__(self, other: State | Self) -> Self:
        """Operator `+`."""
        assert isinstance(other, State | StateEnsemble), (
            "'+' operator expects State or StateEnsemble object"
        )
        new_object = self.copy()
        if isinstance(other, State):
            new_object.states.append(other)
        elif isinstance(other, StateEnsemble):
            new_object.states.extend(other.states)
        return new_object

    def __iadd__(self, other: State | Self) -> Self:
        """Operator `+=`."""
        assert isinstance(other, State | StateEnsemble), (
            "'+=' operator expects State or StateEnsemble object"
        )
        if isinstance(other, State):
            self.states.append(other)
        elif isinstance(other, StateEnsemble):
            self.states.extend(other.states)
        return self

    def copy(self) -> Self:
        """Copy."""
        return copy.deepcopy(self)

    def drop(self) -> Self:
        """Drop duplicate and unreasonable states."""
        U = []
        mask = []
        for state in self.states:
            if state.rdmol is None:
                mask.append(False)
                continue
            if state.smiles in U:
                mask.append(False)
                continue
            reasonable = True
            for pattern in UnreasonablePatterns:
                if len(state.rdmol.GetSubstructMatches(pattern)) > 0:
                    reasonable = False
                    break
            if not reasonable:
                mask.append(False)
                continue
            mask.append(True)
            U.append(state.smiles)
        self.states = list(itertools.compress(self.states, mask))

        return self

    def trim(self, p: np.ndarray, threshold: float = 0.0) -> Self:
        """Trim states whose pH-dependent population is below a given threshold across pH range 0-14.

        Args:
            p (np.ndarray): array of populations.
            threshold (float, optional): min population. Defaults to 0.0.

        Returns:
            Self: StateEnsemble
        """
        retain_mask = [False if max(ph_p) < threshold else True for ph_p in p]
        self.states = list(itertools.compress(self.states, retain_mask))

        return self

    def sort(self, p: np.ndarray) -> Self:
        """Sort states by population.

        Args:
            p (np.ndarray): array of population.

        Returns:
            Self: StateEnsemble
        """
        _ = sorted(
            [(max(ph_p), state_idx) for state_idx, ph_p in enumerate(p)], reverse=True
        )
        self.states = [self.states[i] for (_max_population, i) in _]

        return self

    def set_energies(self, dG: list[float] | np.ndarray, ref_ph: float = 7.0) -> Self:
        """Set energies to states.

        Args:
            dG (list[float] | np.ndarray): list or array of energies.
            ref_ph (float): pH at which the energies are calculated. Defaults to 7.0

        Returns:
            Self: StateEnsemble
        """
        assert len(dG) == self.size(), (
            "The number of energies does not match the number of states"
        )
        for i, energy in enumerate(dG):
            self.states[i].energy = float(energy)
            self.states[i].ref_ph = ref_ph

        return self

    def get_state(self, index: int) -> State:
        """Get a state by index

        Args:
            index (int): state index.

        Returns:
            State: State
        """

        assert -self.size() <= index < self.size(), "State does not exist"
        return self.states[index]

    def size(self) -> int:
        """Number of states."""
        return len(self.states)

    def info(self) -> None:
        """Print information of all states."""
        for i, state in enumerate(self.states):
            state.info(index=i)

    def get_charge_groups(self) -> dict[int, list[int]]:
        """Get charge groups

        Returns:
            dict: {charge: [state_idx, ...], ...}
        """
        charge_groups = defaultdict(list)
        for st_idx, st in enumerate(self.states):
            charge_groups[st.charge].append(st_idx)
        return dict(sorted(charge_groups.items(), reverse=True))

    def get_charge_groups_per_site(self) -> dict[int, dict[int, list[int]]]:
        """Get charge groups per atom site

        Returns:
            dict: {atom_idx: {atom_charge: [state_idx, ...], ...}}
        """
        charge_groups_per_site = {}
        # collect all ionizable sites (atom index)
        sites_collective = set()
        for st in self.states:
            for atom_symbol, atom_idx, atom_charge, pr, de in st.site_info():
                # ex. [('N', 5, 0, True, True), ...]
                sites_collective.add(atom_idx)

        for st_idx, st in enumerate(self.states):
            for atom_idx in sites_collective:
                atom = st.rdmol.GetAtomWithIdx(atom_idx)
                atom_charge = atom.GetFormalCharge()
                if atom_idx in charge_groups_per_site:
                    if atom_charge in charge_groups_per_site[atom_idx]:
                        charge_groups_per_site[atom_idx][atom_charge].append(st_idx)
                    else:
                        charge_groups_per_site[atom_idx][atom_charge] = [st_idx]
                else:
                    charge_groups_per_site[atom_idx] = {atom_charge: [st_idx]}

        return dict(sorted(charge_groups_per_site.items()))

    def get_population(
        self, ph_values: np.ndarray, C: float = ln10, beta: float = 1.0
    ) -> np.ndarray:
        """Get populations at a given pH array.

        \\[
        \\begin{align}
        \\Delta G_{i, ref} &= PE_{i} - PE_{ref} \\\\[0.5em]
        \\Delta m_{i, ref} &= charge_{i} - charge _{ref} \\\\[0.5em]
        \\Delta G_{i, pH} &= \\Delta G_{i, ref} + \\Delta m_{i, ref} C pH \\\\[0.5em]
        p_{i, pH} &= \\frac {exp(-\\beta \\Delta G_{i, pH})}{\\sum_{i} exp(-\\beta \\Delta G_{i, pH})}
        \\end{align}
        \\]

        Args:
            ph_values (np.ndarray): array of pH values.
            C (float, optional): constant for pH-dependent dG calculation. Defaults to ln(10).
            beta (float, optional): \\( \\beta = \\frac{1}{k_{B} T} \\). Defaults to 1.0.

        Returns:
            np.ndarray:
                array of populations with shape of (number of states, number of pH).
        """
        # The reference state can be arbitrary and is set to the initial_state here.
        ref = self.states[0]

        assert ref.energy is not None, "reference state should have defined energy"
        assert ref.charge is not None, "reference state should have defined charge"

        ph_values = np.array(ph_values)

        dG_pH = []
        for st in self.states:
            assert st.energy is not None, "state should have defined energy"
            assert st.charge is not None, "state should have defined charge"
            assert st.ref_ph is not None, "state should have defined reference pH"
            # free energy difference
            delta_G = st.energy - ref.energy
            # charge difference
            delta_m = st.charge - ref.charge
            # pH-dependent free energy
            pH_dependent_dG = delta_G + delta_m * C * (ph_values - st.ref_ph)
            dG_pH.append(pH_dependent_dG)

        dG_pH = np.array(dG_pH)

        Boltzmann_factors = np.exp(-beta * dG_pH)

        # partition function, Z
        Z = np.sum(Boltzmann_factors, axis=0)

        p = Boltzmann_factors / Z

        assert p.shape == (
            self.size(),
            ph_values.shape[0],
        ), "population array has wrong shape"

        return p

    def get_micro_pKa(
        self, ph_values: np.ndarray, p: np.ndarray
    ) -> dict[int, list[tuple[float, float]]]:
        """
        Compute inflection points in pH vs site_charge that could be microscopic pKa values
        For example, ideal pKa transitions should happen at +1.5, +0.5, -0.5 in case of +2 to -1 charges.

        Args:
            ph_values (np.ndarray): Array of pH values to evaluate populations
            p (nd.ndarray): Population matrix for each state at each pH

        Returns:
            dict[int, tuple[float,float]] : {atom_index: [(pH, charge), ..], ...}
        """
        charge_groups_per_site = self.get_charge_groups_per_site()
        inflection_points = {}
        for atom_idx, charge_groups in charge_groups_per_site.items():
            # Calculate fraction of each protonation state or charge vs pH
            site_charge = np.sum(
                [
                    q * p[st_indices].sum(axis=0)
                    for q, st_indices in charge_groups.items()
                ],
                axis=0,
            )
            results = InflectionDetector(ph_values, site_charge).analyze(
                require_plateaus=True, high_confidence=True
            )
            inflection_points[atom_idx] = [
                (float(r["x"]), float(r["y"])) for r in results
            ]

        return inflection_points

    def get_macro_pKa(
        self, ph_values: np.ndarray, p: np.ndarray
    ) -> list[tuple[float, float]]:
        """
        Compute inflection points in pH vs charge that could be macroscopic pKa values.
        For example, ideal pKa transitions should happen at +2.5, +1.5, +0.5, -0.5 in case of +3 to -1 charges.

        Args:
            ph_values (np.ndarray): Array of pH values to evaluate populations
            p (nd.ndarray): Population matrix for each state at each pH

        Returns:
            list[tuple[float,float]] : [(pH, charge), ...]
        """
        # Group microstates by proton count or charge
        charge_groups = self.get_charge_groups()
        charge = np.sum(
            [q * p[st_indices].sum(axis=0) for q, st_indices in charge_groups.items()],
            axis=0,
        )
        results = InflectionDetector(ph_values, charge).analyze(
            require_plateaus=True, high_confidence=True
        )
        inflection_points = [(float(r["x"]), float(r["y"])) for r in results]

        return inflection_points

    def get_plot_data_pH_vs_population(
        self,
        ph_values: np.ndarray,
        p: np.ndarray,
        threshold: float = 0.0,
    ) -> tuple[dict, list[int]]:
        """Get an Altair plot object for pH-dependent population curve.

        For Altair chart:

            ```py
            # plot pH vs population

            import pandas as pd
            import altair as alt

            width = 600
            height = 300
            palette = 'tableau10'

            df = pd.DataFrame(data)

            # line plot
            lineplot = alt.Chart(df).mark_line().encode(
                x=alt.X('pH:Q', title='pH'),
                y=alt.Y('p:Q', title='Population'),
                color=alt.Color('microstate:N', scale=alt.Scale(scheme=palette)),
            ).properties(
                width=width,
                height=height)

            # data labels
            labels = alt.Chart(df).mark_text(
                align='left',
                dx=5,
                dy=-5
            ).encode(
                x=alt.X('pH', aggregate={'argmax': 'p'}),
                y=alt.Y('p', aggregate={'argmax': 'p'}),
                text='microstate:N',
                color='microstate:N'
            )

            chart = (lineplot + labels)
            ```
        Args:
            pH (np.ndarray): array of pH values.
            C (float): constant for pH-dependent dG calculation. Defaults to ln(10).
            beta (float, optional): \\( \\beta = \\frac{1}{k_{B} T} \\). Defaults to 1.0.
            threshold (float) : threshold to ignore low populated microstates. Defaults to 0.0.

        Returns:
            (dict, microstate indices):
                dict: {'pH':list[float], 'p':list[float], 'microstate':list[int(1-based)]}
                microstate indices: list of state index (0-based)
        """
        # prepare a dictionary for dataframe and state indices
        plot_data = {"microstate": [], "pH": [], "p": []}
        microstate_indice = []
        for i, pH_dependent_populations in enumerate(p):
            if max(pH_dependent_populations) < threshold:
                continue
            microstate_indice.append(i)
            j = len(microstate_indice)
            for k, pop in enumerate(pH_dependent_populations):
                plot_data["microstate"].append(
                    j
                )  # for colors, 1,2,... continuous numbers
                plot_data["pH"].append(float(ph_values[k]))  # for X-axis
                plot_data["p"].append(float(pop))  # for Y-axis

        return (plot_data, microstate_indice)

    def get_plot_data_pH_vs_charge(
        self, ph_values: np.ndarray, p: np.ndarray
    ) -> tuple[dict, list]:
        charge_groups = self.get_charge_groups()
        charge = np.sum(
            [q * p[st_indices].sum(axis=0) for q, st_indices in charge_groups.items()],
            axis=0,
        )
        results = InflectionDetector(ph_values, charge).analyze(
            require_plateaus=True, high_confidence=True
        )
        inflection_points = [(float(r["x"]), float(r["y"])) for r in results]
        # convert numpy array to list of floats
        plot_data = {"pH": ph_values.tolist(), "charge": charge.tolist()}

        return (plot_data, inflection_points)

    def get_plot_data_pH_vs_site_charge(
        self, ph_values: np.ndarray, p: np.ndarray
    ) -> tuple[dict, dict]:
        charge_groups_per_site = self.get_charge_groups_per_site()
        plot_data = {"site": [], "pH": [], "charge": []}
        inflection_points = {}
        for atom_idx, charge_groups in charge_groups_per_site.items():
            # Calculate fraction of each protonation state or charge vs pH
            site_charge = np.sum(
                [
                    q * p[st_indices].sum(axis=0)
                    for q, st_indices in charge_groups.items()
                ],
                axis=0,
            )
            results = InflectionDetector(ph_values, site_charge).analyze(
                require_plateaus=True, high_confidence=True
            )
            inflection_points[atom_idx] = [
                (float(r["x"]), float(r["y"])) for r in results
            ]
            for ph, q in zip(ph_values, site_charge):
                plot_data["pH"].append(float(ph))
                plot_data["charge"].append(float(q))
                plot_data["site"].append(atom_idx)

        return (plot_data, inflection_points)

    def serialize(self) -> str:
        """Serialize states to a string."""
        data = [st.serialize() for st in self.states]
        encoded_str = json.dumps(data)

        return encoded_str

    def deserialize(self, encoded_str: str) -> Self:
        """Deserialize states from a string."""
        data = json.loads(encoded_str)
        self.states = [State().deserialize(_) for _ in data]

        return self


class StateNetwork:
    def __init__(self):
        self.graph = nx.DiGraph()
        self.visited_states = []
        self.initial_state = None

    def copy(self) -> Self:
        """Copy."""
        return copy.deepcopy(self)

    def build(
        self,
        smiles: str,
        origin: str | None = None,
        transformation: str | None = None,
        min_formal_charge: int = -2,
        max_formal_charge: int = +2,
        min_atomic_charge: int = -1,
        max_atomic_charge: int = +1,
        protomer_rule: str = "default",
        tautomer_rule: str | None = None,
        verbose: bool = False,
    ) -> Self:
        """Build the microstate network using BFS from initial state."""
        self.initial_state = State(
            smiles=smiles,
            protomer_rule=protomer_rule,
            tautomer_rule=tautomer_rule,
            min_formal_charge=min_formal_charge,
            max_formal_charge=max_formal_charge,
            min_atomic_charge=min_atomic_charge,
            max_atomic_charge=max_atomic_charge,
        )
        self.initial_state
        # Initialize BFS
        queue = deque([self.initial_state])
        self.visited_states.append(self.initial_state)
        self.graph.add_node(
            self.initial_state.smiles,
            initial=True,
            sites=self.initial_state.site_info(),
        )
        iter = 0

        while queue:
            iter += 1
            current_state = queue.popleft()
            neighbors = self._generate_neighbors(current_state)
            for neighbor_state in neighbors:
                if (
                    neighbor_state.transformation == "Tautomer"
                    and current_state.charge != neighbor_state.charge
                ):
                    continue
                self.graph.add_edge(
                    current_state.smiles,
                    neighbor_state.smiles,
                    transformation=neighbor_state.transformation,
                )
                if neighbor_state not in self.visited_states:
                    self.visited_states.append(neighbor_state)
                    imap = self._mcs_index_map(neighbor_state)
                    sites = [
                        (a, imap[i], q, pr, de)
                        for (a, i, q, pr, de) in neighbor_state.site_info()
                    ]
                    self.graph.add_node(
                        neighbor_state.smiles, initial=False, sites=sites
                    )
                    queue.append(neighbor_state)
            if verbose:
                print(
                    f"Iteration {iter:2}: {len(self.visited_states):2} microstates found"
                )

        if verbose:
            print(f"\nNetwork construction complete!")
            print(f"Total microstates: {len(self.graph.nodes())}")
            print(f"Total transformations: {len(self.graph.edges())}")

        return self

    def set_energies(self, dG: list[float] | np.ndarray, ref_ph: float = 7.0) -> Self:
        """Set energies to states.

        Args:
            energies (list[float] | np.ndarray): list or array of energies.

        Returns:
            Self: self
        """
        assert len(dG) == self.size(), (
            "The number of energies does not match the number of states"
        )
        for i, energy in enumerate(dG):
            self.visited_states[i].energy = float(energy)
            self.visited_states[i].ref_ph = ref_ph
        return self

    def trim(self, p: np.ndarray, threshold: float = 0.0) -> Self:
        """Remove states whose pH-dependent population is not above a given threshold at pH values.

        Args:
            p (np.ndarray): array of populations.
            threshold (float, optional): min population. Defaults to 0.0.

        Returns:
            Self: StateNetwork
        """

        retain_mask = [False if max(ph_p) < threshold else True for ph_p in p]
        remove_mask = [not b for b in retain_mask]
        nodes_to_remove = list(
            itertools.compress([st.smiles for st in self.visited_states], remove_mask)
        )

        self.graph.remove_nodes_from(nodes_to_remove)
        self.visited_states = list(itertools.compress(self.visited_states, retain_mask))

        return self

    def get_state_ensemble(self, index: int | slice | None = None) -> StateEnsemble:
        """Get states by index or slice or all states."""
        if isinstance(index, slice):
            return StateEnsemble(self.visited_states[index])
        elif isinstance(index, int):
            return StateEnsemble([self.visited_states[index]])
        else:  # all
            return StateEnsemble(self.visited_states)

    def _generate_neighbors(self, state: State) -> StateEnsemble:
        """Generate all possible neighboring microstates."""
        neighbors = StateEnsemble()
        if state == self.initial_state and isinstance(state.tautomer_rule, str):
            neighbors += StateEnsemble(state.get_tautomers())
        neighbors += StateEnsemble(state.get_protonated())
        neighbors += StateEnsemble(state.get_deprotonated())
        neighbors = neighbors.drop()

        return neighbors

    def get_initial_state(self) -> State:
        """Get the initial state."""
        return self.initial_state

    def info(self) -> None:
        """Print information of the network."""
        print(
            f"StateNetwork - nodes: {self.get_num_nodes()} edeges: {self.get_num_edges()}"
        )

    def size(self) -> int:
        """Number of unique states in the network."""
        return len(self.visited_states)

    def get_num_nodes(self) -> int:
        """Number of nodes in the network."""
        return len(self.graph.nodes())

    def get_num_edges(self) -> int:
        """Number of edges in the network."""
        return len(self.graph.edges())

    def _mcs_index_map(self, other: State) -> dict[int, int]:
        """Mapping atom indices using the maximum common structure (MCS).

        Uses the self.initial_state as reference in mapping `other` State.

        Args:
            other (State): to be mapped state.

        Returns:
            dict: {ref atom index: other atom index, ...}
        """
        mcs = Chem.rdFMCS.FindMCS(
            [self.initial_state.rdmol, other.rdmol],
            atomCompare=Chem.rdFMCS.AtomCompare.CompareAny,
            bondCompare=Chem.rdFMCS.BondCompare.CompareAny,
            completeRingsOnly=True,
        )
        mcs_rdmol = Chem.MolFromSmarts(mcs.smartsString)
        match_1 = self.initial_state.rdmol.GetSubstructMatch(mcs_rdmol)
        match_2 = other.rdmol.GetSubstructMatch(mcs_rdmol)
        return {match_2[i]: match_1[i] for i in range(len(match_1))}

    def get_micro_pKa(
        self, ph_values: np.ndarray, p: np.ndarray
    ) -> dict[int, list[tuple[float, float]]]:
        """Calculate micro-pKa with provided potential energies.

        Args:

        Returns:
            dict[int,list[float]]: micro-pKa values for each ionizable site.
        """
        state_ens = StateEnsemble(self.visited_states)
        return state_ens.get_micro_pKa(ph_values, p)

    def get_macro_pKa(
        self, ph_values: np.ndarray, p: np.ndarray
    ) -> list[tuple[float, float]]:
        """Calculatate macro-pKa with provided potential energies.

        Args:

        Returns:
            list[tuple[float,float]] : [(pH, charge), ...]
        """
        state_ens = StateEnsemble(self.visited_states)
        return state_ens.get_macro_pKa(ph_values, p)

    def get_population(
        self, ph_values: np.ndarray, C: float = ln10, beta: float = 1.0
    ) -> np.ndarray:
        """Calculate populations with provided potential energies and pH.

        The reference state can be arbitrary and is set to the initial_state here.

        \\[
        \\begin{align}
        \\Delta G_{i, ref} &= PE_{i} - PE_{ref} \\\\[0.5em]
        \\Delta m_{i, ref} &= charge_{i} - charge _{ref} \\\\[0.5em]
        \\Delta G_{i, pH} &= \\Delta G_{i, ref} + \\Delta m_{i, ref} C pH \\\\[0.5em]
        p_{i, pH} &= \\frac {exp(-\\beta \\Delta G_{i, pH})}{\\sum_{i} exp(-\\beta \\Delta G_{i, pH})}
        \\end{align}
        \\]

        Args:
            pH (np.ndarray): array of pH values.
            C (float): constant for pH-dependent dG calculation. Defaults to ln(10).
            beta (float, optional): \\( \\beta = \\frac{1}{k_{B} T} \\). Defaults to 1.0.

        Returns:
            np.ndarray:
                array of populations with shape of (number of states, number of pH).
        """
        state_ens = StateEnsemble(self.visited_states)
        return state_ens.get_population(ph_values, C, beta)

    def get_plot_data_pH_vs_population(
        self, ph_values: np.ndarray, p: np.ndarray, threshold: float = 0.0
    ) -> tuple[dict, list[int]]:
        """Make an Altair plot object for pH-dependent population curve.

                Args:
                    pH (np.ndarray): array of pH values.
                    C (float): constant for pH-dependent dG calculation. Defaults to ln(10).
        .            beta (float, optional): \\( \\beta = \\frac{1}{k_{B} T} \\). Defaults to 1.0.
                    threshold (float) : threshold to ignore low populated microstates. Defaults to 0.0.

                Returns:
                    (dict, indices):
                        dict: {'pH':list[float], 'p':list[float], 'microstate':list[int(1-based)]}
                        indices: list of state index (0-based)
        """
        state_ens = StateEnsemble(self.visited_states)
        return state_ens.get_plot_data_pH_vs_population(ph_values, p, threshold)

    def get_plot_data_pH_vs_site_charge(
        self, ph_values: np.ndarray, p: np.ndarray
    ) -> tuple[dict, dict]:
        state_ens = StateEnsemble(self.visited_states)
        return state_ens.get_plot_data_pH_vs_site_charge(ph_values, p)

    def get_plot_data_pH_vs_charge(
        self, ph_values: np.ndarray, p: np.ndarray
    ) -> tuple[dict, list]:
        state_ens = StateEnsemble(self.visited_states)
        return state_ens.get_plot_data_pH_vs_charge(ph_values, p)

    def serialize(self) -> str:
        """Serialize the network to a string."""
        data = {
            "graph": json_graph.adjacency_data(
                self.graph
            ),  # Convert to JSON-compatible dictionary
            "visited_states": [st.serialize() for st in self.visited_states],
            "initial_state": (
                self.initial_state.serialize() if self.initial_state else None
            ),
        }
        encoded_str = json.dumps(data)

        return encoded_str

    def deserialize(self, encoded_str: str) -> Self:
        """Deserialize the network from a string."""
        obj = json.loads(encoded_str)
        self.graph = json_graph.adjacency_graph(obj["graph"])
        self.visited_states = [State().deserialize(st) for st in obj["visited_states"]]
        self.initial_state = State().deserialize(obj["initial_state"])

        return self


class QupkakeMicrostates:
    def __init__(self, origin: Mol, calculator: str = "xTB"):
        self.origin = origin
        self.calculator = calculator
        self.basic_sites = []
        self.acidic_sites = []
        self.states = []
        self.mols = []
        self.reference = None

    def enumerate(self) -> None:
        # Qu pKake results must be stored at .confs
        for conf in self.origin:
            pka = conf.props.get("pka", None)
            if pka is None:
                # no protonation/deprotonation sites
                continue
            if isinstance(pka, str) and pka.startswith("tensor"):
                # ex. 'tensor(9.5784)'
                pka = float(pka.replace("tensor(", "").replace(")", ""))
            if conf.props.get("pka_type") == "basic":
                self.basic_sites.append(conf.props.get("idx"))
            elif conf.props.get("pka_type") == "acidic":
                self.acidic_sites.append(conf.props.get("idx"))

        # enumerate protonation/deprotonation sites to generate microstates

        np = len(self.basic_sites)
        nd = len(self.acidic_sites)
        P = [
            c
            for n in range(np + 1)
            for c in itertools.combinations(self.basic_sites, n)
        ]
        D = [
            c
            for n in range(nd + 1)
            for c in itertools.combinations(self.acidic_sites, n)
        ]

        PD = list(itertools.product(P, D))

        for p, d in PD:
            conf = self.origin.confs[0].copy()
            conf = conf.protonate(p).deprotonate(d).optimize(calculator=self.calculator)
            charge = len(p) - len(d)
            self.states.append(
                SimpleNamespace(
                    charge=charge,
                    protonation_sites=p,
                    deprotonation_sites=d,
                    conf=conf,
                    smiles=Mol(conf).smiles,
                    delta_m=None,
                    PE=None,
                )
            )

        # sort microstates by ascending charges
        self.states = sorted(self.states, key=lambda x: x.charge)

    @staticmethod
    def Boltzmann_weighted_average(potential_energies: list) -> float:
        """Calculate Boltzmann weighted average potential energy at pH 0.

        Args:
            potential_energies (list): a list of potential energies.

        Returns:
            float: Boltzmann weighted average potential energy.
        """
        kT = 0.001987 * 298.0  # (kcal/mol K), standard condition
        C = math.log(10) * kT
        pe_array = np.array(potential_energies)
        pe = pe_array - min(potential_energies)
        Boltzmann_factors = np.exp(-pe / kT)
        Z = np.sum(Boltzmann_factors)
        p = Boltzmann_factors / Z

        return float(np.dot(p, pe_array))

    def populate(self) -> None:
        for microstate in self.states:
            mol = Mol(microstate.conf).make_confs(n=4).optimize_confs()
            # mol = mol.drop_confs(similar=True, similar_rmsd=0.3, verbose=True)
            # mol = mol.optimize_confs(calculator=calculator)
            # mol = mol.drop_confs(k=10, window=15.0, verbose=True)
            PE = []
            for conf in mol.confs:
                conf = conf.optimize(calculator=self.calculator, verbose=True)
                # GFN2xTB requires 3D coordinates
                # xtb = GFN2xTB(conf.rdmol).singlepoint(water='cpcmx', verbose=True)
                PE.append(conf.potential_energy(calculator=self.calculator))
                # xtb = GFN2xTB(conf.rdmol).singlepoint(verbose=True)
                # SimpleNamespace(
                #             PE = datadict['total energy'] * hartree2kcalpermol,
                #             Gsolv = Gsolv,
                #             charges = datadict['partial charges'],
                #             wbo = Wiberg_bond_orders,
                #             )
            microstate.PE = self.Boltzmann_weighted_average(PE)
            logger.info(f"PE= {PE}")
            logger.info(f"Boltzmann weighted= {microstate.PE}")
            self.mols.append(mol)

    def get_populations(self, pH: float) -> list[tuple]:
        # set the lowest dG as the reference
        self.reference = self.states[
            np.argmin([microstate.PE for microstate in self.states])
        ]
        for microstate in self.states:
            microstate.delta_m = microstate.charge - self.reference.charge
        dG = []
        for microstate in self.states:
            dG.append((microstate.PE - self.reference.PE) + microstate.delta_m * C * pH)
        dG = np.array(dG)

        logger.info(f"dG= {dG}")
        kT = 0.001987 * 298.0  # (kcal/mol K), standard condition
        C = math.log(10) * kT
        Boltzmann_factors = np.exp(-dG / kT)
        Z = np.sum(Boltzmann_factors)
        p = Boltzmann_factors / Z
        idx_p = sorted(list(enumerate(p)), key=lambda x: x[1], reverse=True)
        # [(0, p0), (1, p1), ...]

        return idx_p

    def get_ensemble(self) -> list[Mol]:
        return self.mols

    def get_mol(self, idx: int) -> Mol:
        return self.mols[idx]

    def count(self) -> int:
        return len(self.states)
