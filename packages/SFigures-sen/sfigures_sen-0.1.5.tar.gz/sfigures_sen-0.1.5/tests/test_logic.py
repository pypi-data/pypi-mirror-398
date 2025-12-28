import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from Sfigures.figures import square_area, circle_area, triangle_area
from Sfigures.utils import is_valid_size

def test_square():
    assert square_area(4) == 16

def test_circle():
    assert round(circle_area(1), 2) == 3.14

def test_triangle():
    assert triangle_area(10, 5) == 25.0

def test_validation():
    assert is_valid_size(10) is True
    assert is_valid_size(-5) is False
    assert is_valid_size(0) is False