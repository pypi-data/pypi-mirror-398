"""
Collections of reusable patch factory functions.

This module provides factory functions for creating common shapes used
in psychological experiment stimuli.
"""

from .notched_circle import notched_circle
from .lines import centered_line, cross_line
from .shapes import (
    circle,
    square,
    triangle,
    diamond,
    hexagon,
    star,
    centered_arrow,
    semicircle,
    ring,
)

__all__ = [
    "notched_circle",
    "centered_line",
    "cross_line",
    "circle",
    "square",
    "triangle",
    "diamond",
    "hexagon",
    "star",
    "centered_arrow",
    "semicircle",
    "ring",
]
