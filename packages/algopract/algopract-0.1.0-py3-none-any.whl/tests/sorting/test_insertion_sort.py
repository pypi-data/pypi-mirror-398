from algopract.sorting.insertion_sort import run_insertion_sort


def test_insertion_sort_basic():
    data = [12, 11, 13, 5, 6]
    result = run_insertion_sort(data)
    assert result["result"] == [5, 6, 11, 12, 13]


def test_insertion_sort_sorted():
    data = [1, 2, 3]
    result = run_insertion_sort(data)
    assert result["result"] == [1, 2, 3]
