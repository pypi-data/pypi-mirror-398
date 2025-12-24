"""
Author: TMJ
Date: 2025-12-01 12:45:28
LastEditors: TMJ
LastEditTime: 2025-12-01 14:13:11
Description: 请填写简介
"""

AtomColorMap = dict[int, tuple[float, float, float]]

# Basic RDKit-style color map
DEFAULT_STYLE: AtomColorMap = {
    1: (0.55, 0.55, 0.55),  # H (Gray)
    6: (0.2, 0.2, 0.2),  # C (Dark Gray)
    7: (0.0, 0.0, 1.0),  # N (Blue)
    8: (1.0, 0.0, 0.0),  # O (Red)
    9: (0.2, 0.8, 0.8),  # F
    15: (1.0, 0.5, 0.0),  # P
    16: (0.8, 0.8, 0.0),  # S
    17: (0.0, 0.8, 0.0),  # Cl
    35: (0.5, 0.3, 0.1),  # Br
    53: (0.63, 0.12, 0.94),  # I
}

# Nature-style color map: distinct, with blue and red more modern
NATURE_STYLE: AtomColorMap = {
    1: (0.9, 0.9, 0.9),  # H (Light Gray)
    6: (0.25, 0.25, 0.25),  # C (Dark Gray, not pitch black)
    7: (0.19, 0.51, 0.74),  # N (Nature Blue - slightly lighter)
    8: (0.89, 0.10, 0.11),  # O (Nature Red - less neon)
    9: (0.50, 0.70, 0.90),  # F (Sky Blue)
    15: (1.0, 0.6, 0.0),  # P (Orange)
    16: (0.9, 0.8, 0.2),  # S (Yellow)
    17: (0.1, 0.7, 0.3),  # Cl (Green)
    35: (0.6, 0.2, 0.2),  # Br (Dark Red/Brown)
}

# JACS-style color map: deep, close to print colors, high contrast
JACS_STYLE: AtomColorMap = {
    1: (1.0, 1.0, 1.0),  # H (White)
    6: (0.1, 0.1, 0.1),  # C (Almost Black)
    7: (0.05, 0.20, 0.60),  # N (Navy Blue)
    8: (0.75, 0.05, 0.05),  # O (Crimson Red)
    9: (0.4, 0.8, 0.4),  # F (Pale Green)
    15: (0.8, 0.4, 0.0),  # P (Dark Orange)
    16: (0.8, 0.8, 0.0),  # S (Standard Yellow)
    17: (0.0, 0.5, 0.0),  # Cl (Dark Green)
}

# dark neon-style color map: high contrast, pop with black background
DARK_NEON_STYLE: AtomColorMap = {
    1: (0.8, 0.8, 0.8),  # H (Light Gray)
    6: (0.9, 0.9, 0.9),  # C (White/Light Gray to pop on black)
    7: (0.3, 0.6, 1.0),  # N (Bright Blue)
    8: (1.0, 0.4, 0.4),  # O (Bright Red/Pink)
    9: (0.2, 1.0, 1.0),  # F (Cyan)
    15: (1.0, 0.7, 0.2),  # P (Bright Orange)
    16: (1.0, 1.0, 0.4),  # S (Bright Yellow)
}
