"""
Example 5: Rendering a Batch of Stimuli via a Data Pipeline
==========================================================

This example demonstrates how to set up a rendering pipeline that processes
multiple trials or scenes from a structured data source (e.g., a CSV file).
It utilizes a custom Renderer to interpret each row of data and generate
corresponding stimulus images.
"""


import matplotlib.patches as patches
from pydantic import BaseModel, Field
from pathlib import Path
import sys
import pandas as pd

REPO_ROOT = Path(__file__).parent.parent.resolve()


from stimkit import Canvas, CanvasConfig, OutputConfig, Renderer, VisualAngle
from stimkit.collections import notched_circle

class SceneConfig(BaseModel):
    """
    Configuration for a single scene containing two notched circles.

    Parameters
    ----------
    notch1_color : str
        Color of the first (upper) notched circle.
    notch2_color : str
        Color of the second (lower) notched circle.
    radius : VisualAngle
        The radius of both notched circles in visual degrees.
    notch_side : VisualAngle
        The side length of the square notch for both circles in visual degrees.
    face2face : bool
        If True, the two notches face each other (upper notch faces down, 
        lower notch faces up). If False, both notches follow their default 
        orientations.
    """

    notch1_color: str = Field(description="Color of the first notch")
    notch2_color: str = Field(description="Color of the second notch")
    radius: VisualAngle = Field(description="Radius of the notched circle")
    notch_side: VisualAngle = Field(description="Side length of the square notch")
    face2face: bool = Field(description="Whether the two notches face each other")


class NotchRenderer(Renderer):
    """
    Renderer for vertically aligned notched circles.

    This renderer places two notched circles on the canvas, one above the other,
    with colors and orientations determined by the SceneConfig.
    """

    def draw(self, canvas: Canvas, config: SceneConfig) -> list[patches.Patch]:
        """
        Draw the notched circles onto the canvas.

        Parameters
        ----------
        canvas : Canvas
            The canvas object to draw on.
        config : SceneConfig
            The configuration for the scene to be rendered.

        Returns
        -------
        list[patches.Patch]
            The list of patches added to the canvas.
        """
        radius = config.radius.value_in_unit(canvas)
        notch_side = config.notch_side.value_in_unit(canvas)
        
        upper_angle = -90
        lower_angle = 90 if config.face2face else 0

        # Draw the upper notch
        canvas.add_patches(
            notched_circle(
                xy=(0, radius*1.1),
                radius=radius,
                notch_side=notch_side,
                color=config.notch1_color,
                bg_color=canvas.cfg.bg_color,
                angle=upper_angle,
                transform=canvas.transData,
            )
        )

        # Draw the lower notch
        canvas.add_patches(
            notched_circle(
                xy=(0, -radius*1.1),
                radius=radius,
                notch_side=notch_side,
                color=config.notch2_color,
                bg_color=canvas.cfg.bg_color,
                angle=lower_angle,
                transform=canvas.transData,
            )
        )


def main_pipeline(data: pd.DataFrame, output_dir: Path):
    """
    Iterate through data rows and render each scene.

    This function sets up the renderer and loops through each row of the 
    provided DataFrame. Each row is converted to a SceneConfig and rendered 
    to a separate file in the specified output directory.

    Parameters
    ----------
    data : pd.DataFrame
        DataFrame containing the configuration for each scene. Each row 
        must include an 'id' column and fields corresponding to SceneConfig.
    output_dir : Path
        Directory where the rendered SVG files will be saved.
    """
    renderer = NotchRenderer(CanvasConfig(bg_color='white'))
    for index, row in data.iterrows():
        config = row.to_dict()
        data_id = config.pop('id')
        renderer.render(
            SceneConfig(**config),
            OutputConfig(file_path=str(output_dir / f"{data_id}.svg"))
        )


        
if __name__ == "__main__":
    data_path = REPO_ROOT / "example/5_pipeline_data.csv"
    output_dir = REPO_ROOT / "example/output/5_pipeline"
    output_dir.mkdir(parents=True, exist_ok=True)

    data = pd.read_csv(data_path)
    main_pipeline(data, output_dir)
