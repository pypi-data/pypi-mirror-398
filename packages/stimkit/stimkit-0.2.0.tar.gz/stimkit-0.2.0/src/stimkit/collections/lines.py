"""
Factory functions for creating line patches.

This module provides functions for creating centered line segments and
cross (plus sign) shapes composed of perpendicular lines.
"""

import matplotlib.patches as patches
import matplotlib.transforms as transforms


def centered_line(
    xy: tuple[float, float],
    length: float,
    color: str,
    angle: float,
    transform: transforms.Affine2D,
    linewidth: float = 1.0,
) -> patches.Patch:
    """
    Create a centered line segment.

    If you need a line defined by explicit endpoints, use matplotlib.patches.FancyArrowPatch
    with posA/posB directly.

    Parameters
    ----------
    xy : tuple[float, float]
        The center coordinates (x, y) of the line.
    length : float
        The total length of the line.
    color : str
        The color of the line.
    angle : float
        The rotation angle in degrees.
    transform : matplotlib.transforms.Affine2D
        The base transform to apply.
    linewidth : float, optional
        The width of the line (default is 1.0).

    Returns
    -------
    patches.Patch
        A FancyArrowPatch representing the line.
    """
    return patches.FancyArrowPatch(
        posA=(-length / 2, 0),
        posB=(length / 2, 0),
        arrowstyle="-",
        color=color,
        linewidth=linewidth,
        transform=(
            transforms.Affine2D()
            .rotate_deg_around(x=0, y=0, degrees=angle)
            .translate(tx=xy[0], ty=xy[1])
            + transform
        ),
    )


def cross_line(
    xy: tuple[float, float],
    length: float,
    color: str,
    angle: float,
    transform: transforms.Affine2D,
    linewidth: float = 1.0,
) -> tuple[patches.Patch, patches.Patch]:
    """
    Create a cross (plus sign) composed of two perpendicular lines.

    Parameters
    ----------
    xy : tuple[float, float]
        The center coordinates (x, y) of the cross.
    length : float
        The length of each line in the cross.
    color : str
        The color of the cross.
    angle : float
        The rotation angle in degrees.
    transform : matplotlib.transforms.Affine2D
        The base transform to apply.
    linewidth : float, optional
        The width of the lines (default is 1.0).

    Returns
    -------
    tuple[patches.Patch, patches.Patch]
        A tuple containing the horizontal and vertical line patches.
    """
    shared_transform = (
        transforms.Affine2D()
        .rotate_deg_around(x=0, y=0, degrees=angle)
        .translate(tx=xy[0], ty=xy[1])
    ) + transform

    line1 = centered_line(
        xy=(0, 0),
        length=length,
        color=color,
        angle=0,
        transform=shared_transform,
        linewidth=linewidth,
    )

    line2 = centered_line(
        xy=(0, 0),
        length=length,
        color=color,
        angle=90,
        transform=shared_transform,
        linewidth=linewidth,
    )

    return line1, line2
