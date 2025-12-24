from rdkit import Chem
from rdkit.Chem import AllChem, DataStructs


def distance_function(i: int, j: int, fps: list) -> float:
    """Calculate Tanimoto distance between two fingerprints."""
    return 1.0 - DataStructs.TanimotoSimilarity(fps[i], fps[j])


def calculate_fingerprints(
    rdmols: list[Chem.Mol], fp_type: str = "morgan", radius: int = 2, n_bits: int = 2048
) -> list:
    """
    Calculate molecular fingerprints for a list of SMILES.

    Args:
        smiles_list: List of SMILES strings
        fp_type: Type of fingerprint ('morgan', 'rdkit', 'maccs')
        radius: Radius for Morgan fingerprints
        n_bits: Number of bits for fingerprints

    Returns:
        List of fingerprint objects
    """

    fps = []

    for mol in rdmols:
        if mol is None:
            fps.append(None)
            continue

        if fp_type == "morgan":
            fp = AllChem.GetMorganFingerprintAsBitVect(mol, radius, nBits=n_bits)
        elif fp_type == "rdkit":
            fp = Chem.RDKFingerprint(mol, fpSize=n_bits)
        elif fp_type == "maccs":
            fp = AllChem.GetMACCSKeysFingerprint(mol)
        else:
            raise ValueError(f"Unknown fingerprint type: {fp_type}")

        fps.append(fp)

    return fps
