"""
Author: TMJ
Date: 2025-12-01 15:22:40
LastEditors: TMJ
LastEditTime: 2025-12-21 22:21:27
Description: Generates comparison images for the README file.
- Default RDKit vs. rdkit-dof for a single molecule.
- Default RDKit vs. rdkit-dof for a grid of molecules.
"""

from rdkit import Chem
from rdkit.Chem import Draw
from rdkit.Chem.rdDistGeom import EmbedMolecule
from rdkit.Chem.rdForceFieldHelpers import MMFFOptimizeMolecule

from rdkit_dof import MolsToGridDofImage, MolToDofImage, dofconfig


def generate_single_mol_comparison():
    """Generates comparison for a single complex molecule."""
    print("Generating single molecule comparison...")
    smiles = "CC1=C2[C@@]([C@]([C@H]([C@@H]3[C@]4([C@H](OC4)C[C@@H]([C@]3(C(=O)[C@@H]2OC(=O)C)C)O)OC(=O)C)OC(=O)c5ccccc5)(C[C@@H]1OC(=O)[C@H](O)[C@@H](NC(=O)c6ccccc6)c7ccccc7)C)C"
    mol = Chem.MolFromSmiles(smiles)
    mol = Chem.AddHs(mol)
    EmbedMolecule(mol, randomSeed=42)
    MMFFOptimizeMolecule(mol)

    img_size = (600, 400)
    legend = "Paclitaxel"

    # 1. Default RDKit drawing
    img = Draw.MolToImage(mol, size=img_size)
    img.save("assets/comparison_single_default.png")
    print("  - Saved assets/comparison_single_default.png")

    # 1. Default RDKit drawing (SVG)
    drawer = Draw.rdMolDraw2D.MolDraw2DSVG(img_size[0], img_size[1])
    drawer.DrawMolecule(mol, legend=legend)
    drawer.FinishDrawing()
    img_svg = drawer.GetDrawingText()
    with open("assets/comparison_single_default.svg", "w") as f:
        f.write(img_svg)
    print("  - Saved assets/comparison_single_default.svg")

    # 2. rdkit-dof drawing
    dofconfig.use_style("default")
    MolToDofImage(
        mol,
        size=img_size,
        legend=legend,
        use_svg=False,
        return_image=False,
        filename="assets/comparison_single_dof.png",
    )
    print("  - Saved assets/comparison_single_dof.png")

    # 2. rdkit-dof drawing (SVG)
    MolToDofImage(
        mol,
        size=img_size,
        legend=legend,
        use_svg=True,
        return_image=False,
        filename="assets/comparison_single_dof.svg",
    )
    print("  - Saved assets/comparison_single_dof.svg")


def generate_grid_comparison():
    """Generates comparison for a grid of molecules."""
    print("Generating grid comparison...")
    smiles_list = [
        "CC(=O)Oc1ccccc1C(=O)O",  # Aspirin
        "CC(C)CC1=CC=C(C=C1)C(C)C(=O)O",  # Ibuprofen
        "CN1C=NC2=C1C(=O)N(C(=O)N2C)C",  # Caffeine
        "CC(=O)NC1=CC=C(O)C=C1",  # Paracetamol
        "CCO",  # Ethanol
        "OCC1OC(CCC2=CNC3=CC=CC=C32)C(O)C(O)C1O",  # Serotonin
        "C(C(C(C(C(=O)CO)O)O)O)O",  # Glucose (open-chain)
        "C([C@@H]1[C@H]([C@@H]([C@H](C(O1)O)O)O)O)O",  # Glucose (closed-chain)
    ]
    mols = [Chem.MolFromSmiles(s) for s in smiles_list]
    legends = [
        "Aspirin",
        "Ibuprofen",
        "Caffeine",
        "Paracetamol",
        "Ethanol",
        "Serotonin",
        "Glucose (open-chain)",
        "Glucose (closed-chain)",
    ]

    # Generate 3D conformer for each
    mols_with_conformer = []
    for mol in mols:
        mol = Chem.AddHs(mol)
        EmbedMolecule(mol, randomSeed=42)
        MMFFOptimizeMolecule(mol)
        mols_with_conformer.append(mol)

    img_size = (300, 300)
    mols_per_row = 2  # Adjusted for better layout

    # 1. Default RDKit grid
    grid_img = Draw.MolsToGridImage(
        mols_with_conformer,
        molsPerRow=mols_per_row,
        subImgSize=(img_size[0] * 2, img_size[1] * 2),
        legends=legends,
        useSVG=False,
        returnPNG=False,
    )
    grid_img.save("assets/comparison_grid_default.png", dpi=(800, 800))
    print("  - Saved assets/comparison_grid_default.png")

    grid_img_svg = Draw.MolsToGridImage(
        mols_with_conformer,
        molsPerRow=mols_per_row,
        subImgSize=img_size,
        legends=legends,
        useSVG=True,
    )
    with open("assets/comparison_grid_default.svg", "w") as f:
        f.write(grid_img_svg.data)
    print("  - Saved assets/comparison_grid_default.svg")

    # 2. rdkit-dof grid
    dofconfig.use_style("default")
    MolsToGridDofImage(
        mols_with_conformer,
        molsPerRow=mols_per_row,
        subImgSize=(img_size[0] * 2, img_size[1] * 2),
        legends=legends,
        use_svg=False,
        return_image=False,
        filename="assets/comparison_grid_dof.png",
    )
    print("  - Saved assets/comparison_grid_dof.png")

    MolsToGridDofImage(
        mols_with_conformer,
        molsPerRow=mols_per_row,
        subImgSize=img_size,
        legends=legends,
        use_svg=True,
        return_image=False,
        filename="assets/comparison_grid_dof.svg",
    )
    print("  - Saved assets/comparison_grid_dof.svg")


def generate_highlighting_showcase():
    """Generates images showcasing the highlighting functionality."""
    print("Generating highlighting showcase...")

    # 1. Single molecule highlighting
    mol = Chem.MolFromSmiles("COc1ccc(C(=O)O)cc1")  # Anisic acid
    mol = Chem.AddHs(mol)
    EmbedMolecule(mol, randomSeed=42)
    MMFFOptimizeMolecule(mol)

    # Highlight the carboxylic acid group (C(=O)O)
    patt = Chem.MolFromSmarts("C(=O)[OH]")
    match = mol.GetSubstructMatch(patt)

    img_size = (400, 300)
    legend = "Anisic acid (COOH highlighted)"

    dofconfig.use_style("default")

    # Test highlightAtoms and highlightBonds
    # Find bonds between matched atoms
    highlight_bonds = []
    for b in mol.GetBonds():
        if b.GetBeginAtomIdx() in match and b.GetEndAtomIdx() in match:
            highlight_bonds.append(b.GetIdx())

    MolToDofImage(
        mol,
        size=img_size,
        legend=legend,
        highlightAtoms=match,
        highlightBonds=highlight_bonds,
        highlightColor=(0.0, 1.0, 0.0, 0.5),  # Green highlight
        use_svg=False,
        return_image=False,
        filename="assets/showcase_highlight_single.png",
    )
    print("  - Saved assets/showcase_highlight_single.png")

    # 1. Single molecule highlighting (SVG)
    MolToDofImage(
        mol,
        size=img_size,
        legend=legend,
        highlightAtoms=match,
        highlightBonds=highlight_bonds,
        highlightColor=(0.0, 1.0, 0.0, 0.5),  # Green highlight
        use_svg=True,
        return_image=False,
        filename="assets/showcase_highlight_single.svg",
    )
    print("  - Saved assets/showcase_highlight_single.svg")

    # 2. Grid highlighting
    smiles_list = [
        "c1ccccc1C(=O)O",  # Benzoic acid
        "CCO",  # Ethanol
        "CC(=O)O",  # Acetic acid
        "c1ccccc1O",  # Phenol
    ]
    mols = [Chem.MolFromSmiles(s) for s in smiles_list]
    legends = ["Benzoic acid", "Ethanol", "Acetic acid", "Phenol"]

    patt_acid = Chem.MolFromSmarts("C(=O)[OH]")
    patt_hydroxyl = Chem.MolFromSmarts("[OH]")

    highlight_atom_lists = []
    highlight_bond_lists = []

    mols_with_conformer = []
    for m in mols:
        m = Chem.AddHs(m)
        EmbedMolecule(m, randomSeed=42)
        MMFFOptimizeMolecule(m)
        mols_with_conformer.append(m)

        # Highlight acid group if present, else hydroxyl
        match = m.GetSubstructMatch(patt_acid)
        if not match:
            match = m.GetSubstructMatch(patt_hydroxyl)

        highlight_atom_lists.append(match)

        bonds = []
        for b in m.GetBonds():
            if b.GetBeginAtomIdx() in match and b.GetEndAtomIdx() in match:
                bonds.append(b.GetIdx())
        highlight_bond_lists.append(bonds)

    MolsToGridDofImage(
        mols_with_conformer,
        molsPerRow=2,
        subImgSize=(300, 300),
        legends=legends,
        highlightAtomLists=highlight_atom_lists,
        highlightBondLists=highlight_bond_lists,
        highlightColor=(1.0, 0.5, 0.0, 1.0),  # Orange highlight
        use_svg=False,
        return_image=False,
        filename="assets/showcase_highlight_grid.png",
    )
    print("  - Saved assets/showcase_highlight_grid.png")

    # 2. Grid highlighting (SVG)
    MolsToGridDofImage(
        mols_with_conformer,
        molsPerRow=2,
        subImgSize=(300, 300),
        legends=legends,
        highlightAtomLists=highlight_atom_lists,
        highlightBondLists=highlight_bond_lists,
        highlightColor=(1.0, 0.5, 0.0, 1.0),  # Orange highlight
        use_svg=True,
        return_image=False,
        filename="assets/showcase_highlight_grid.svg",
    )
    print("  - Saved assets/showcase_highlight_grid.svg")


if __name__ == "__main__":
    generate_single_mol_comparison()
    print("-" * 20)
    generate_grid_comparison()
    print("-" * 20)
    generate_highlighting_showcase()
    print("\nAll comparison images generated successfully.")
