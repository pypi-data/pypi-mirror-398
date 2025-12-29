# test_utils.py
from utils import multiply

def test_multiply_basic():
    assert multiply(2, 3) == 6
    assert multiply(-2, 5) == -10
    assert multiply(0, 7) == 0
