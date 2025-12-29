from importlib import resources
from pydantic import BaseModel, Field, model_validator
from loguru import logger
from typing import Iterable, Any
import math 
import matplotlib.pyplot as plt
import matplotlib.transforms as transforms
import matplotlib.patches as patches 
from matplotlib.font_manager import FontProperties
from matplotlib.collections import PatchCollection

_FONT_RESOURCE = resources.files(__package__).joinpath("resources", "NotoSansSC-Regular.ttf")

class VisualAngle(BaseModel):
    """Represents a visual angle in degrees."""
    value: float = Field(..., description="Visual angle in degrees")

    @model_validator(mode='before')
    @classmethod
    def wrap_numeric(cls, data: Any) -> Any:
        """Allow initializing from a raw float/int."""
        if isinstance(data, (int, float)):
            return {"value": float(data)}
        return data

    def value_in_unit(self, canvas: 'Canvas') -> float:
        """
        Calculates the length in matplotlib data coordinates for a given visual angle.
        This assumes the matplotlib data coordinate have the same height/width ratio as the screen.

        Args:
            canvas: The canvas to calculate the length for
        
        Returns:
            float: The equivalent length in matplotlib data coordinates
        """
        return canvas.cfg._visual_angle_to_unit(self.value)

    def value_in_points(self, canvas: 'Canvas', *, min_points: float = 0.0) -> float:
        """
        Converts the visual angle into Matplotlib points (pt), which are commonly used for line widths and font sizes.

        Args:
            canvas: The canvas defining the coordinate system.
            min_points: Optional floor value applied after conversion.

        Returns:
            float: Length in points (1 pt = 1/72 inch) suitable for Matplotlib styling APIs.
        """
        points = self.value_in_unit(canvas) * 72.0
        return max(points, min_points) if min_points else points


class Pixel(BaseModel):
    """Represents a length in pixels.
    
    Used when experiment parameters are specified in pixel units rather than
    visual angles. Converts to canvas data coordinates using the screen DPI.
    """
    value: float = Field(..., description="Length in pixels")

    @model_validator(mode='before')
    @classmethod
    def wrap_numeric(cls, data: Any) -> Any:
        """Allow initializing from a raw float/int."""
        if isinstance(data, (int, float)):
            return {"value": float(data)}
        return data

    def value_in_unit(self, canvas: 'Canvas') -> float:
        """
        Convert pixel length to matplotlib data coordinates.

        Args:
            canvas: The canvas to calculate the length for
        
        Returns:
            float: The equivalent length in matplotlib data coordinates
        """
        # pixels / dpi = inches
        # inches * (canvas_width / screen_width_inches) = data units
        # Simplified: pixels / dpi * (width / (width)) = pixels / dpi
        # Since canvas width = screen width in inches, and dpi converts to data:
        return self.value / canvas.cfg.dpi

    def value_in_points(self, canvas: 'Canvas', *, min_points: float = 0.0) -> float:
        """
        Converts the stored pixel length into Matplotlib points (pt) for line widths or glyph sizes.

        Args:
            canvas: The canvas defining the coordinate system.
            min_points: Optional floor value applied after conversion.

        Returns:
            float: Length in points (1 pt = 1/72 inch) suitable for Matplotlib styling.
        """
        points = (self.value / canvas.cfg.dpi) * 72.0
        return max(points, min_points) if min_points else points

class CanvasConfig(BaseModel):
    """Configuration for the drawing environment (Canvas).
    
    The canvas dimensions are automatically computed from screen_size and 
    screen_resolution to ensure the correct aspect ratio. The x lim of the 
    canvas is [-width/2, width/2] and the y lim is [-height/2, height/2].

    Attributes:
        bg_color: Background face color.
        screen_distance: Viewing distance from screen in cm.
        screen_size: Screen diagonal size in inches.
        screen_resolution: Screen resolution as (width_px, height_px).
        
    Properties:
        width: Canvas width in matplotlib data coordinates (computed).
        height: Canvas height in matplotlib data coordinates (computed).
    """
    bg_color: str = Field('white', description="Background face color")
    screen_distance: float = Field(50, description="Screen distance in cm")
    screen_size: float = Field(17, description="Screen size in inches")
    screen_resolution: tuple[int, int] = Field((1024, 768), description="Screen resolution")

    def model_post_init(self, __context):
        assert self.screen_distance > 0, "Screen distance must be greater than 0"
        assert self.screen_size > 0, "Screen size must be greater than 0"
        assert self.screen_resolution[0] > 0, "Screen resolution width must be greater than 0"
        assert self.screen_resolution[1] > 0, "Screen resolution height must be greater than 0"

    @property
    def width(self) -> float:
        """Canvas width in matplotlib data coordinates.
        
        Computed from screen_size and screen_resolution to match physical
        screen width while maintaining the correct aspect ratio.
        """
        w_px, h_px = self.screen_resolution
        aspect_ratio = w_px / h_px
        # width = screen_size / sqrt(1 + 1/aspect^2) (screen diagonal geometry)
        return self.screen_size / math.sqrt(1 + (1 / aspect_ratio) ** 2)

    @property
    def height(self) -> float:
        """Canvas height in matplotlib data coordinates.
        
        Computed from width and screen_resolution to maintain the correct
        aspect ratio.
        """
        w_px, h_px = self.screen_resolution
        return self.width * h_px / w_px

    @property
    def dpi(self) -> float:
        """
        Returns the DPI for rendering the canvas at screen_resolution.
        
        This ensures that when the figure is saved with this DPI, the output 
        image will have exactly screen_resolution[0] × screen_resolution[1] pixels.
        
        Returns
        -------
        float
            The DPI calculated as screen_resolution_width / canvas_width
        """
        return self.screen_resolution[0] / self.width

    def _visual_angle_to_unit(self, visual_angle: float) -> float:
        """
        Calculates the length in matplotlib data coordinates for a given visual angle.
        
        This method converts a visual angle (in degrees) to the corresponding length
        in matplotlib data coordinates, taking into account the viewing distance 
        and the physical screen properties.

        Args:
            visual_angle: The visual angle in degrees.
        
        Returns:
            float: The equivalent length in matplotlib data coordinates.
        """
        # 1. Calculate physical size on screen (in inches)
        distance_inches = self.screen_distance / 2.54
        angle_radians = math.radians(visual_angle)
        size_inches = 2 * distance_inches * math.tan(angle_radians / 2)
        
        # 2. Calculate physical screen width (in inches) from diagonal size.
        #    We assume the screen pixels are square, so the physical aspect ratio 
        #    matches the resolution aspect ratio.
        w_px, h_px = self.screen_resolution
        aspect_ratio = w_px / h_px
        
        # diagonal^2 = width^2 + height^2 = width^2 + (width/aspect)^2
        # screen_size^2 = width^2 * (1 + 1/aspect^2)
        # width = screen_size / sqrt(1 + 1/aspect^2)
        screen_width_inches = self.screen_size / math.sqrt(1 + (1 / aspect_ratio)**2)
        
        # 3. Convert physical size to data coordinates.
        #    The canvas width (self.width) corresponds to the full screen width
        #    (since dpi is calculated to match screen resolution width).
        #    So: data_units / physical_inches = self.width / screen_width_inches
        data_units_per_inch = self.width / screen_width_inches
        
        return size_inches * data_units_per_inch

    

class OutputConfig(BaseModel):
    """Configuration for output settings.

    Attributes:
        file_path: Destination file path for the rendered canvas.
    """
    file_path: str = Field(..., description="Destination file path")


class Canvas:
    """
    A reusable canvas manager designed as a Context Manager.
    """
    def __init__(self, config: CanvasConfig):
        self._cfg = config
        self._fig = None
        self._ax = None
        self.patches = []

    def __enter__(self):
        """Creates a new figure and axes for the canvas.

        The axes spans the entire figure and has no border. The x and y limits 
        are set to [-width/2, width/2] and [-height/2, height/2] respectively.
        The background color is set to the background color specified in the config.

        Returns:
            Canvas: The active canvas instance.

        Examples:
            >>> with Canvas(config) as canvas:
            ...     canvas.add_patch(patch)
            ...     canvas.save(output_cfg)
        """
        self._fig = plt.figure(
            figsize=(self._cfg.width, self._cfg.height), 
            facecolor=self._cfg.bg_color
        )
        # Create exactly 1 axes that spans the entire figure
        self._ax = self._fig.add_axes([0, 0, 1, 1])
        self._ax.set_xlim(-self._cfg.width / 2, self._cfg.width / 2)
        self._ax.set_ylim(-self._cfg.height / 2, self._cfg.height / 2)
        self._ax.axis('off')
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._fig:
            plt.close(self._fig)
            self._fig = None

    @property
    def ax(self) -> plt.Axes:
        return self._ax

    @property
    def fig(self) -> plt.Figure:
        return self._fig
        
    @property
    def cfg(self) -> CanvasConfig:
        return self._cfg

    @property
    def transData(self) -> transforms.Affine2D:
        return self._ax.transData

    def add_patch(self, patch: patches.Patch) -> patches.Patch:
        """
        Add a matplotlib Patch object to the canvas.

        This method is optimized for performance in stimulus generation scenarios.
        It uses `ax.add_artist()` internally to bypass Matplotlib's automatic 
        coordinate limit recalculation (O(N) overhead per patch), which is 
        redundant since stimkit uses fixed canvas boundaries.

        Parameters
        ----------
        patch : matplotlib.patches.Patch
            The patch to add. All standard properties (colors, transforms, 
            zorder, etc.) are fully preserved.

        Returns
        -------
        matplotlib.patches.Patch
            The patch object that was added.
        """
        # Ensure the patch is clipped by the axes box, matching add_patch() behavior
        if patch.get_clip_path() is None:
            patch.set_clip_path(self._ax.patch)
        
        # Add to ax.artists instead of ax.patches to skip _update_patch_limits
        self._ax.add_artist(patch)
        return patch

    def add_patches(self, patches: Iterable[patches.Patch]):
        """Add multiple matplotlib Patch objects to the canvas efficiently."""
        for patch in patches:
            self.add_patch(patch)


    def add_text(self, xy: tuple[float, float], text: str, **kwargs):
        """
        Add text to the canvas at the specified position.

        This method provides a convenient interface for adding text labels,
        annotations, or other textual content to the canvas.

        Parameters
        ----------
        xy : tuple[float, float]
            The position of the text in data coordinates.
        text : str
            The text string to display.
        **kwargs : dict, optional
            Additional keyword arguments passed to matplotlib's `ax.text()` method.
            Common options include:
            
            - transform : matplotlib.transforms.Transform
                The transform to apply to the text.
            - transform_rotates_text : bool
                Whether the transform rotates the text.
            - fontsize : int or float or {'xx-small', 'x-small', 'small', 'medium', 
              'large', 'x-large', 'xx-large'}
                Font size in points or relative size.
            - color : color spec
                Text color (name, hex string, or RGB tuple).
            - horizontalalignment (or ha) : {'left', 'center', 'right'}
                Horizontal alignment of the text relative to (x, y).
            - verticalalignment (or va) : {'top', 'center', 'bottom', 'baseline'}
                Vertical alignment of the text relative to (x, y).
            - rotation : float
                Rotation angle in degrees (counter-clockwise).
            - fontfamily : str or list of str
                Font family name(s).
            - fontweight : int or {'ultralight', 'light', 'normal', 'regular', 
              'book', 'medium', 'roman', 'semibold', 'demibold', 'demi', 'bold', 
              'heavy', 'extra bold', 'black'}
                Font weight.
            - alpha : float (0.0 to 1.0)
                Text transparency.

        Returns
        -------
        matplotlib.text.Text
            The created Text object, which can be used for further customization.

        Notes
        -----
        **Layer Ordering**: Like patches, text elements are drawn in the order 
        they are added. Text added earlier appears **below** text and patches 
        added later. To ensure text appears on top of all patches, add it after 
        adding all patches.

        The (x, y) position is interpreted in data coordinates, the same coordinate
        system used for patches and defined by the canvas xlim and ylim settings.

        Examples
        --------
        >>> with Canvas(config) as canvas:
        ...     # Add a background patch first
        ...     rect = Rectangle(xy=(-1, -0.5), width=2, height=1, color='lightblue')
        ...     canvas.add_patch(rect)
        ...     # Add text on top of the rectangle
        ...     canvas.add_text(
        ...         xy=(0, 0),
        ...         text='Hello World',
        ...         fontsize=14,
        ...         horizontalalignment='center',
        ...         verticalalignment='center',
        ...         color='black'
        ...     )
        """
        with resources.as_file(_FONT_RESOURCE) as font_path:
            font_prop = FontProperties(fname=str(font_path))
            return self._ax.text(xy[0], xy[1], text, fontproperties=font_prop, **kwargs)

    def clear(self):
        """
        Clears all added artists (patches, collections, texts) from the canvas.

        This is much faster than ax.clear() as it avoids resetting axes properties,
        scales, and layout configurations.
        """
        if not self._ax:
            return

        # Explicitly remove each type of artist
        # Using list() to avoid mutation issues during iteration
        for p in list(self._ax.patches):
            p.remove()
        for c in list(self._ax.collections):
            c.remove()
        for t in list(self._ax.texts):
            t.remove()
        for a in list(self._ax.artists):
            a.remove()

    def save(self, output_cfg: OutputConfig):
        if not self._fig:
            raise RuntimeError("Canvas not active.")

        self._fig.savefig(
            output_cfg.file_path, 
            pad_inches=0,
            dpi=self._cfg.dpi
        )
        logger.debug(f"Saved to: {output_cfg.file_path}")
