from algopract.sorting.selection_sort import run_selection_sort


def test_selection_sort_basic():
    data = [64, 25, 12, 22, 11]
    result = run_selection_sort(data)
    assert result["result"] == [11, 12, 22, 25, 64]


def test_selection_sort_single():
    result = run_selection_sort([3])
    assert result["result"] == [3]
