from PIL import Image
import aggdraw
import math


def create_parallel_lines(
    width=800,
    height=800,
    spacing=20,
    thickness=2,
    angle=45,
    color=(0, 0, 0, 255),
    bg_color=(0, 0, 0, 0),
):
    """
    Create an RGBA image and draw parallel angled lines on it.

    This is a convenience wrapper around `draw_angled_lines` that allocates a
    new `PIL.Image.Image`, renders the lines using `aggdraw`, and returns the
    image.

    Args:
        width (int): Width of the output image in pixels.
        height (int): Height of the output image in pixels.
        spacing (int): Distance between adjacent lines in pixels.
        thickness (float): Line stroke width in pixels.
        angle (float): Line orientation in degrees; 0 is horizontal, positive
            values rotate counterclockwise.
        color (tuple): Stroke color as an RGBA tuple.
        bg_color (tuple): Background color for the created image as RGBA;
            default is fully transparent black `(0, 0, 0, 0)`.

    Returns:
        PIL.Image.Image: The generated image containing the angled lines.
    """
    img = Image.new("RGBA", (width, height), bg_color)
    draw = aggdraw.Draw(img)
    draw_parallel_lines(
        draw,
        (width, height),
        spacing=spacing,
        thickness=thickness,
        angle=angle,
        color=color,
    )
    draw.flush()
    return img


def draw_parallel_lines(
    draw,
    area_size,
    spacing=20,
    thickness=2,
    angle=45,
    color=(0, 0, 0, 255),
):
    """
    Draw a set of equally spaced, parallel lines at a given angle into a context.

    The line segment extents are chosen so that, for the given rotation, the
    rectangular area is fully covered.

    Args:
        draw (aggdraw.Draw): The drawing context to render into.
        area_size (tuple[int, int]): Target area size as `(width, height)` in pixels.
        spacing (int): Distance between adjacent lines in pixels.
        thickness (float): Line stroke width in pixels.
        angle (float): Line orientation in degrees; 0 is horizontal, positive
            values rotate counterclockwise.
        color (tuple): Stroke color as an RGBA tuple.

    Returns:
        None: The drawing is rendered directly into `draw`.
    """
    width, height = area_size
    pen = aggdraw.Pen(color, thickness)

    # Convert angle to radians
    radians = math.radians(angle)

    # Calculate the diagonal of the canvas to ensure full coverage
    diagonal = int(math.sqrt(width ** 2 + height ** 2))

    # Draw lines large enough to cover the rotated viewport
    for d in range(-diagonal, diagonal * 2, int(spacing)):
        # Start and end far outside the canvas boundaries
        x0 = d * math.cos(radians + math.pi / 2) - diagonal * math.cos(radians)
        y0 = d * math.sin(radians + math.pi / 2) - diagonal * math.sin(radians)
        x1 = d * math.cos(radians + math.pi / 2) + diagonal * math.cos(radians)
        y1 = d * math.sin(radians + math.pi / 2) + diagonal * math.sin(radians)

        draw.line((x0, y0, x1, y1), pen)

    draw.flush()
