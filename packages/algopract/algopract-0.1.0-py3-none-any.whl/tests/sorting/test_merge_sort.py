from algopract.sorting.merge_sort import run_merge_sort


def test_merge_sort_basic():
    data = [38, 27, 43, 3, 9, 82, 10]
    result = run_merge_sort(data)
    assert result["result"] == sorted(data)


def test_merge_sort_empty():
    result = run_merge_sort([])
    assert result["result"] == []
