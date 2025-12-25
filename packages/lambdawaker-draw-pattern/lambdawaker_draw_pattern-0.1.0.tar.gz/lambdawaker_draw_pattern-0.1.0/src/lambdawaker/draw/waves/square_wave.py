from PIL import Image
import aggdraw
import math


def create_angled_square_waves(
    width=800,
    height=800,
    spacing=50,
    thickness=2,
    amplitude=25,
    wavelength=80,
    angle=0,
    color=(0, 0, 0, 255),
    bg_color=(0, 0, 0, 0),
):
    """
    Create an RGBA image and draw rotated parallel square waves on it.

    This is a convenience wrapper around `draw_angled_square_waves` that
    allocates a new `PIL.Image.Image`, renders the waves using `aggdraw`, and
    returns the image.

    Args:
        width (int): Width of the output image in pixels.
        height (int): Height of the output image in pixels.
        spacing (int): Distance between adjacent wave baselines in pixels.
        thickness (float): Stroke thickness of the wave in pixels.
        amplitude (float): Peak vertical displacement of the square wave in pixels.
        wavelength (float): Horizontal length of one full cycle in pixels.
        angle (float): Rotation in degrees; positive values rotate
            counterclockwise around the image center.
        color (tuple): Stroke color as an RGBA tuple.
        bg_color (tuple): Background color for the created image as RGBA; default
            is fully transparent black `(0, 0, 0, 0)`.

    Returns:
        PIL.Image.Image: The generated image containing the angled square waves.
    """
    img = Image.new("RGBA", (width, height), bg_color)
    draw = aggdraw.Draw(img)
    draw_angled_square_waves(
        draw=draw,
        area_size=(width, height),
        spacing=spacing,
        thickness=thickness,
        amplitude=amplitude,
        wavelength=wavelength,
        angle=angle,
        color=color,
    )
    draw.flush()
    return img


def draw_angled_square_waves(
    draw,
    area_size,
    spacing=50,
    thickness=2,
    amplitude=25,
    wavelength=80,
    angle=0,
    color=(0, 0, 0, 255),
):
    """
    Draw a set of parallel square waves at a given rotation into a context.

    Each wave alternates horizontal segments at `+amplitude` and `-amplitude`
    relative to its baseline, with vertical transitions at the half-wavelength
    boundaries. The entire set is rotated by `angle` degrees about the center
    and sized to cover the rectangular area after rotation.

    Args:
        draw (aggdraw.Draw): The drawing context to render into.
        area_size (tuple[int, int]): Target area as `(width, height)` in pixels.
        spacing (int): Distance between adjacent wave baselines in pixels.
        thickness (float): Stroke thickness of the wave in pixels.
        amplitude (float): Peak vertical displacement of the square wave in pixels.
        wavelength (float): Horizontal length of one full cycle in pixels.
        angle (float): Rotation angle in degrees; positive values rotate
            counterclockwise.
        color (tuple): Stroke color as an RGBA tuple.

    Returns:
        None: The drawing is rendered directly into `draw`.
    """
    width, height = area_size
    pen = aggdraw.Pen(color, thickness)

    rad = math.radians(angle)
    cx, cy = width / 2.0, height / 2.0

    # Ensure coverage of corners after rotation
    diagonal = int(math.sqrt(width ** 2 + height ** 2))

    # Half wavelength is the length of each flat section
    step = max(1, int(round(wavelength / 2.0)))

    def rotate_point(px: float, py: float):
        nx = px * math.cos(rad) - py * math.sin(rad) + cx
        ny = px * math.sin(rad) + py * math.cos(rad) + cy
        return nx, ny

    for d in range(-diagonal, diagonal + int(spacing), int(spacing)):
        y_high = d + amplitude
        y_low = d - amplitude

        # Build polyline: start at far left, alternate horizontal and vertical
        x = -diagonal - step
        pts = []

        # Initialize starting level so that segments align deterministically
        is_high = True
        # Move start to -diagonal
        x = -diagonal
        pts.extend(rotate_point(x, y_high if is_high else y_low))

        # Generate until far right
        while x <= diagonal + step:
            next_x = x + step
            y_curr = y_high if is_high else y_low
            y_next = y_low if is_high else y_high

            # Horizontal segment to next_x at current level
            pts.extend(rotate_point(next_x, y_curr))
            # Vertical transition at next_x to the other level
            pts.extend(rotate_point(next_x, y_next))

            x = next_x
            is_high = not is_high

        if len(pts) > 3:
            draw.line(pts, pen)

    draw.flush()

create_angled_square_waves().show()