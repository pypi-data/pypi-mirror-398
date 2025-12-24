from algopract.searching.interpolation_search import run_interpolation_search


def test_interpolation_search_found():
    data = [10, 20, 30, 40, 50, 60]
    result = run_interpolation_search(data, 40)
    assert result["result"] == 3


def test_interpolation_search_not_found():
    data = [5, 15, 25, 35]
    result = run_interpolation_search(data, 20)
    assert result["result"] == -1
