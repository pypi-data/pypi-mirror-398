import pytest
from seallib.graphs import deykstra
def test_deykstra():
    graph = {
        "1": {"2": 3, "3": 8, "4": 4},
        "2": {"1": 6, "5": 13, "7": 4, "8": 9},
        "3": {"4":2, "5": 10, "6": 5},
        "4": {"5": 2},
        "5": {"6": 3},
        "6": {"7": 2},
        "7": {"8": 1},
        "8": {"9": 3, "10": 2, "11": 12},
        "9": {"10": 4},
        "10": {"11": 6},
        "11": {"10": 2},
    }
    path, distance = deykstra(graph, "1", "11")
    assert path == ["1", "2", "7", "8", "10", "11"]
    assert distance == 16


