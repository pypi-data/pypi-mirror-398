from algopract.sorting.bubble_sort import run_bubble_sort


def test_bubble_sort_basic():
    data = [5, 1, 4, 2, 8]
    result = run_bubble_sort(data)
    assert result["result"] == [1, 2, 4, 5, 8]


def test_bubble_sort_empty():
    result = run_bubble_sort([])
    assert result["result"] == []
