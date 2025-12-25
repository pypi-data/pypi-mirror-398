from PIL import Image
import aggdraw
import math

def create_hexagon_grid(
        width=800,
        height=800,
        hexagon_size=20,
        thickness=2.0,
        angle=0,
        color=(0, 0, 0, 255),
        bg_color=(0, 0, 0, 0)):
    """
    Create an RGBA image and draw a hexagonal grid on it.

    This is a convenience wrapper around `draw_hexagon_grid` that allocates a
    new `PIL.Image.Image`, draws the grid using `aggdraw`, and returns the image.

    Args:
        width (int): Width of the output image in pixels.
        height (int): Height of the output image in pixels.
        hexagon_size (float): Distance from the hexagon center to a vertex
            (circumradius), in pixels.
        thickness (float): Stroke thickness of hexagon edges in pixels.
        angle (float): Rotation of the entire grid in degrees. Positive values
            rotate counterclockwise around the image center.
        color (tuple): Stroke color as an RGBA tuple.
        bg_color (tuple): Background color for the created image as RGBA
            (default fully transparent black `(0, 0, 0, 0)`).

    Returns:
        PIL.Image.Image: The generated image containing the hexagon grid.
    """
    img = Image.new("RGBA", (width, height), bg_color)
    draw = aggdraw.Draw(img)
    size = img.size

    draw_hexagon_grid(
        draw=draw,
        area_size=size,
        hexagon_size=hexagon_size,
        thickness=thickness,
        angle=angle,
        color=color,
    )
    return img


def draw_hexagon_grid(
        draw,
        area_size,
        hexagon_size=50,
        thickness=2.0,
        angle=0,
        color=(0, 0, 0, 255),
):
    """
    Draw a hexagon tiling across a given area onto an existing `aggdraw` context.

    The grid is large enough to cover the entire rectangular area and can be
    rotated around the area's center.

    Args:
        draw (aggdraw.Draw): The drawing context to render into.
        area_size (tuple[int, int]): The target area size as `(width, height)`
            in pixels.
        hexagon_size (float): Distance from the hexagon center to a vertex
            (circumradius), in pixels.
        thickness (float): Stroke thickness of hexagon edges in pixels.
        angle (float): Rotation of the entire grid in degrees. Positive values
            rotate counterclockwise around the center of the area.
        color (tuple): Stroke color as an RGBA tuple.
        center (tuple[int, int] | None): The center point of the grid as
            `(x, y)` in pixels. If `None`, the grid is centered on `area_size`.

    Returns:
        None: The drawing is rendered directly into `draw`.
    """
    width, height = area_size
    pen = aggdraw.Pen(color, thickness)

    cx, cy = width / 2, height / 2
    rad_rotation = math.radians(angle)

    # Hexagon Math: Width and Height of a single hexagon
    hex_width = 2 * hexagon_size
    hex_height = math.sqrt(3) * hexagon_size

    # Horizontal and Vertical spacing for tiling
    horiz_dist = hex_width * 3 / 4
    vert_dist = hex_height

    # Calculate diagonal to ensure full coverage during rotation
    diagonal = int(math.sqrt(width ** 2 + height ** 2))

    # helper for rotation
    def rotate_point(px, py):
        # Translate to origin, rotate, translate back
        tx, ty = px - cx, py - cy
        rx = tx * math.cos(rad_rotation) - ty * math.sin(rad_rotation) + cx
        ry = tx * math.sin(rad_rotation) + ty * math.cos(rad_rotation) + cy
        return rx, ry

    # Iterate through a grid large enough to cover the diagonal
    for col in range(-diagonal // int(horiz_dist) - 2, diagonal // int(horiz_dist) + 2):
        for row in range(-diagonal // int(vert_dist) - 2, diagonal // int(vert_dist) + 2):

            # Calculate center of current hexagon
            # Offset every other column
            x_offset = col * horiz_dist
            y_offset = row * vert_dist
            if col % 2 != 0:
                y_offset += vert_dist / 2

            # Draw the 6 sides
            points = []
            for i in range(7):  # 7 points to close the loop
                # Calculate vertex relative to grid origin (0,0) before rotation
                angle_deg = 60 * i
                angle_rad = math.radians(angle_deg)

                px = x_offset + hexagon_size * math.cos(angle_rad)
                py = y_offset + hexagon_size * math.sin(angle_rad)

                # Apply global grid rotation
                rx, ry = rotate_point(px, py)
                points.extend([rx, ry])

            draw.line(points, pen)

    draw.flush()



