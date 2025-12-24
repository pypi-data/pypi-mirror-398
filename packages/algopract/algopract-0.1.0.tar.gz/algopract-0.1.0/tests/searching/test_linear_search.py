from algopract.searching.linear_search import run_linear_search


def test_linear_search_found():
    data = [10, 20, 30, 40]
    result = run_linear_search(data, 30)
    assert result["result"] == 2


def test_linear_search_not_found():
    data = [1, 2, 3]
    result = run_linear_search(data, 5)
    assert result["result"] == -1
