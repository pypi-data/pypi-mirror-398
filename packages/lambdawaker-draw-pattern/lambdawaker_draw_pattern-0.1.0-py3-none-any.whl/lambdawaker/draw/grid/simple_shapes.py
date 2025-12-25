import math


def circle(draw, center, radius, _, pen, brush, **__):
    """Draws a circle (angle doesn't change a circle's appearance)."""
    x, y = center
    draw.ellipse((x - radius, y - radius, x + radius, y + radius), pen, brush)


def square(draw, center, radius, angle, pen, brush, **_):
    """Draws a square rotated by the grid angle."""
    cx, cy = center
    rad = math.radians(angle)
    cos_a, sin_a = math.cos(rad), math.sin(rad)

    # Define the 4 corners of the square relative to (0,0)
    corners = [
        (-radius, -radius),
        (radius, -radius),
        (radius, radius),
        (-radius, radius)
    ]

    # Rotate each corner and shift to the center (cx, cy)
    rotated_corners = []
    for px, py in corners:
        rx = px * cos_a - py * sin_a + cx
        ry = px * sin_a + py * cos_a + cy
        rotated_corners.extend([rx, ry])  # aggdraw polygon takes a flat list

    draw.polygon(rotated_corners, pen, brush)


def triangle(draw, center, radius, angle, pen, brush, **_):
    """Draws an equilateral triangle rotated by the grid angle."""
    cx, cy = center
    # Convert base angle to radians
    # We subtract 90 degrees (pi/2) so the first vertex is at the top
    rad_offset = math.radians(angle) - (math.pi / 2)

    vertices = []
    # An equilateral triangle has 3 vertices
    for i in range(3):
        # Each vertex is 120 degrees apart
        phi = rad_offset + (2 * math.pi / 3) * i
        vx = cx + radius * math.cos(phi)
        vy = cy + radius * math.sin(phi)
        vertices.extend([vx, vy])

    draw.polygon(vertices, pen, brush)


def polygon(draw, center, radius, angle, pen, brush, sides=5, **_):
    """
    Draws a regular polygon with 'n' sides.
    - sides=3: Triangle
    - sides=4: Diamond/Square
    - sides=5: Pentagon
    - sides=6: Hexagon
    """
    cx, cy = center
    # Subtract 90 degrees to make the first point the "top" vertex
    rad_offset = math.radians(angle) - (math.pi / 2)

    vertices = []
    for i in range(sides):
        # Angle for this specific vertex
        phi = rad_offset + (2 * math.pi / sides) * i
        vx = cx + radius * math.cos(phi)
        vy = cy + radius * math.sin(phi)
        vertices.extend([vx, vy])

    draw.polygon(vertices, pen, brush)


def star(draw, center, radius, angle, pen, brush, points=5, inner_radius=None, **_):
    """
    Draws a star with 'n' points.
    - points: Number of star tips
    - inner_radius: Distance to the 'valleys'. Defaults to half the radius.
    """
    cx, cy = center
    if inner_radius is None:
        inner_radius = radius * 0.5  # Default pointiness

    # Start at the top
    rad_offset = math.radians(angle) - (math.pi / 2)

    vertices = []
    # A star has 2 points per "arm" (tip and valley)
    for i in range(points * 2):
        # Alternate between outer and inner radius
        r = radius if i % 2 == 0 else inner_radius

        # Angle increments by half the step of a normal polygon
        phi = rad_offset + (math.pi / points) * i
        vx = cx + r * math.cos(phi)
        vy = cy + r * math.sin(phi)
        vertices.extend([vx, vy])

    draw.polygon(vertices, pen, brush)
