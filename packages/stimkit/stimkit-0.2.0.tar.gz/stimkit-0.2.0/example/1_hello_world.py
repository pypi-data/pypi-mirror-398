"""Example 1: minimal draw pipeline with a centered rectangle and text."""
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


class HelloRenderer(Renderer):
    def draw(self, canvas: Canvas, scene_cfg: DrawConfig):
        # Draw the rectangle as a background
        rect_shape = (scene_cfg.rect_size[0].value_in_unit(canvas), scene_cfg.rect_size[1].value_in_unit(canvas))
        rect_patch = patches.Rectangle(
            xy = (-rect_shape[0]/2, -rect_shape[1]/2),
            width = rect_shape[0],
            height = rect_shape[1],
            transform=canvas.transData, 
            color = 'blue',
            alpha=1.0,
        )
        canvas.add_patch(rect_patch)

        # Draw the text above the rectangle
        canvas.add_text(
            xy=(0, 0),
            text=scene_cfg.text,
            transform=canvas.transData,
            horizontalalignment='center',
            verticalalignment='center',
            fontsize=scene_cfg.font_size,
            color='black'
        )


if __name__ == "__main__":
    renderer = HelloRenderer(CanvasConfig(bg_color='white'))
    renderer.render(
        DrawConfig(
            text="你好世界",
            font_size=24,
            rect_size=(VisualAngle(value=12), VisualAngle(value=5))
        ),
        OutputConfig(file_path=str(REPO_ROOT / "example/output/1_hello_world.svg"))
    )


        
