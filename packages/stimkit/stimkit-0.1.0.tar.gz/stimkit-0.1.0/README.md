# stimkit

`stimkit` is the Python package that powered the `stim_example` project. This repository now houses

- the reusable `stimkit` sources under a `src/stimkit` layout,
- the original `example` scripts that demonstrate the basic drawing workflows, and
- the minimal metadata needed to build and install the package.

## Getting started

1. Install the project in editable mode while you explore the examples:

   ```bash
   python -m pip install -e .
   ```

2. Run one of the example scripts to render the corresponding SVG output (each script writes to `example/output/`).

   ```bash
   python example/1_hello_world.py
   ```

3. Open the generated `example/output/1_hello_world.svg` in a browser or viewer to inspect the result.

## Repository layout

- `src/stimkit/`: package implementation (canvas, renderers, layout helpers, IO helpers, etc.).
- `example/`: scripts that consume `Stimkit` to draw progressively more complex scenes.
- `README.md`, `pyproject.toml`, `LICENSE`: standard package metadata.

## License

This project is distributed under the same terms as the `LICENSE` file already present in the repository.
