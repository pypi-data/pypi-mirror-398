import pytest
from seallib.eyler import func_eyler

@pytest.mark.parametrize("n, expected", [
    (1, 1), (2, 1), (3, 2), (4, 2), 
    (12, 4), (13, 12), (30, 8), (100, 40)
])
def test_basic_values(n, expected):
    assert func_eyler(n) == expected