import pytest
from seallib.eyler import func_eyler


@pytest.mark.parametrize("n, expected", [
    (1, 1), (2, 1), (12, 4), (13, 12), (30, 8)])

def test_eyler(n, expected):
    assert func_eyler(n) == expected

