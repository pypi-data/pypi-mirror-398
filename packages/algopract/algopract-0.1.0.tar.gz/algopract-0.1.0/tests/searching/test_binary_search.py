from algopract.searching.binary_search import run_binary_search


def test_binary_search_found():
    data = [2, 4, 6, 8, 10, 12]
    result = run_binary_search(data, 8)
    assert result["result"] == 3


def test_binary_search_not_found():
    data = [1, 3, 5, 7]
    result = run_binary_search(data, 6)
    assert result["result"] == -1
