import math

import aggdraw
from PIL import Image

from lambdawaker.draw.grid.simple_shapes import circle


def create_shapes_grid(width=800, height=800, radius=15,
                       draw_function=circle, draw_parameters=None,
                       separation=10, angle=0, thickness=2,
                       color=(0, 0, 0, 255), outline=(0, 0, 0, 255)
                       ):
    """Create an RGBA image and draw a grid of shapes.

    Args:
        width (int): Image width in pixels.
        height (int): Image height in pixels.
        radius (float): Base radius for shapes.
        draw_function (callable): Shape drawing function from `simple_shapes`.
        draw_parameters (dict | None): Extra keyword args for the shape function.
        separation (float): Extra spacing added between shapes.
        angle (float): Rotation angle for the grid.
        thickness (float): Outline thickness in pixels.
        color (tuple): Fill color as an RGBA tuple.
        outline (tuple): Outline color as an RGBA tuple.

    Returns:
        PIL.Image.Image: The generated image.
    """
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = aggdraw.Draw(img)
    size = img.size

    draw_parameters = draw_parameters if draw_parameters is not None else {}

    draw_shapes_grid(draw, size, radius,
                     draw_function=draw_function,
                     draw_parameters=draw_parameters,
                     separation=separation, angle=angle, thickness=thickness,
                     color=color, outline=outline)
    return img


def draw_shapes_grid(draw, size, radius,
                     draw_function=None,
                     draw_parameters=None,
                     separation=0, angle=0, thickness=2,
                     color=(0, 0, 0, 255), outline=(0, 0, 0, 255)):
    """Draw a staggered grid of shapes into an existing aggdraw context.

    Args:
        draw (aggdraw.Draw): Target drawing context.
        size (tuple[int,int]): Canvas size as (width, height).
        radius (float): Base radius for shapes.
        draw_function (callable | None): Shape drawing function. Defaults to circle.
        draw_parameters (dict | None): Extra keyword args passed to shape function.
        separation (float): Extra spacing between neighbors.
        angle (float): Grid rotation angle in degrees.
        thickness (float): Outline thickness in pixels.
        color (tuple): Fill color as an RGBA tuple.
        outline (tuple): Outline color as an RGBA tuple.
    """
    draw_function = draw_function if draw_function is not None else circle
    draw_parameters = draw_parameters if draw_parameters is not None else {}
    width, height = size

    brush = aggdraw.Brush(color)
    pen = aggdraw.Pen(outline, thickness)

    eff_r = radius + (separation / 2)
    h_spacing = eff_r * 2
    v_spacing = eff_r * math.sqrt(3)

    rad = math.radians(angle)
    cos_a, sin_a = math.cos(rad), math.sin(rad)
    cx, cy = width / 2, height / 2

    # Coverage margin (increased to account for rotation clipping)
    limit = int(max(width, height) / radius) + 10

    for row in range(-limit, limit):
        for col in range(-limit, limit):
            grid_x = col * h_spacing
            if row % 2 == 1:
                grid_x += eff_r
            grid_y = row * v_spacing

            rot_x = grid_x * cos_a - grid_y * sin_a + cx
            rot_y = grid_x * sin_a + grid_y * cos_a + cy

            # Bounds check with a buffer for rotated shapes
            buffer = radius * 2
            if -buffer < rot_x < width + buffer and -buffer < rot_y < height + buffer:
                # Now passing 'angle' to the proxy!
                draw_function(draw, (rot_x, rot_y), radius, angle, pen, brush, **draw_parameters)

    draw.flush()


