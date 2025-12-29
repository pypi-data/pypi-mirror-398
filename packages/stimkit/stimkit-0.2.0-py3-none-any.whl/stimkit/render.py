from .canvas import CanvasConfig, OutputConfig, Canvas
from abc import ABC, abstractmethod
from pydantic import BaseModel

class Renderer(ABC):
    """
    Base class for all stimulus renderers.
    
    Thread safety: This class is NOT thread-safe. It manages an internal 
    cached Canvas to optimize performance. Simultaneous rendering from 
    multiple threads is unsafe.
    """
    def __init__(self, canvas_cfg: CanvasConfig):
        self.canvas_cfg = canvas_cfg
        self._canvas = Canvas(self.canvas_cfg)
        self._is_activated = False

    def render(self, scene_cfg: BaseModel, output_cfg: OutputConfig, canvas: Canvas | None = None):
        """
        The template method that executes the rendering process.
        
        Args:
            scene_cfg: Configuration for the scene to draw.
            output_cfg: Configuration for where to save the output.
            canvas: Optional existing Canvas to reuse. If provided, it takes 
                   precedence over the internal cached canvas.
        """
        # 1. Determine which canvas to use (passed or internal)
        target_canvas = canvas if canvas is not None else self._canvas

        # 2. Lazy activation of internal canvas
        if target_canvas is self._canvas and not self._is_activated:
            self._canvas.__enter__()
            self._is_activated = True

        # 3. Clean, Draw, and Save
        target_canvas.clear()
        self.draw(target_canvas, scene_cfg)
        target_canvas.save(output_cfg)

    def __del__(self):
        """Ensure the internal figure is closed when the renderer is destroyed."""
        if hasattr(self, "_is_activated") and self._is_activated:
            try:
                self._canvas.__exit__(None, None, None)
            except Exception:
                pass

    @abstractmethod
    def draw(self, canvas: Canvas, scene_cfg: BaseModel):
        """
        Hook method for concrete drawing logic.
        Must be implemented by subclasses.
        """
        raise NotImplementedError
