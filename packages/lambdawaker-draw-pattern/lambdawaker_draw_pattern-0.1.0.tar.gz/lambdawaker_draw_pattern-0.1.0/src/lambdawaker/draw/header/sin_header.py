import aggdraw
import math
from PIL import Image


def draw_sine_header(canvas, height=100, amplitude=20, frequency=2, color=(0, 0, 0, 255)):
    """
    Creates a header with a sine-wave bottom edge.

    :param canvas: The aggdraw.Draw object.
    :param height: The vertical center point of the wave.
    :param amplitude: The height of the wave peaks.
    :param frequency: How many full waves span the width.
    :param color: Tuple (R, G, B, A).
    """
    width, _ = canvas.size
    brush = aggdraw.Brush(color)
    path = aggdraw.Path()

    # 1. Start at top-left and go to top-right
    path.moveto(0, 0)
    path.lineto(width, 0)

    # 2. Draw the right-side vertical edge down to the start of the wave
    # We calculate the Y for the sine wave at the far right edge
    end_y = height + amplitude * math.sin(2 * math.pi * frequency)
    path.lineto(width, end_y)

    # 3. Trace the Sine wave from right to left (back to x=0)
    # The more steps, the smoother the curve appears.
    steps = 100
    for i in range(steps, -1, -1):
        x = (i / steps) * width
        # Sine formula: y = baseline + amplitude * sin(2 * PI * freq * (x/width))
        y = height + amplitude * math.sin(2 * math.pi * frequency * (i / steps))
        path.lineto(x, y)

    # 4. Close the path (returns to 0,0)
    path.close()

    # 5. Render onto canvas
    canvas.path(path, brush)
    canvas.flush()


def create_sine_header(
    width=800,
    height=400,
    header_height=100,
    amplitude=20,
    frequency=2,
    color=(0, 0, 0, 255),
    bg_color=(0, 0, 0, 0),
):
    """
    Create an image and render a sine-wave header on top.

    Args:
        width (int): Image width.
        height (int): Image height.
        header_height (int): Vertical position of the wave baseline.
        amplitude (float): Wave amplitude in pixels.
        frequency (float): Number of full waves across the width.
        color (tuple): Fill color for the header (RGBA tuple).
        bg_color (tuple): Background color (RGBA tuple).

    Returns:
        PIL.Image.Image: The generated image.
    """
    img = Image.new("RGBA", (width, height), bg_color)
    draw = aggdraw.Draw(img)
    draw_sine_header(
        canvas=draw,
        height=header_height,
        amplitude=amplitude,
        frequency=frequency,
        color=color,
    )
    draw.flush()
    return img


