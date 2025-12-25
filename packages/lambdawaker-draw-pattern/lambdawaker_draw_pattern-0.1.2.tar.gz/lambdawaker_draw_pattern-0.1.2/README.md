lambda-draw-tools

Drawing utilities for generating geometric patterns, grids, and wave-based line art using Pillow and aggdraw.

Install

```
pip install lambda-draw-tools
```

Quick start

Hexagon grid

```python
from lambdawaker.draw.grid.hexagon_grid import create_hexagon_grid

img = create_hexagon_grid(
    width=600,
    height=600,
    hexagon_size=40,
    thickness=2,
    angle=0,
    color="#4B0082",
    bg_color=(255, 255, 255, 0),
)
img.show()
```

Angled parallel lines

```python
from lambdawaker.draw.waves.parallel_lines import create_parallel_lines

img = create_parallel_lines(
    width=800,
    height=600,
    spacing=24,
    thickness=2,
    angle=35,
    color="midnightblue",
    bg_color=(255, 255, 255, 0),
)
img.show()
```

Requirements

- Python 3.8+
- Pillow >= 9.0
- aggdraw >= 1.3.16.post1

Notes

- On some platforms, `aggdraw` may require build tools if a prebuilt wheel isn’t available.
- The library exposes convenience creators like `create_hexagon_grid` and `create_parallel_lines`, as well as lower-level `draw_*` functions that render into an existing `aggdraw.Draw` context.
