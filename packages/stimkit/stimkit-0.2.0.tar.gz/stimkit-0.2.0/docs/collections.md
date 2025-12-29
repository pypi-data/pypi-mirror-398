# Collections (shapes and orientation)

This module provides reusable matplotlib patches. For anything with an
`angle` or `rotation`, **angle=0 is the canonical orientation** described
below. Positive angles rotate counter-clockwise.

## lines.py

- `centered_line`: angle=0 is a horizontal line (left-to-right).
- `cross_line`: angle=0 gives a plus sign with horizontal + vertical lines.

## notched_circle.py

- `notched_circle`: angle=0 positions the square notch on the **right** edge of
  the circle, centered vertically; angle=90 moves the notch to the **top**.

## shapes.py

- `circle`: no orientation (rotation not applicable).
- `square`: rotation=0 is axis-aligned (edges parallel to x/y).
- `triangle`: rotation=0 points **up** (one vertex at the top).
- `diamond`: rotation=0 is a rotated square with a vertex pointing **up**.
- `hexagon`: rotation=0 has a vertex pointing to the **right** (positive x).
- `star`: rotation=0 has a point at the **top** (12 o'clock).
- `centered_arrow`: angle=0 points to the **right** (positive x).
- `semicircle`: no angle parameter; `orientation` selects which side is curved
  (top/bottom/left/right). Default is `top`.
- `ring`: no orientation (rotation not applicable).
