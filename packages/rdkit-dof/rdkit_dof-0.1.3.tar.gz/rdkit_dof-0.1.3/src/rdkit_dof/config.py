"""
Author: TMJ
Date: 2025-12-01 12:38:03
LastEditors: TMJ
LastEditTime: 2025-12-02 11:12:43
Description: 请填写简介
"""

from typing import Literal, Union

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from rdkit.Chem import Mol, RWMol
from typing_extensions import Self

from .palettes import DARK_NEON_STYLE, DEFAULT_STYLE, JACS_STYLE, NATURE_STYLE

StyleName = Literal["default", "nature", "jacs", "dark"]


class DofDrawSettings(BaseSettings):
    """
    Logic:
    1. load preset style
    2. if dark mode, and fog color is default, set fog color to (0.1, 0.1, 0.1)
    3. override specific atoms with user-provided atom_colors
    """

    preset_style: StyleName = "default"

    fog_color: tuple[float, float, float] = (0.95, 0.95, 0.95)
    min_alpha: float = 0.4
    default_size: tuple[int, int] = (800, 800)

    enable_ipython: bool = True

    atom_colors: dict[int, tuple[float, float, float]] = Field(default_factory=dict)

    model_config = SettingsConfigDict(
        env_file=".env", env_prefix="RDKIT_DOF_", extra="ignore"
    )

    @model_validator(mode="after")
    def _init_merge_configuration(self) -> Self:
        self._apply_style_logic(self.preset_style)
        return self

    def _apply_style_logic(self, style: str):
        style_map = {
            "default": DEFAULT_STYLE,
            "nature": NATURE_STYLE,
            "jacs": JACS_STYLE,
            "dark": DARK_NEON_STYLE,
        }
        # If preset_style is specified, use it; otherwise, use default
        base_colors = style_map.get(style, DEFAULT_STYLE).copy()

        if self.preset_style == "dark":
            if self.fog_color == (0.95, 0.95, 0.95):
                self.fog_color = (0.1, 0.1, 0.1)

        if self.atom_colors:
            base_colors.update(self.atom_colors)

        self.atom_colors = base_colors

    def get_atom_color(self, atomic_num: int) -> tuple[float, float, float]:
        return self.atom_colors.get(
            atomic_num, self.atom_colors.get(6, (0.2, 0.2, 0.2))
        )

    def use_style(self, style: StyleName):
        """
        Switch to a different preset style, resetting any custom atom colors.
        """
        self.preset_style = style
        self.atom_colors = {}
        self._apply_style_logic(style)

    def enable_ipython_integration(self, enable: bool = True):
        """
        Toggle whether to use the DOF effect drawer as the default renderer
        for RDKit Mol objects in Jupyter/IPython.

        Args:
            enable (bool): True to enable DOF rendering, False to restore RDKit default.
        """
        try:
            from IPython.core.getipython import get_ipython
        except ImportError:
            return
        ip = get_ipython()
        if ip is None:
            return
        svg_formatter = ip.display_formatter.formatters["image/svg+xml"]  # type: ignore

        if enable:
            from .core import MolToDofImage

            def _dof_drawer_hook(mol: Union[Mol, RWMol]) -> str:
                return MolToDofImage(
                    mol,
                    use_svg=True,
                    return_image=False,  # 必须为 False，返回 SVG 源码字符串
                    settings=self,  # 绑定当前配置实例
                )

            svg_formatter.for_type(Mol, _dof_drawer_hook)
            svg_formatter.for_type(RWMol, _dof_drawer_hook)
        else:
            if Mol in svg_formatter.type_printers:
                svg_formatter.type_printers.pop(Mol)
            if RWMol in svg_formatter.type_printers:
                svg_formatter.type_printers.pop(RWMol)


dofconfig = DofDrawSettings()
if dofconfig.enable_ipython:
    dofconfig.enable_ipython_integration(True)
