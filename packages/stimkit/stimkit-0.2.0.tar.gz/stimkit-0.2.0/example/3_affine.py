"""Example 3: shared affine transform for consistent rotation and shift or more complex transformations like scale."""
import matplotlib.patches as patches
import matplotlib.transforms as transforms
from pydantic import BaseModel, Field
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).parent.parent.resolve()


from stimkit import Canvas, CanvasConfig, OutputConfig, Renderer, VisualAngle


class DrawConfig(BaseModel):
    text: str = Field(description="The text to show in the middle of the screen")
    font_size: int = Field(default=14, description="The font size in points")
    rect_size: tuple[VisualAngle, VisualAngle] = Field(description="The size of the rectangle in visual degrees")
    # IMPORTANT: add `rotation` to the config to define the rotation angle of the text and rectangle
    rotation: float = Field(default=0, description="The rotation angle in degrees")
    xy_shift: tuple[VisualAngle, VisualAngle] = Field(description="The shift in visual degrees")
    scale_factor: float = Field(default=1, description="The scale factor")

class HelloRenderer(Renderer):
    def draw(self, canvas: Canvas, scene_cfg: DrawConfig):
        # Convert visual angle to matplotlib data coordinates
        rect_shape = (scene_cfg.rect_size[0].value_in_unit(canvas), scene_cfg.rect_size[1].value_in_unit(canvas))
        xy_shift = (scene_cfg.xy_shift[0].value_in_unit(canvas), scene_cfg.xy_shift[1].value_in_unit(canvas))

        # Create the shared transform, 1st rotate, then translate, then apply the canvas transform
        shared_transform = (
            transforms.Affine2D()
                .rotate_deg_around(x=0, y=0, degrees=scene_cfg.rotation)
                .translate(xy_shift[0], xy_shift[1])
                .scale(scene_cfg.scale_factor)
            + canvas.transData
        )

        # Draw the rectangle as a background
        rect_patch = patches.Rectangle(
            xy = (-rect_shape[0]/2, -rect_shape[1]/2),
            width = rect_shape[0],
            height = rect_shape[1],
            transform=shared_transform,
            color = 'blue',
            alpha=1.0,
        )

        canvas.add_patch(rect_patch)
        # Draw the text above the rectangle
        canvas.add_text(
            xy=(0, 0),
            transform=shared_transform,
            transform_rotates_text=True, # IMPORTANT: set this to True or the text will not be rotated
            text=scene_cfg.text,
            horizontalalignment='center',
            verticalalignment='center',
            fontsize=scene_cfg.font_size,
            color='black'
        )


if __name__ == "__main__":
    renderer = HelloRenderer(CanvasConfig(bg_color='white'))
    renderer.render(
        DrawConfig(
            text="Hello World",
            font_size=12,
            rect_size=(VisualAngle(value=12), VisualAngle(value=5)),
            rotation=30,
            xy_shift=(VisualAngle(value=-5), VisualAngle(value=5)),
            scale_factor=1.5
        ),
        OutputConfig(file_path=str(REPO_ROOT / "example/output/3_affine.svg"))
    )


        
