"""
Layout utilities for generating geometric coordinate positions.

This module provides stateless, pure functions for calculating positions
in common layouts used in psychological experiments. Functions are independent
of Canvas, VisualAngle, or any configuration objects.

Design principles:
- Only geometry: no experiment logic, no unit conversion, no collision detection.
- Input/output units are caller's responsibility.
- Reproducible: if randomness is needed, pass an explicit `rng`.
- Functional API: no classes, just pure functions.
"""

import numpy as np
from numpy.typing import ArrayLike
from typing import Literal


__all__ = [
    "circular_positions",
    "radial_positions",
    "grid_positions",
    "diamond_positions",
    "rotate_points",
    "shuffle_positions",
]


def circular_positions(
    count: int,
    radius: float,
    *,
    start_deg: float = 0.0,
    center: tuple[float, float] = (0.0, 0.0),
    clockwise: bool = False,
) -> list[tuple[float, float]]:
    """
    Generate positions evenly distributed on a circle.

    Parameters
    ----------
    count : int
        Number of positions to generate.
    radius : float
        Radius of the circle.
    start_deg : float, default 0.0
        Starting angle in degrees (0 = East/right, 90 = North/up).
    center : tuple[float, float], default (0.0, 0.0)
        Center of the circle.
    clockwise : bool, default False
        If True, positions are generated clockwise. Otherwise counter-clockwise.

    Returns
    -------
    list[tuple[float, float]]
        List of (x, y) coordinates.
    """
    if count <= 0:
        return []

    cx, cy = center
    direction = -1 if clockwise else 1
    angles = np.deg2rad(start_deg + direction * np.linspace(0, 360, count, endpoint=False))

    return [(cx + radius * np.cos(a), cy + radius * np.sin(a)) for a in angles]


def radial_positions(
    angles_deg: ArrayLike,
    radius: float,
    *,
    center: tuple[float, float] = (0.0, 0.0),
) -> list[tuple[float, float]]:
    """
    Generate positions at specified angles on a circle.

    Parameters
    ----------
    angles_deg : array-like
        Angles in degrees (0 = East/right, 90 = North/up).
    radius : float
        Radius of the circle.
    center : tuple[float, float], default (0.0, 0.0)
        Center of the circle.

    Returns
    -------
    list[tuple[float, float]]
        List of (x, y) coordinates.
    """
    cx, cy = center
    angles = np.deg2rad(np.asarray(angles_deg))
    return [(cx + radius * np.cos(a), cy + radius * np.sin(a)) for a in angles]


def grid_positions(
    rows: int,
    cols: int,
    spacing: float | tuple[float, float],
    *,
    center: tuple[float, float] = (0.0, 0.0),
    order: Literal["row-major", "col-major"] = "row-major",
) -> list[tuple[float, float]]:
    """
    Generate positions in a regular grid.

    Parameters
    ----------
    rows : int
        Number of rows.
    cols : int
        Number of columns.
    spacing : float or tuple[float, float]
        Spacing between items. If a single float, use same spacing for x and y.
        If a tuple, (x_spacing, y_spacing).
    center : tuple[float, float], default (0.0, 0.0)
        Center of the grid.
    order : {"row-major", "col-major"}, default "row-major"
        Order of traversal. "row-major" fills rows first (left-to-right, top-to-bottom).

    Returns
    -------
    list[tuple[float, float]]
        List of (x, y) coordinates, starting from top-left.
    """
    if rows <= 0 or cols <= 0:
        return []

    if isinstance(spacing, (int, float)):
        sx, sy = spacing, spacing
    else:
        sx, sy = spacing

    cx, cy = center
    # Calculate offsets to center the grid
    x_offset = (cols - 1) * sx / 2
    y_offset = (rows - 1) * sy / 2

    positions = []
    if order == "row-major":
        for r in range(rows):
            for c in range(cols):
                x = cx - x_offset + c * sx
                y = cy + y_offset - r * sy  # y decreases as row increases (top to bottom)
                positions.append((x, y))
    else:  # col-major
        for c in range(cols):
            for r in range(rows):
                x = cx - x_offset + c * sx
                y = cy + y_offset - r * sy
                positions.append((x, y))

    return positions


def diamond_positions(
    eccentricity: float,
    *,
    center: tuple[float, float] = (0.0, 0.0),
) -> list[tuple[float, float]]:
    """
    Generate 4 positions in a diamond pattern (top, right, bottom, left).

    Parameters
    ----------
    eccentricity : float
        Distance from center to each position.
    center : tuple[float, float], default (0.0, 0.0)
        Center of the diamond.

    Returns
    -------
    list[tuple[float, float]]
        List of 4 (x, y) coordinates: [top, right, bottom, left].
    """
    cx, cy = center
    return [
        (cx, cy + eccentricity),   # top
        (cx + eccentricity, cy),   # right
        (cx, cy - eccentricity),   # bottom
        (cx - eccentricity, cy),   # left
    ]


def rotate_points(
    points: list[tuple[float, float]],
    angle_deg: float,
    *,
    center: tuple[float, float] = (0.0, 0.0),
) -> list[tuple[float, float]]:
    """
    Rotate a list of points around a center.

    Parameters
    ----------
    points : list[tuple[float, float]]
        Points to rotate.
    angle_deg : float
        Rotation angle in degrees (counter-clockwise).
    center : tuple[float, float], default (0.0, 0.0)
        Center of rotation.

    Returns
    -------
    list[tuple[float, float]]
        Rotated points.
    """
    if not points:
        return []

    cx, cy = center
    angle_rad = np.deg2rad(angle_deg)
    cos_a, sin_a = np.cos(angle_rad), np.sin(angle_rad)

    result = []
    for x, y in points:
        dx, dy = x - cx, y - cy
        new_x = cx + dx * cos_a - dy * sin_a
        new_y = cy + dx * sin_a + dy * cos_a
        result.append((new_x, new_y))

    return result


def shuffle_positions(
    points: list[tuple[float, float]],
    *,
    rng: np.random.Generator | None = None,
) -> list[tuple[float, float]]:
    """
    Shuffle a list of positions.

    Parameters
    ----------
    points : list[tuple[float, float]]
        Points to shuffle.
    rng : numpy.random.Generator or None, default None
        Random number generator. If None, uses numpy's default RNG.

    Returns
    -------
    list[tuple[float, float]]
        Shuffled points (new list, original is unchanged).
    """
    if rng is None:
        rng = np.random.default_rng()

    result = list(points)
    rng.shuffle(result)
    return result
