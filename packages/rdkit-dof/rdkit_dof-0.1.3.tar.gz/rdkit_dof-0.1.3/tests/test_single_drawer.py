"""
Author: TMJ
Date: 2025-12-01 14:54:08
LastEditors: TMJ
LastEditTime: 2025-12-21 22:40:15
Description: Test the core functionality of MolToDofImage.
"""

import pytest
from PIL.Image import Image
from rdkit import Chem
from rdkit.Chem.rdDistGeom import EmbedMolecule
from rdkit.Chem.rdForceFieldHelpers import MMFFOptimizeMolecule

from rdkit_dof.config import dofconfig
from rdkit_dof.core import MolToDofImage

try:
    from IPython.display import SVG
except ImportError:
    pass


@pytest.fixture(scope="module")
def sample_mol_3d():
    """
    Provides a sample molecule (methane) with 3D coordinates.
    """
    mol = Chem.MolFromSmiles("C")
    mol = Chem.AddHs(mol)
    EmbedMolecule(mol, randomSeed=42)
    MMFFOptimizeMolecule(mol)
    return mol


@pytest.fixture(scope="module")
def sample_mol_2d():
    """
    Provides a sample molecule with only 2D coordinates.
    """
    mol = Chem.MolFromSmiles("c1cnccc1")  # Pyridine
    return mol


@pytest.fixture(scope="module")
def empty_mol():
    """
    Provides an empty molecule.
    """
    return Chem.Mol()


def test_mol_to_dof_image_returns_png_image(sample_mol_3d):
    """
    Tests that MolToDofImage returns a PIL Image for PNG output.
    """
    # WHEN
    img = MolToDofImage(sample_mol_3d, use_svg=False, return_image=True)

    # THEN
    assert img is not None
    assert isinstance(img, Image)


@pytest.mark.skipif(SVG is None, reason="IPython is not installed")
def test_mol_to_dof_image_returns_svg_image(sample_mol_3d):
    """
    Tests that MolToDofImage returns an SVG object for SVG output.
    """
    # WHEN
    svg = MolToDofImage(sample_mol_3d, use_svg=True, return_image=True)

    # THEN
    assert svg is not None
    assert isinstance(svg, SVG)


def test_mol_to_dof_image_returns_png_bytes(sample_mol_3d):
    """
    Tests that MolToDofImage returns bytes for PNG raw data output.
    """
    # WHEN
    png_data = MolToDofImage(sample_mol_3d, use_svg=False, return_image=False)

    # THEN
    assert png_data is not None
    assert isinstance(png_data, bytes)
    # Check for PNG header
    assert png_data.startswith(b"\x89PNG\r\n\x1a\n")


def test_mol_to_dof_image_returns_svg_str(sample_mol_3d):
    """
    Tests that MolToDofImage returns a string for SVG raw data output.
    """
    # WHEN
    svg_text = MolToDofImage(sample_mol_3d, use_svg=True, return_image=False)

    # THEN
    assert svg_text is not None
    assert isinstance(svg_text, str)
    assert "<svg" in svg_text
    assert svg_text.strip().endswith("</svg>")


def test_mol_to_dof_image_handles_2d_mol(sample_mol_2d):
    """
    Tests that MolToDofImage can process a molecule with no 3D conformer.
    """
    # WHEN
    img = MolToDofImage(sample_mol_2d, use_svg=False)

    # THEN
    assert img is not None
    assert isinstance(img, Image)


def test_mol_to_dof_image_raises_error_for_none_mol(empty_mol):
    """
    Tests that MolToDofImage raises a ValueError for an invalid molecule.
    The internal helper _prepare_mol_data raises the error.
    """
    # THEN
    with pytest.raises(ValueError, match="Invalid molecule"):
        # WHEN
        MolToDofImage(None)  # type: ignore


def test_mol_to_dof_image_handles_empty_mol(empty_mol):
    """
    Tests that MolToDofImage can handle an empty molecule object without errors.
    """
    # WHEN
    img = MolToDofImage(empty_mol, use_svg=False)

    # THEN
    assert img is not None
    assert isinstance(img, Image)


def test_use_style_switches_configuration(sample_mol_3d):
    """
    Tests that use_style correctly updates the global config object.
    """
    # GIVEN
    # Reset to default state first
    dofconfig.use_style("default")
    default_fog = dofconfig.fog_color
    default_carbon_color = dofconfig.get_atom_color(6)

    # WHEN
    dofconfig.use_style("dark")

    # THEN
    assert dofconfig.preset_style == "dark"
    assert dofconfig.fog_color != default_fog
    assert dofconfig.fog_color == (0.1, 0.1, 0.1)
    assert dofconfig.get_atom_color(6) != default_carbon_color

    # Clean up by resetting to default for other tests
    dofconfig.use_style("default")


def test_mol_to_dof_image_highlighting(sample_mol_3d):
    """
    Tests that MolToDofImage accepts highlighting parameters without error.
    """
    # WHEN
    img = MolToDofImage(
        sample_mol_3d,
        use_svg=False,
        highlightAtoms=[0],
        highlightBonds=[0],
        highlightColor=(0, 1, 0, 0.5),
    )

    # THEN
    assert img is not None
    assert isinstance(img, Image)


def test_mol_to_dof_image_saves_png_file(sample_mol_3d, tmp_path):
    """
    Tests that MolToDofImage saves a PNG file when filename is provided.
    """
    # GIVEN
    output_file = tmp_path / "test_output.png"

    # WHEN
    MolToDofImage(sample_mol_3d, use_svg=False, filename=str(output_file))

    # THEN
    assert output_file.exists()
    assert output_file.stat().st_size > 0
    with open(output_file, "rb") as f:
        header = f.read(8)
        assert header.startswith(b"\x89PNG\r\n\x1a\n")


def test_mol_to_dof_image_saves_svg_file(sample_mol_3d, tmp_path):
    """
    Tests that MolToDofImage saves an SVG file when filename is provided.
    """
    # GIVEN
    output_file = tmp_path / "test_output.svg"

    # WHEN
    MolToDofImage(sample_mol_3d, use_svg=True, filename=str(output_file))

    # THEN
    assert output_file.exists()
    assert output_file.stat().st_size > 0
    with open(output_file) as f:
        content = f.read()
        assert "<svg" in content
        assert content.strip().endswith("</svg>")
