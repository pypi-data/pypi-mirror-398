from PIL import Image
import aggdraw
import math


def create_triangle_grid(
    width=800,
    height=800,
    size=50,
    thickness=2.0,
    angle=0,
    color=(0, 0, 0, 255),
    bg_color=(0, 0, 0, 0),
):
    """
    Create an RGBA image and draw an equilateral triangle tiling on it.

    This is a convenience wrapper around `draw_triangle_grid` that allocates a
    new `PIL.Image.Image`, renders the grid using `aggdraw`, and returns the image.

    Args:
        width (int): Width of the output image in pixels.
        height (int): Height of the output image in pixels.
        size (float): Side length of each equilateral triangle in pixels.
        thickness (float): Stroke thickness of triangle edges in pixels.
        angle (float): Rotation of the entire grid in degrees; positive values
            rotate counterclockwise around the image center.
        color (tuple): Stroke color as an RGBA tuple.
        bg_color (tuple): Background color as an RGBA tuple. Default is fully
            transparent black `(0, 0, 0, 0)`.

    Returns:
        PIL.Image.Image: The generated image containing the triangle grid.
    """
    img = Image.new("RGBA", (width, height), bg_color)
    draw = aggdraw.Draw(img)
    draw_triangle_grid(
        draw=draw,
        area_size=(width, height),
        size=size,
        thickness=thickness,
        angle=angle,
        color=color,
    )
    draw.flush()
    return img


def draw_triangle_grid(
    draw,
    area_size,
    size=50,
    thickness=2.0,
    angle=0,
    color=(0, 0, 0, 255),
):
    """
    Draw a tiling of equilateral triangles across a given area into a context.

    The grid is large enough to cover the rectangular area after rotation by
    `angle` degrees around the center.

    Args:
        draw (aggdraw.Draw): The drawing context to render into.
        area_size (tuple[int, int]): Target area as `(width, height)` in pixels.
        size (float): Side length of each equilateral triangle in pixels.
        thickness (float): Stroke thickness of triangle edges in pixels.
        angle (float): Rotation angle in degrees; positive values rotate
            counterclockwise.
        color (tuple): Stroke color as an RGBA tuple.

    Returns:
        None: The drawing is rendered directly into `draw`.
    """
    width, height = area_size
    pen = aggdraw.Pen(color, thickness)

    cx, cy = width / 2.0, height / 2.0
    rad = math.radians(angle)

    # Equilateral triangle geometry
    tri_height = (math.sqrt(3.0) / 2.0) * size
    horiz_dist = size / 2.0
    vert_dist = tri_height

    # Coverage for rotation
    diagonal = int(math.sqrt(width ** 2 + height ** 2))

    def rot(px: float, py: float):
        nx = px * math.cos(rad) - py * math.sin(rad) + cx
        ny = px * math.sin(rad) + py * math.cos(rad) + cy
        return nx, ny

    col_range = int(diagonal // max(1.0, horiz_dist)) + 4
    row_range = int(diagonal // max(1.0, vert_dist)) + 4

    for row in range(-row_range, row_range + 1):
        for col in range(-col_range, col_range + 1):
            x_base = col * horiz_dist
            y_base = row * vert_dist

            # Alternate up and down triangles
            is_up = ((row + col) % 2) == 0

            if is_up:
                verts = [
                    (x_base, y_base),
                    (x_base - size / 2.0, y_base + tri_height),
                    (x_base + size / 2.0, y_base + tri_height),
                ]
            else:
                verts = [
                    (x_base, y_base + tri_height),
                    (x_base - size / 2.0, y_base),
                    (x_base + size / 2.0, y_base),
                ]

            verts.append(verts[0])  # close path

            path = []
            for px, py in verts:
                path.extend(rot(px, py))

            draw.line(path, pen)

    draw.flush()

create_triangle_grid().show()