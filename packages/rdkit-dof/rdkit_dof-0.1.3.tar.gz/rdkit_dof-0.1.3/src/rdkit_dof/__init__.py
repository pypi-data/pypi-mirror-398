"""
Author: TMJ
Date: 2025-12-01 12:37:38
LastEditors: TMJ
LastEditTime: 2025-12-21 21:15:57
Description: 请填写简介
"""

import importlib.metadata

from .config import DofDrawSettings, dofconfig
from .core import MolsToGridDofImage, MolToDofImage

try:
    __version__ = importlib.metadata.version("myrepositorytemplate")
except importlib.metadata.PackageNotFoundError:
    __version__ = "unknown"

__all__ = ["MolsToGridDofImage", "MolToDofImage", "DofDrawSettings", "dofconfig"]
