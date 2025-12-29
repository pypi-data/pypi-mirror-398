"""Example 2: per-element rotation and translation without using matplotlib transform."""
import matplotlib.patches as patches
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

class HelloRenderer(Renderer):
    def draw(self, canvas: Canvas, scene_cfg: DrawConfig):
        # Convert visual angle to matplotlib data coordinates
        rect_shape = (scene_cfg.rect_size[0].value_in_unit(canvas), scene_cfg.rect_size[1].value_in_unit(canvas))
        xy_shift = (scene_cfg.xy_shift[0].value_in_unit(canvas), scene_cfg.xy_shift[1].value_in_unit(canvas))

        # Draw the rectangle as a background
        rect_patch = patches.Rectangle(
            # IMPORTANT: directly calculate the final position of the rectangle after shift
            xy = (-rect_shape[0]/2 + xy_shift[0], -rect_shape[1]/2 + xy_shift[1]),
            width = rect_shape[0],
            height = rect_shape[1],
            transform=canvas.transData,
            # IMPORTANT: set the rotation point to the center of the rectangle
            rotation_point="center",
            # IMPORTANT: for patches, the angle is the rotation angle around the rotation point
            angle=scene_cfg.rotation,
            color = 'blue',
            alpha=1.0,
        )

        canvas.add_patch(rect_patch)
        # Draw the text above the rectangle
        canvas.add_text(
            # IMPORTANT: directly calculate the final position of the text after shift
            xy=(xy_shift[0], xy_shift[1]),
            # IMPORTANT: for texts, the angle is the rotation angle around the rotation point
            rotation=scene_cfg.rotation,
            transform=canvas.transData,
            text=scene_cfg.text,
            # IMPORTANT: The roation anchor of the text is defined by horizontalalignment and verticalalignment
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
        ),
        OutputConfig(file_path=str(REPO_ROOT / "example/output/2_rotate_shift.svg"))
    )


        
