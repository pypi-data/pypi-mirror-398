from algopract.sorting.quick_sort import run_quick_sort


def test_quick_sort_basic():
    data = [10, 7, 8, 9, 1, 5]
    result = run_quick_sort(data)
    assert result["result"] == sorted(data)


def test_quick_sort_empty():
    result = run_quick_sort([])
    assert result["result"] == []


def test_quick_sort_duplicates():
    data = [3, 3, 2, 1, 2]
    result = run_quick_sort(data)
    assert result["result"] == sorted(data)
