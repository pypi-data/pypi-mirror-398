from rdkit import Chem
from rdkit.Chem.EnumerateStereoisomers import (
    EnumerateStereoisomers,
    StereoEnumerationOptions,
)


def correct_wedged_bonds(rdmol: Chem.Mol) -> None:
    """Corrects wedged bonds for chiral centers.
    Args:
        rdmol (Chem.Mol): input molecule.
    
    1. Clear all stereochemistry information
    2. Identify chiral centers and non-chiral atoms/bonds
    3. Reassign stereochemistry only where appropriate
    4. Return the modified molecule
    """
    chiral_centers = Chem.FindMolChiralCenters(rdmol, includeUnassigned=True)
    chiral_atom_idx = [atom_idx for atom_idx, chirality in chiral_centers]
    for bond in rdmol.GetBonds():
        ai = bond.GetBeginAtom()
        aj = bond.GetEndAtom()
        is_chiral = [ai.GetIdx() in chiral_atom_idx, aj.GetIdx() in chiral_atom_idx]
        if any(is_chiral):
            continue
        else:
            # clear atom chirality
            if not is_chiral[0]:
                ai.SetChiralTag(Chem.ChiralType.CHI_UNSPECIFIED)
            if not is_chiral[1]:
                aj.SetChiralTag(Chem.ChiralType.CHI_UNSPECIFIED)
            # clear bond directions (wedge/dash) and bond stereo
            bond.SetBondDir(Chem.BondDir.NONE)
            bond.SetStereo(Chem.BondStereo.STEREONONE)
    # 3. Reassign stereochemistry only where appropriate
    Chem.AssignStereochemistry(rdmol, cleanIt=True, force=True)


def enumerate_stereoisomers(rdmol: Chem.Mol) -> list[Chem.Mol]:
    """Returns enumerated stereoisomers.

    Args:
        rdmol (Chem.Mol): input molecule.

    Returns:
        List[Chem.Mol]: a list of enumerated stereoisomers.
    """
    return list(
        EnumerateStereoisomers(
            rdmol,
            options=StereoEnumerationOptions(
                tryEmbedding=False,
                onlyUnassigned=True,
                maxIsomers=1024,
                rand=None,
                unique=True,
                onlyStereoGroups=False
            ),
        )
    )


def enumerate_ring_bond_stereoisomers(
    rdmol: Chem.Mol, ring_bond_stereo_info: list[tuple], override: bool = False
) -> list[Chem.Mol]:
    """Enumerates unspecified double bond stereochemistry (cis/trans).

    Small rings (< 8 atoms): 
        RDKit does NOT enumerate E/Z stereochemistry for double bonds 
        because the ring constraints make one configuration impossible
    
    Macrocycles (≥ 8 atoms): 
        RDKit CAN enumerate E/Z stereochemistry for double bonds 
        since both configurations are geometrically feasible

    Args:
        rdmol (Chem.Mol): input molecule.
        ring_bond_stereo_info (List[Tuple]): 
            ring_bond_stereo_info will be set when .remove_stereo() is called.
            bond_stereo_info = [(bond_idx, bond_stereo_descriptor), ..] where
            bond_stereo_descriptor is `Chem.StereoDescriptor.Bond_Cis` or
            `Chem.StereoDescriptor.Bond_Trans`, or `Chem.StereoDescriptor.NoValue`.
        override (bool, optional): _description_. Defaults to False.

    Returns:
        List[Chem.Mol]: list of enumerated stereoisomers.
    """
    isomers = []
    for bond_idx, bond_stereo_desc in ring_bond_stereo_info:
        if (bond_stereo_desc == Chem.StereoDescriptor.NoValue) or override:
            bond = rdmol.GetBondWithIdx(bond_idx)
            (a2, a3) = (bond.GetBeginAtom(), bond.GetEndAtom())
            a2_idx = a2.GetIdx()
            a3_idx = a3.GetIdx()
            a1_idx = sorted(
                [
                    (a.GetIdx(), a.GetAtomicNum())
                    for a in a2.GetNeighbors()
                    if a.GetIdx() != a3_idx
                ],
                key=lambda x: x[1],
                reverse=True,
            )[0][0]
            a4_idx = sorted(
                [
                    (a.GetIdx(), a.GetAtomicNum())
                    for a in a3.GetNeighbors()
                    if a.GetIdx() != a2_idx
                ],
                key=lambda x: x[1],
                reverse=True,
            )[0][0]
            bond.SetStereoAtoms(a1_idx, a4_idx)  # need to set reference atoms
            # cis
            bond.SetStereo(Chem.BondStereo.STEREOCIS)
            isomers.append(Chem.Mol(rdmol))
            # trans
            bond.SetStereo(Chem.BondStereo.STEREOTRANS)
            isomers.append(Chem.Mol(rdmol))
    return isomers
