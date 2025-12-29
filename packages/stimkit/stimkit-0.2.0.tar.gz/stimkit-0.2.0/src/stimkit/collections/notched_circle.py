"""
Factory function for creating a notched circle patch.

This module provides the `notched_circle` function which creates a filled
circle with a square notch removed from its edge using pseudo-boolean drawing.
"""

import matplotlib.patches as patches
import matplotlib.transforms as transforms


def notched_circle(
    xy: tuple[float, float],
    radius: float,
    notch_side: float,
    color: str,
    bg_color: str,
    angle: float,
    transform: transforms.Affine2D,
) -> tuple[patches.Patch, patches.Patch]:
    """
    Create a notched circle using pseudo-boolean drawing.

    This function creates a filled circle with a square notch removed from
    its edge. At angle=0, the square notch is positioned on the right side
    of the circle, with its left edge tangent to the circumference and
    vertically centered. Positive angle values rotate the entire shape
    counter-clockwise around the circle's center.

    The notch effect is achieved by drawing a background-colored rectangle
    on top of the circle, simulating a boolean difference operation. This
    pseudo-boolean approach works well for simple stimulus generation in
    psychological experiments.

    Parameters
    ----------
    xy : tuple[float, float]
        The center coordinates (x, y) of the circle.
    radius : float
        The radius of the circle.
    notch_side : float
        The side length of the square notch. The notch is vertically
        centered on the circle's edge.
    color : str
        The fill color of the circle.
    bg_color : str
        The background color used to fill the notch (mask). Should match
        the canvas background for the pseudo-boolean effect to work.
    angle : float
        The rotation angle in degrees (counter-clockwise). At 0 degrees,
        the notch faces right; at 90 degrees, it faces up.
    transform : matplotlib.transforms.Affine2D
        The base transform to apply (typically canvas.transData).

    Returns
    -------
    tuple[patches.Patch, patches.Patch]
        A tuple containing (circle, notch) patches. The notch patch is
        filled with bg_color to create the visual "cut-out" effect.
        Both patches must be added to the canvas in order.
    """
    shared_transform = (
        transforms.Affine2D()
        .rotate_deg_around(x=0, y=0, degrees=angle)
        .translate(tx=xy[0], ty=xy[1])
    ) + transform

    circle = patches.Circle(
        xy=(0, 0),
        radius=radius,
        color=color,
        transform=shared_transform,
    )

    notch = patches.Rectangle(
        xy=(radius - notch_side, -notch_side / 2),
        width=notch_side,
        height=notch_side,
        angle=0,  # IMPORTANT: set the angle to 0 because all the rotation is done by the shared transform
        color=bg_color,  # IMPORTANT: set the notch to backgroud color to make it like a mask, and their should be no stroke
        transform=shared_transform,
    )

    return circle, notch
