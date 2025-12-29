"""
Example 4: Implementing a Custom Complex Patch with Pseudo-Boolean Drawing
===========================================================================

This example demonstrates how to create complex shapes (like a notched circle)
using a pseudo-boolean drawing technique. Instead of performing true geometric
boolean operations, we achieve an approximate "difference" effect by drawing
a mask shape filled with the background color on top of the base shape.

This approach is simple and effective for psychological experiment stimulus
images and similar straightforward drawing scenarios where visual correctness
is sufficient and exact geometric precision is not required.
"""

import matplotlib.patches as patches
from pydantic import BaseModel, Field
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).parent.parent.resolve()


from stimkit import Canvas, CanvasConfig, OutputConfig, Renderer, VisualAngle
import matplotlib.transforms as transforms
import matplotlib.patches as patches


class DrawConfig(BaseModel):
    """
    Configuration for drawing a notched circle with a cross line.

    Parameters
    ----------
    radius : VisualAngle
        The radius of the circle in visual degrees.
    notch_side : VisualAngle
        The side length of the square notch in visual degrees.
    angle : float
        The rotation angle of the entire shape in degrees.
    fill_color : str
        The fill color of the circle.
    cross_line_size : VisualAngle
        The size of the cross line in visual degrees.
    """

    radius: VisualAngle = Field(description="The radius of the circle in visual degrees")
    notch_side: VisualAngle = Field(description="The side length of the notch in visual degrees")
    angle: float = Field(description="The angle of the circle in degrees")
    fill_color: str = Field(description="The fill color of the circle")
    cross_line_size: VisualAngle = Field(description="The size of the cross line in visual degrees")


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
        .rotate_deg_around(x=0,y=0,degrees=angle)
        .translate(tx=xy[0], ty=xy[1])
    ) + transform

    circle = patches.Circle(
        xy=(0, 0), 
        radius=radius, 
        color=color,
        transform=shared_transform 
    )

    notch = patches.Rectangle(
        xy=(radius - notch_side, -notch_side / 2),
        width=notch_side,
        height=notch_side,
        angle=0,        # IMPORTANT: set the angle to 0 because all the rotation is done by the shared transform
        color=bg_color, # IMPORTANT: set the notch to backgroud color to make it like a mask, and their should be no stroke
        transform=shared_transform
    )

    return circle, notch

def line(
    xy: tuple[float, float],
    length: float,
    color: str,
    angle: float,
    transform: transforms.Affine2D,
) -> patches.Patch:
    """
    Create a centered line segment.

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

    line1 = line(
        xy=(0, 0),
        length=length,
        color=color,
        angle=0,
        transform=shared_transform,
    )

    line2 = line(
        xy=(0, 0),
        length=length,
        color=color,
        angle=90,
        transform=shared_transform,
    )

    return line1, line2

class HelloRenderer(Renderer):
    """
    Renderer that draws a notched circle with a centered cross line.

    This renderer demonstrates the pseudo-boolean drawing technique
    for creating complex stimulus shapes commonly used in psychological
    experiments.
    """

    def draw(self, canvas: Canvas, scene_cfg: DrawConfig):
        # Calculate dimensions in data units
        radius = scene_cfg.radius.value_in_unit(canvas)
        notch_side = scene_cfg.notch_side.value_in_unit(canvas)
        cross_line_size = scene_cfg.cross_line_size.value_in_unit(canvas)
        
        canvas.add_patches(
            notched_circle(
                xy=(0, 0),
                radius=radius,
                notch_side=notch_side,
                color=scene_cfg.fill_color,
                bg_color=canvas.cfg.bg_color,
                angle=scene_cfg.angle,
                transform=canvas.transData
            )
        )

        canvas.add_patches(
            cross_line(
                xy=(0, 0),
                length=cross_line_size,
                color='black',
                angle=scene_cfg.angle,
                transform=canvas.transData
            )
        )


if __name__ == "__main__":
    renderer = HelloRenderer(CanvasConfig(bg_color='white'))
    renderer.render(
        DrawConfig(
            radius=VisualAngle(value=8),
            notch_side=VisualAngle(value=5),
            angle=0,
            fill_color='red',
            cross_line_size=VisualAngle(value=1.5),
        ),
        OutputConfig(file_path=str(REPO_ROOT / "example/output/4_custom_patch.svg"))
    )


        
