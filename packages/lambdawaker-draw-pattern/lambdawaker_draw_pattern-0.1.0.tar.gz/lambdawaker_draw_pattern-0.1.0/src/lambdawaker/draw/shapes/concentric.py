import aggdraw
from PIL import Image
import math


def rotating_polygons(draw, center, sides=6, num_polygons=10,
                      spacing=20, rotation_step=10,
                      color=(0, 0, 0, 255), thickness=2):
    """
    Draws concentric rotating polygons using aggdraw.

    :param draw: aggdraw.Draw object
    :param center: (x, y) tuple for the center of polygons
    :param sides: Number of sides for the polygons (3=triangle, 4=square, etc.)
    :param num_polygons: Total number of nested polygons
    :param spacing: Pixel distance between each consecutive polygon
    :param rotation_step: Degrees of rotation to add per nested layer
    :param color: RGBA tuple for the outline
    :param thickness: Line width
    """

    # Define the pen for drawing
    pen = aggdraw.Pen(color, thickness)
    cx, cy = center

    for i in range(1, num_polygons + 1):
        # Calculate the radius for this specific layer
        radius = i * spacing

        # Calculate the rotation for this specific layer (in radians)
        angle_offset = math.radians(i * rotation_step)

        # Generate coordinates for the polygon vertices
        points = []
        for s in range(sides):
            angle = (2 * math.pi * s / sides) + angle_offset
            x = cx + radius * math.cos(angle)
            y = cy + radius * math.sin(angle)
            points.append(x)
            points.append(y)

        # Create a path string for aggdraw or use draw.polygon
        # Note: aggdraw's polygon takes a list/sequence of coordinates
        draw.polygon(points, pen)
