# Rendering notes

- `Canvas.add_text` always uses the bundled NotoSansSC font resource, so text
  rendering is deterministic across environments.
- The font file is packaged under `stimkit/resources/` and loaded via
  `importlib.resources` to work both from source and from a wheel.
