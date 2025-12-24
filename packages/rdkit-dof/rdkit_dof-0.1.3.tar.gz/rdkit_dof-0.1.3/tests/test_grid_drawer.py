import base64

import pytest
from PIL import Image
from rdkit import Chem
from rdkit.Chem.rdDistGeom import EmbedMolecule

from rdkit_dof.core import DofDrawSettings, MolsToGridDofImage

try:
    from IPython.display import SVG
except ImportError:
    pass


# ==========================================
# Fixtures
# ==========================================


@pytest.fixture
def molecules_3d():
    mols_smiles = [
        "CCO",
        "COC",
        "c1ccccc1C(F)(F)F",
    ]
    mols_with_hs = []
    for smi in mols_smiles:
        m = Chem.MolFromSmiles(smi)
        if m:
            m_h = Chem.AddHs(m)
            EmbedMolecule(m_h, randomSeed=42)
            mols_with_hs.append(m_h)
    return mols_with_hs


@pytest.fixture
def settings():
    return DofDrawSettings()


# ==========================================
# Integration Tests (No Mocks)
# ==========================================


def test_integration_returns_png_image(molecules_3d):
    """Tests that a grid image is created as a PIL Image."""
    # WHEN
    img = MolsToGridDofImage(molecules_3d, use_svg=False, return_image=True)

    # THEN
    assert img is not None
    assert isinstance(img, Image.Image)
    # Check if the image size is reasonable (not 0x0)
    assert img.width > 0
    assert img.height > 0


@pytest.mark.skipif(SVG is None, reason="IPython is not installed")
def test_integration_returns_svg_image(molecules_3d):
    """Tests that a grid image is created as an SVG object."""
    # WHEN
    svg = MolsToGridDofImage(molecules_3d, use_svg=True, return_image=True)

    # THEN
    assert svg is not None
    assert isinstance(svg, SVG)


def test_integration_returns_png_bytes(molecules_3d):
    """Tests that a grid image is created as PNG bytes."""
    # WHEN
    png_data = MolsToGridDofImage(molecules_3d, use_svg=False, return_image=False)

    # THEN
    assert png_data is not None
    assert isinstance(png_data, bytes)
    assert png_data.startswith(b"\x89PNG\r\n\x1a\n")


def test_integration_returns_svg_str(molecules_3d):
    """Tests that a grid image is created as an SVG string."""
    # WHEN
    svg_text = MolsToGridDofImage(molecules_3d, use_svg=True, return_image=False)

    # THEN
    assert svg_text is not None
    assert isinstance(svg_text, str)
    assert "<svg" in svg_text
    assert svg_text.strip().endswith("</svg>")


def test_integration_handles_empty_list():
    """Tests that an empty list of molecules returns an image without error."""
    # WHEN
    img = MolsToGridDofImage([], use_svg=False, return_image=True)

    # THEN
    assert isinstance(img, Image.Image)


def test_integration_handles_list_with_none():
    """Tests that a list containing None is handled gracefully."""
    # GIVEN
    mols = [Chem.MolFromSmiles("CCO"), None, Chem.MolFromSmiles("CNC")]

    # WHEN
    img = MolsToGridDofImage(mols, use_svg=False, return_image=True)

    # THEN
    assert isinstance(img, Image.Image)
    assert img.width > 0
    assert img.height > 0


def test_integration_highlighting(molecules_3d):
    """
    Tests that MolsToGridDofImage accepts highlighting parameters without error.
    """
    # WHEN
    img = MolsToGridDofImage(
        molecules_3d,
        use_svg=False,
        return_image=True,
        highlightAtomLists=[[0] for _ in molecules_3d],
        highlightBondLists=[[0] for _ in molecules_3d],
        highlightColor=(0, 1, 0, 0.5),
    )

    # THEN
    assert img is not None
    assert isinstance(img, Image.Image)


def test_integration_saves_png_file(molecules_3d, tmp_path):
    """
    Tests that MolsToGridDofImage saves a PNG file when filename is provided.
    """
    # GIVEN
    output_file = tmp_path / "test_grid_output.png"

    # WHEN
    MolsToGridDofImage(molecules_3d, use_svg=False, filename=str(output_file))

    # THEN
    assert output_file.exists()
    assert output_file.stat().st_size > 0
    with open(output_file, "rb") as f:
        header = f.read(8)
        assert header.startswith(b"\x89PNG\r\n\x1a\n")


def test_integration_saves_svg_file(molecules_3d, tmp_path):
    """
    Tests that MolsToGridDofImage saves an SVG file when filename is provided.
    """
    # GIVEN
    output_file = tmp_path / "test_grid_output.svg"

    # WHEN
    MolsToGridDofImage(molecules_3d, use_svg=True, filename=str(output_file))

    # THEN
    assert output_file.exists()
    assert output_file.stat().st_size > 0
    with open(output_file) as f:
        content = f.read()
        assert "<svg" in content
        assert content.strip().endswith("</svg>")


# ==========================================
# Mocked Unit Tests
# ==========================================


@pytest.fixture
def mock_prepare_mol_data(mocker):
    """Mock _prepare_mol_data 并自动清理"""
    return mocker.patch("rdkit_dof.core._prepare_mol_data")


@pytest.fixture
def mock_svg_drawer(mocker):
    """Mock MolDraw2DSVG 并设置默认返回值"""
    mock_cls = mocker.patch("rdkit_dof.core.rdMolDraw2D.MolDraw2DSVG")
    mock_instance = mock_cls.return_value
    mock_instance.GetDrawingText.return_value = "<svg></svg>"
    return mock_instance


@pytest.fixture
def mock_cairo_drawer(mocker):
    """Mock MolDraw2DCairo 并设置默认返回值"""
    mock_cls = mocker.patch("rdkit_dof.core.rdMolDraw2D.MolDraw2DCairo")
    mock_instance = mock_cls.return_value
    # A valid 1x1 black PNG
    png_data = base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="
    )
    mock_instance.GetDrawingText.return_value = png_data
    return mock_instance


def test_mocked_happy_path_svg_return_image(
    molecules_3d, mock_prepare_mol_data, mock_svg_drawer
):
    mock_prepare_mol_data.side_effect = [
        (molecules_3d[0], {}, {}),
        (molecules_3d[1], {}, {}),
        (molecules_3d[2], {}, {}),
    ]

    result = MolsToGridDofImage(molecules_3d, use_svg=True, return_image=True)
    assert isinstance(result, SVG)


def test_mocked_happy_path_svg_return_text(
    molecules_3d, mock_prepare_mol_data, mock_svg_drawer
):
    mock_prepare_mol_data.side_effect = [
        (molecules_3d[0], {}, {}),
        (molecules_3d[1], {}, {}),
        (molecules_3d[2], {}, {}),
    ]

    result = MolsToGridDofImage(molecules_3d, use_svg=True, return_image=False)
    assert result == "<svg></svg>"


def test_mocked_happy_path_png_return_image(
    molecules_3d, mock_prepare_mol_data, mock_cairo_drawer
):
    mock_prepare_mol_data.side_effect = [
        (molecules_3d[0], {}, {}),
        (molecules_3d[1], {}, {}),
        (molecules_3d[2], {}, {}),
    ]

    result = MolsToGridDofImage(molecules_3d, use_svg=False, return_image=True)
    assert isinstance(result, Image.Image)


def test_mocked_happy_path_png_return_bytes(
    molecules_3d, mock_prepare_mol_data, mock_cairo_drawer
):
    mock_prepare_mol_data.side_effect = [
        (molecules_3d[0], {}, {}),
        (molecules_3d[1], {}, {}),
        (molecules_3d[2], {}, {}),
    ]

    result = MolsToGridDofImage(molecules_3d, use_svg=False, return_image=False)
    assert isinstance(result, bytes)
    assert result.startswith(b"\x89PNG")


def test_mocked_mols_with_none(molecules_3d, mock_prepare_mol_data, mock_svg_drawer):
    mock_prepare_mol_data.side_effect = [
        (molecules_3d[0], {}, {}),
        (Chem.Mol(), {}, {}),  # 对应 None
        (molecules_3d[2], {}, {}),
    ]

    input_mols = [molecules_3d[0], None, molecules_3d[2]]
    result = MolsToGridDofImage(input_mols, use_svg=True, return_image=False)

    assert result == "<svg></svg>"
    assert mock_prepare_mol_data.call_count == 3


def test_mocked_invalid_mol_is_handled(
    molecules_3d, mock_prepare_mol_data, mock_svg_drawer
):
    """
    Tests that if _prepare_mol_data fails, it's caught and drawing continues.
    """
    mock_prepare_mol_data.side_effect = [
        (molecules_3d[0], {"atom": "color"}, {"bond": "color"}),
        ValueError("Invalid molecule"),  # This one will fail
        (molecules_3d[2], {"atom": "color"}, {"bond": "color"}),
    ]

    result = MolsToGridDofImage(molecules_3d, use_svg=True, return_image=False)

    assert result == "<svg></svg>"
    # Check that DrawMolecules was still called with 3 molecules
    draw_call_args = mock_svg_drawer.DrawMolecules.call_args[0]
    assert len(draw_call_args[0]) == 3
    # Check that the highlights for the failed molecule are empty
    highlight_atoms_arg = mock_svg_drawer.DrawMolecules.call_args[1]["highlightAtoms"]
    assert highlight_atoms_arg[0]  # First one is ok
    assert not highlight_atoms_arg[1]  # Second one failed, should be empty
    assert highlight_atoms_arg[2]  # Third is ok


def test_mocked_no_svg_support(molecules_3d, mock_prepare_mol_data, mocker):
    mock_prepare_mol_data.return_value = (molecules_3d[0], {}, {})
    mocker.patch("rdkit_dof.core.svg_support", False)

    with pytest.raises(ImportError):
        MolsToGridDofImage([molecules_3d[0]], use_svg=True, return_image=True)
