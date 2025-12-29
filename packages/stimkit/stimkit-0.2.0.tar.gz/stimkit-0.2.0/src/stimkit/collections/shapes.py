"""
Factory functions for creating basic geometric shape patches.

This module provides atomic functions for creating common shapes used in
psychological experiment stimuli. Each function returns a matplotlib Patch
object that can be added to a Canvas.

Design principles:
- Each function has a single responsibility (one shape).
- Functions accept explicit geometric parameters (xy, size, color, etc.).
- Supports both filled and outlined (stroke-only) rendering via fill parameter.
- All rotations are in degrees, counter-clockwise from the positive x-axis.
"""

import numpy as np
import matplotlib.patches as mpl_patches
import matplotlib.transforms as transforms
from typing import Literal


__all__ = [
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


def circle(
    xy: tuple[float, float],
    radius: float,
    color: str,
    transform: transforms.Transform,
    *,
    fill: bool = True,
    linewidth: float = 1.0,
) -> mpl_patches.Patch:
    """
    Create a circle patch.

    Parameters
    ----------
    xy : tuple[float, float]
        Center coordinates (x, y).
    radius : float
        Radius of the circle.
    color : str
        Fill color (if fill=True) or edge color (if fill=False).
    transform : Transform
        Matplotlib transform to apply.
    fill : bool, default True
        If True, create a filled circle. If False, create an outlined circle.
    linewidth : float, default 1.0
        Line width for outlined circles (ignored if fill=True).
    """
    if fill:
        return mpl_patches.Circle(xy, radius=radius, color=color, transform=transform)
    return mpl_patches.Circle(
        xy, radius=radius, edgecolor=color, facecolor="none",
        linewidth=linewidth, transform=transform
    )


def square(
    xy: tuple[float, float],
    size: float,
    color: str,
    transform: transforms.Transform,
    *,
    rotation: float = 0.0,
    fill: bool = True,
    linewidth: float = 1.0,
) -> mpl_patches.Patch:
    """
    Create a square patch centered at xy.

    Parameters
    ----------
    xy : tuple[float, float]
        Center coordinates (x, y).
    size : float
        Side length of the square.
    color : str
        Fill color (if fill=True) or edge color (if fill=False).
    transform : Transform
        Matplotlib transform to apply.
    rotation : float, default 0.0
        Rotation angle in degrees (counter-clockwise).
    fill : bool, default True
        If True, create a filled square. If False, create an outlined square.
    linewidth : float, default 1.0
        Line width for outlined squares (ignored if fill=True).
    """
    x, y = xy
    r = size / 2
    if fill:
        return mpl_patches.Rectangle(
            (x - r, y - r), size, size, angle=rotation, color=color, transform=transform
        )
    return mpl_patches.Rectangle(
        (x - r, y - r), size, size, angle=rotation,
        edgecolor=color, facecolor="none", linewidth=linewidth, transform=transform
    )


def triangle(
    xy: tuple[float, float],
    radius: float,
    color: str,
    transform: transforms.Transform,
    *,
    rotation: float = 0.0,
    fill: bool = True,
    linewidth: float = 1.0,
) -> mpl_patches.Patch:
    """
    Create an equilateral triangle patch (circumscribed by a circle of given radius).

    Parameters
    ----------
    xy : tuple[float, float]
        Center coordinates (x, y).
    radius : float
        Circumradius of the triangle.
    color : str
        Fill color (if fill=True) or edge color (if fill=False).
    transform : Transform
        Matplotlib transform to apply.
    rotation : float, default 0.0
        Rotation angle in degrees (counter-clockwise). At 0, one vertex points up.
    fill : bool, default True
        If True, create a filled triangle. If False, create an outlined triangle.
    linewidth : float, default 1.0
        Line width for outlined triangles (ignored if fill=True).
    """
    # matplotlib's orientation is in radians; 0 = vertex to the right, so add 90 for up
    orientation = np.deg2rad(rotation + 90)
    if fill:
        return mpl_patches.RegularPolygon(
            xy, numVertices=3, radius=radius, orientation=orientation,
            color=color, transform=transform
        )
    return mpl_patches.RegularPolygon(
        xy, numVertices=3, radius=radius, orientation=orientation,
        edgecolor=color, facecolor="none", linewidth=linewidth, transform=transform
    )


def diamond(
    xy: tuple[float, float],
    radius: float,
    color: str,
    transform: transforms.Transform,
    *,
    rotation: float = 0.0,
    fill: bool = True,
    linewidth: float = 1.0,
) -> mpl_patches.Patch:
    """
    Create a diamond (rotated square) patch.

    Parameters
    ----------
    xy : tuple[float, float]
        Center coordinates (x, y).
    radius : float
        Circumradius (distance from center to vertex).
    color : str
        Fill color (if fill=True) or edge color (if fill=False).
    transform : Transform
        Matplotlib transform to apply.
    rotation : float, default 0.0
        Additional rotation angle in degrees.
    fill : bool, default True
        If True, create a filled diamond. If False, create an outlined diamond.
    linewidth : float, default 1.0
        Line width for outlined diamonds (ignored if fill=True).
    """
    # Diamond is a 4-sided polygon with vertex pointing up (45 deg offset)
    orientation = np.deg2rad(rotation + 45)
    if fill:
        return mpl_patches.RegularPolygon(
            xy, numVertices=4, radius=radius, orientation=orientation,
            color=color, transform=transform
        )
    return mpl_patches.RegularPolygon(
        xy, numVertices=4, radius=radius, orientation=orientation,
        edgecolor=color, facecolor="none", linewidth=linewidth, transform=transform
    )


def hexagon(
    xy: tuple[float, float],
    radius: float,
    color: str,
    transform: transforms.Transform,
    *,
    rotation: float = 0.0,
    fill: bool = True,
    linewidth: float = 1.0,
) -> mpl_patches.Patch:
    """
    Create a regular hexagon patch.

    Parameters
    ----------
    xy : tuple[float, float]
        Center coordinates (x, y).
    radius : float
        Circumradius (distance from center to vertex).
    color : str
        Fill color (if fill=True) or edge color (if fill=False).
    transform : Transform
        Matplotlib transform to apply.
    rotation : float, default 0.0
        Rotation angle in degrees.
    fill : bool, default True
        If True, create a filled hexagon. If False, create an outlined hexagon.
    linewidth : float, default 1.0
        Line width for outlined hexagons (ignored if fill=True).
    """
    orientation = np.deg2rad(rotation)
    if fill:
        return mpl_patches.RegularPolygon(
            xy, numVertices=6, radius=radius, orientation=orientation,
            color=color, transform=transform
        )
    return mpl_patches.RegularPolygon(
        xy, numVertices=6, radius=radius, orientation=orientation,
        edgecolor=color, facecolor="none", linewidth=linewidth, transform=transform
    )


def star(
    xy: tuple[float, float],
    outer_radius: float,
    color: str,
    transform: transforms.Transform,
    *,
    inner_radius_ratio: float = 0.4,
    num_points: int = 5,
    rotation: float = 0.0,
    fill: bool = True,
    linewidth: float = 1.0,
) -> mpl_patches.Patch:
    """
    Create a star-shaped polygon.

    Parameters
    ----------
    xy : tuple[float, float]
        Center coordinates (x, y).
    outer_radius : float
        Radius of the outer points.
    color : str
        Fill color (if fill=True) or edge color (if fill=False).
    transform : Transform
        Matplotlib transform to apply.
    inner_radius_ratio : float, default 0.4
        Ratio of inner radius to outer radius (controls star "thinness").
    num_points : int, default 5
        Number of star points.
    rotation : float, default 0.0
        Rotation angle in degrees. At 0, one point is at the top.
    fill : bool, default True
        If True, create a filled star. If False, create an outlined star.
    linewidth : float, default 1.0
        Line width for outlined stars (ignored if fill=True).
    """
    x, y = xy
    inner_radius = outer_radius * inner_radius_ratio
    verts = []
    # Start from top (90 degrees) and go counter-clockwise
    start_angle = 90 + rotation
    for i in range(num_points * 2):
        angle = np.deg2rad(start_angle + i * (180 / num_points))
        r = outer_radius if i % 2 == 0 else inner_radius
        verts.append((x + r * np.cos(angle), y + r * np.sin(angle)))

    if fill:
        return mpl_patches.Polygon(verts, closed=True, color=color, transform=transform)
    return mpl_patches.Polygon(
        verts, closed=True, edgecolor=color, facecolor="none",
        linewidth=linewidth, transform=transform
    )


def centered_arrow(
    xy: tuple[float, float],
    length: float,
    color: str,
    transform: transforms.Transform,
    *,
    angle: float = 0.0,
    head_width_ratio: float = 0.4,
    linewidth: float = 1.0,
) -> mpl_patches.Patch:
    """
    Create a centered arrow patch.

    If you need an arrow defined by explicit endpoints, use
    matplotlib.patches.FancyArrowPatch with posA/posB directly.

    Parameters
    ----------
    xy : tuple[float, float]
        Center coordinates (x, y).
    length : float
        Total arrow length.
    color : str
        Arrow color.
    transform : Transform
        Matplotlib transform to apply.
    angle : float, default 0.0
        Rotation angle in degrees (counter-clockwise).
    head_width_ratio : float, default 0.4
        Head size ratio relative to length (controls arrow head scale).
    linewidth : float, default 1.0
        Line width of the arrow shaft.
    """
    angle_rad = np.deg2rad(angle)
    dx = np.cos(angle_rad) * length
    dy = np.sin(angle_rad) * length
    start = (xy[0] - dx / 2, xy[1] - dy / 2)
    end = (xy[0] + dx / 2, xy[1] + dy / 2)
    mutation_scale = max(length * head_width_ratio, linewidth * 4.0, 6.0)
    return mpl_patches.FancyArrowPatch(
        posA=start,
        posB=end,
        arrowstyle="-|>",
        mutation_scale=mutation_scale,
        color=color,
        linewidth=linewidth,
        transform=transform,
    )




def semicircle(
    xy: tuple[float, float],
    radius: float,
    color: str,
    transform: transforms.Transform,
    *,
    orientation: Literal["top", "bottom", "left", "right"] = "top",
    fill: bool = True,
    linewidth: float = 1.0,
) -> mpl_patches.Patch:
    """
    Create a semicircle (half-disc) patch.

    Parameters
    ----------
    xy : tuple[float, float]
        Center coordinates (x, y) of the full circle.
    radius : float
        Radius of the semicircle.
    color : str
        Fill color (if fill=True) or edge color (if fill=False).
    transform : Transform
        Matplotlib transform to apply.
    orientation : {"top", "bottom", "left", "right"}, default "top"
        Direction the curved part faces.
    fill : bool, default True
        If True, create a filled semicircle. If False, create an outlined semicircle.
    linewidth : float, default 1.0
        Line width for outlined semicircles (ignored if fill=True).
    """
    angle_map = {"top": (0, 180), "bottom": (180, 360), "left": (90, 270), "right": (270, 90)}
    theta1, theta2 = angle_map[orientation]
    if fill:
        return mpl_patches.Wedge(xy, radius, theta1, theta2, color=color, transform=transform)
    return mpl_patches.Wedge(
        xy, radius, theta1, theta2,
        edgecolor=color, facecolor="none", linewidth=linewidth, transform=transform
    )


def ring(
    xy: tuple[float, float],
    outer_radius: float,
    inner_radius: float,
    color: str,
    transform: transforms.Transform,
    *,
    fill: bool = True,
    linewidth: float = 1.0,
) -> mpl_patches.Patch:
    """
    Create a ring (annulus) patch.

    Parameters
    ----------
    xy : tuple[float, float]
        Center coordinates (x, y).
    outer_radius : float
        Outer radius of the ring.
    inner_radius : float
        Inner radius of the ring (the "hole").
    color : str
        Fill color (if fill=True) or edge color (if fill=False).
    transform : Transform
        Matplotlib transform to apply.
    fill : bool, default True
        If True, create a filled ring. If False, create an outlined ring.
    linewidth : float, default 1.0
        Line width for outlined rings (ignored if fill=True).
    """
    # Use Wedge with width parameter for annulus effect
    width = outer_radius - inner_radius
    if fill:
        return mpl_patches.Annulus(xy, outer_radius, width, color=color, transform=transform)
    return mpl_patches.Annulus(
        xy, outer_radius, width,
        edgecolor=color, facecolor="none", linewidth=linewidth, transform=transform
    )
