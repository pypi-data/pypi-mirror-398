import pytest
from PIL import Image

from lambdawaker.draw.grid.shapes_grid import create_shapes_grid
from lambdawaker.draw.grid.simple_shapes import circle


def test_create_shapes_grid_default():
    """Test create_shapes_grid with default parameters."""
    img = create_shapes_grid()

    assert isinstance(img, Image.Image)
    assert img.size == (800, 800)
    assert img.mode == "RGBA"


def test_create_shapes_grid_custom_dimensions():
    """Test create_shapes_grid with custom width and height."""
    width, height = 1024, 768
    img = create_shapes_grid(width=width, height=height)

    assert isinstance(img, Image.Image)
    assert img.size == (width, height)
    assert img.mode == "RGBA"


def test_create_shapes_grid_with_parameters():
    """Test create_shapes_grid with custom radius, separation, and thickness."""
    img = create_shapes_grid(
        width=600,
        height=600,
        radius=20,
        separation=15,
        thickness=3,
        color=(255, 0, 0, 255),
        outline=(0, 0, 255, 255)
    )

    assert isinstance(img, Image.Image)
    assert img.size == (600, 600)


def test_create_shapes_grid_with_rotation():
    """Test create_shapes_grid with rotation angle."""
    img = create_shapes_grid(angle=45)

    assert isinstance(img, Image.Image)
    assert img.size == (800, 800)


def test_create_shapes_grid_with_draw_parameters():
    """Test create_shapes_grid with custom draw_parameters."""
    draw_params = {"some_param": "value"}
    img = create_shapes_grid(
        draw_function=circle,
        draw_parameters=draw_params
    )

    assert isinstance(img, Image.Image)
    assert img.size == (800, 800)

