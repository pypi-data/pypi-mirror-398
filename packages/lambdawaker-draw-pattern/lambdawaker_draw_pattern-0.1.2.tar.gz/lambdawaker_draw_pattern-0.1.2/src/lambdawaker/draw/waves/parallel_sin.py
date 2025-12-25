from PIL import Image
import math
import aggdraw


def create_sine_waves(
    width=800,
    height=800,
    spacing=30,
    thickness=2,
    amplitude=40,
    frequency=0.01,
    angle=45,
    color=(0, 0, 0, 255),
    bg_color=(0, 0, 0, 0),
):
    """
    Create an RGBA image and draw rotated parallel sine waves on it.

    This is a convenience wrapper around `draw_angled_sine_waves` that
    allocates a new `PIL.Image.Image`, renders the waves using `aggdraw`,
    and returns the image.

    Args:
        width (int): Width of the output image in pixels.
        height (int): Height of the output image in pixels.
        spacing (int): Distance between adjacent sine baselines in pixels.
        thickness (float): Stroke thickness of the sine curves in pixels.
        amplitude (float): Peak amplitude of each sine wave in pixels.
        frequency (float): Frequency factor for the sine function; larger
            values create more oscillations per pixel along the wave.
        angle (float): Rotation angle in degrees; positive values rotate
            counterclockwise around the image center.
        color (tuple): Stroke color as an RGBA tuple.
        bg_color (tuple): Background color for the created image as RGBA;
            default is fully transparent black `(0, 0, 0, 0)`.

    Returns:
        PIL.Image.Image: The generated image containing the angled sine waves.
    """
    img = Image.new("RGBA", (width, height), bg_color)
    draw = aggdraw.Draw(img)
    draw_sine_waves(
        draw=draw,
        area_size=(width, height),
        spacing=spacing,
        thickness=thickness,
        amplitude=amplitude,
        frequency=frequency,
        angle=angle,
        color=color,
    )
    draw.flush()
    return img


def draw_sine_waves(
    draw,
    area_size,
    spacing=30,
    thickness=2,
    amplitude=40,
    frequency=0.01,
    angle=45,
    color=(0, 0, 0, 255),
):
    """
    Draw a set of parallel sine waves at a given rotation into a context.

    The sine waves are defined along a virtual horizontal axis and then rotated
    around the center of the area by `angle` degrees. The drawing extents are
    chosen to cover the rectangular area after rotation.

    Args:
        draw (aggdraw.Draw): The drawing context to render into.
        area_size (tuple[int, int]): Target area as `(width, height)` in pixels.
        spacing (int): Distance between adjacent sine baselines in pixels.
        thickness (float): Stroke thickness of the sine curves in pixels.
        amplitude (float): Peak amplitude of each sine wave in pixels.
        frequency (float): Frequency factor for the sine function; larger
            values create more oscillations per pixel along the wave.
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

    # Iterate baseline offsets for each parallel sine wave
    for d in range(-diagonal, diagonal + int(spacing), int(spacing)):
        pts = []
        # Sample the sine wave along a virtual x-axis spanning beyond the diagonal
        for x_virtual in range(-diagonal, diagonal + 1, 2):
            y_virtual = amplitude * math.sin(frequency * x_virtual) + d

            # Rotate the point around center
            nx = x_virtual * math.cos(rad) - y_virtual * math.sin(rad) + cx
            ny = x_virtual * math.sin(rad) + y_virtual * math.cos(rad) + cy

            pts.extend([nx, ny])

        if len(pts) > 3:
            draw.line(pts, pen)

    draw.flush()

