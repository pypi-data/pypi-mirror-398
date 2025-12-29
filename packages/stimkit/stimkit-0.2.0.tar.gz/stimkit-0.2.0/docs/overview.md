# Overview

stimkit is a small drawing toolkit built on matplotlib. It provides:

- `Canvas` and `Renderer` for structured scene rendering.
- A `collections` module of reusable geometric shapes.
- `VisualAngle` and `Pixel` helpers for stimulus geometry.

Typical flow:

1. Create a `Renderer` with a `CanvasConfig`.
2. Build a scene config (Pydantic model).
3. `renderer.render(scene, OutputConfig(file_path=...))`.

See `collections.md` for shape orientation details.
