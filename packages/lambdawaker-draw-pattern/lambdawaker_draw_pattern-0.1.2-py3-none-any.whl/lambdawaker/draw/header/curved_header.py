import aggdraw


def draw_curved_header(canvas, height=100, curve_depth=50, color=(0, 0, 0, 255)):
    """
    Creates a header with a curved bottom edge using aggdraw.path()
    """
    width, _ = canvas.size
    brush = aggdraw.Brush(color)

    # 1. Define the Path coordinates/commands
    # aggdraw.Path() accepts a list of coordinates or a symbol string,
    # but we can also use its methods.
    path = aggdraw.Path()
    path.moveto(0, 0)
    path.lineto(width, 0)
    path.lineto(width, height)

    # Use qcurveto for the 4-parameter quadratic curve
    # (control_x, control_y, end_x, end_y)
    # Arguments: (ctrl1_x, ctrl1_y, ctrl2_x, ctrl2_y, end_x, end_y)
    path.curveto(width * 0.75, height + curve_depth, width * 0.25, height + curve_depth, 0, height)
    path.close()

    # 2. DRAW the path using the canvas object
    # The syntax is: canvas.path(path, pen_or_brush)
    # Or: canvas.path(path_string, pen, brush)
    canvas.path(path, brush)

    # 3. Flush to the PIL image
    canvas.flush()


def create_curved_header(
    width=800,
    height=400,
    header_height=100,
    curve_depth=50,
    color=(0, 0, 0, 255),
    bg_color=(0, 0, 0, 0),
):
    """
    Create an image and render a curved header on top.

    Args:
        width (int): Image width.
        height (int): Image height.
        header_height (int): Vertical position where the curve meets the sides.
        curve_depth (int|float): How far the curve dips below the header_height.
        color (tuple): Fill color for the header as an RGBA tuple.
        bg_color (tuple): Background color (RGBA).

    Returns:
        PIL.Image.Image: The generated image.
    """
    from PIL import Image

    img = Image.new("RGBA", (width, height), bg_color)
    draw = aggdraw.Draw(img)
    draw_curved_header(canvas=draw, height=header_height, curve_depth=curve_depth, color=color)
    draw.flush()
    return img

