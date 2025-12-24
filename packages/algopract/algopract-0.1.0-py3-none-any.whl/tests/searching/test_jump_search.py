from algopract.searching.jump_search import run_jump_search


def test_jump_search_found():
    data = [1, 3, 5, 7, 9, 11, 13, 15]
    result = run_jump_search(data, 11)
    assert result["result"] == 5


def test_jump_search_not_found():
    data = [2, 4, 6, 8, 10]
    result = run_jump_search(data, 7)
    assert result["result"] == -1
