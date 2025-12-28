from laba44.math_advanced.mul_div import multiply, divide
import pytest


def test_multiply():
    assert multiply(2, 4) == 8


def test_divide():
    assert divide(10, 2) == 5


def test_divide_by_zero():
    with pytest.raises(ValueError):
        divide(5, 0)
