from PIL import Image
import math
import aggdraw


def create_angled_sawtooth_waves(
    width=800,
    height=800,
    spacing=50,
    thickness=2,
    amplitude=25,
    wavelength=80,
    angle=20,
    color=(0, 0, 0, 255),
    bg_color=(0, 0, 0, 0),
):
    """
    Create an RGBA image and draw rotated parallel sawtooth waves on it.

    This is a convenience wrapper around `draw_angled_sawtooth_waves` that
    allocates a new `PIL.Image.Image`, renders the waves using `aggdraw`, and
    returns the image.

    Args:
        width (int): Width of the output image in pixels.
        height (int): Height of the output image in pixels.
        spacing (int): Distance between adjacent sawtooth baselines in pixels.
        thickness (float): Stroke thickness of the wave in pixels.
        amplitude (float): Peak vertical displacement of the sawtooth in pixels.
        wavelength (float): Horizontal length of one full tooth in pixels.
        angle (float): Rotation in degrees; positive values rotate
            counterclockwise around the image center.
        color (tuple): Stroke color as an RGBA tuple.
        bg_color (tuple): Background color for the created image as RGBA. Default
            is fully transparent black `(0, 0, 0, 0)`.

    Returns:
        PIL.Image.Image: The generated image containing the angled sawtooth waves.
    """
    img = Image.new("RGBA", (width, height), bg_color)
    draw = aggdraw.Draw(img)
    draw_angled_sawtooth_waves(
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


def draw_angled_sawtooth_waves(
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
    Draw a set of parallel sawtooth waves at a given rotation into a context.

    Each wave is a zigzag (sawtooth) formed by alternating peaks and troughs
    spaced by `wavelength / 2`. The set of waves is rotated by `angle` degrees
    about the center and sized to cover the rectangular area after rotation.

    Args:
        draw (aggdraw.Draw): The drawing context to render into.
        area_size (tuple[int, int]): Target area as `(width, height)` in pixels.
        spacing (int): Distance between adjacent sawtooth baselines in pixels.
        thickness (float): Stroke thickness of the wave in pixels.
        amplitude (float): Peak vertical displacement of the sawtooth in pixels.
        wavelength (float): Horizontal length of one full tooth in pixels.
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

    # Step for alternating peak/trough points along the x-axis
    step = max(1, int(round(wavelength / 2.0)))

    for d in range(-diagonal, diagonal + int(spacing), int(spacing)):
        pts = []
        # Build a zigzag path far beyond the diagonal for full coverage
        for x_virtual in range(-diagonal - step, diagonal + step + 1, step):
            is_peak = ((x_virtual // step) % 2) == 0
            y_virtual = d + (amplitude if is_peak else -amplitude)

            # Rotate around center
            nx = x_virtual * math.cos(rad) - y_virtual * math.sin(rad) + cx
            ny = x_virtual * math.sin(rad) + y_virtual * math.cos(rad) + cy

            pts.extend([nx, ny])

        if len(pts) > 3:
            draw.line(pts, pen)

    draw.flush()

create_angled_sawtooth_waves().show()