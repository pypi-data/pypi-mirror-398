import aggdraw


def draw_squared_header(canvas, height=100, color=(0, 0, 0, 255)):
    """
    Fills the top area of the canvas to create a header section.

    :param canvas: The aggdraw.Draw object.
    :param height: The vertical distance from the top to fill.
    :param color: A tuple (R, G, B).
    """
    # Create a Brush for the fill.
    # aggdraw uses (opacity, R, G, B) for color arguments in the Brush.
    brush = aggdraw.Brush(color)

    # Define the coordinates for the header rectangle: (x0, y0, x1, y1)
    # We get the width from the canvas's internal surface if needed,
    # but drawing past the edge is safe in aggdraw.
    width = canvas.size[0]

    # Draw the rectangle (no Pen/outline needed for a simple fill)
    canvas.rectangle((0, 0, width, height), brush)

    # Ensure the drawing is flushed to the image buffer
    canvas.flush()


def create_squared_header(
    width=800,
    height=400,
    header_height=100,
    color=(0, 0, 0, 255),
    bg_color=(0, 0, 0, 0),
):
    """
    Create an image and render a rectangular header on top.

    Args:
        width (int): Image width.
        height (int): Image height.
        header_height (int): Height of the filled header area from the top.
        color (tuple|str): Fill color for the header.
        bg_color (tuple|str): Background color (supports RGBA).

    Returns:
        PIL.Image.Image: The generated image.
    """
    from PIL import Image

    img = Image.new("RGBA", (width, height), bg_color)
    draw = aggdraw.Draw(img)
    draw_squared_header(canvas=draw, height=header_height, color=color)
    draw.flush()
    return img


def create_square_header(
    width=800,
    height=400,
    header_height=100,
    color=(0, 0, 0, 255),
    bg_color=(0, 0, 0, 0),
):
    """Alias for create_squared_header for convenience."""
    return create_squared_header(
        width=width,
        height=height,
        header_height=header_height,
        color=color,
        bg_color=bg_color,
    )

