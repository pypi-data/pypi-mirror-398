"""Chemistry utils for refinery."""

from typing import Optional

from rdkit import Chem, rdBase

__all__ = ["generate_inchikey"]

rdBase.DisableLog("rdApp.warning")
rdBase.DisableLog("rdApp.error")


def generate_inchikey(
    s: str, rgroup_smiles: Optional[str] = None, ignore_direction: bool = False
) -> str:
    """Generate INChI key from SMILES or reaction SMILES string.
       Passes exceptions to the caller.

    Args:
        s (str): SMILES or reaction SMILES
        rgroup_smiles (Optional[str]): Replacement SMILES string for R groups (*).
            If None, R groups raise a ValueError.
        ignore_direction (bool, optional): Ignore direction in reaction SMILES.
            Has no effect on SMILES. Defaults to False.

    Returns:
        str: INChI key of molecule (products>>substrates)
    """

    if ">>" in s:
        reactants, products = s.split(">>", maxsplit=1)
        reactants_inchikey = generate_inchikey(reactants, rgroup_smiles=rgroup_smiles)
        products_inchikey = generate_inchikey(products, rgroup_smiles=rgroup_smiles)
        if ignore_direction and reactants_inchikey > products_inchikey:
            reaction_inchikey = products_inchikey + ">>" + reactants_inchikey
        else:
            reaction_inchikey = reactants_inchikey + ">>" + products_inchikey
        return reaction_inchikey
    elif "*" in s:
        if rgroup_smiles is not None:
            replaced_smiles = s.replace("*", rgroup_smiles)
            if "()" in replaced_smiles:
                replaced_smiles = replaced_smiles.replace("()", "")
            return generate_inchikey(replaced_smiles)
        else:
            raise ValueError(
                f"Found R (*) groups in SMILES string {s}. Set rgroup_smiles to replace."
            )
    elif s != "":
        rdmol = None
        try:
            rdmol = Chem.MolFromSmiles(s, sanitize=True)  # type: ignore
        except Exception:
            pass
        if rdmol is None:
            raise ValueError(f"Invalid SMILES string {s}")
        inchikey = Chem.MolToInchiKey(rdmol)
        if inchikey != "":
            return inchikey
        else:
            raise ValueError("Could not generate INChI key")
    else:
        raise ValueError("Empty SMILES string")
