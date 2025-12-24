from algopract.core.profiler import measure_time
from algopract.core.result import build_result


def _merge(left, right, steps, explain):
    result = []
    i = j = 0

    while i < len(left) and j < len(right):
        if explain:
            steps.append(f"Comparing {left[i]} and {right[j]}")

        if left[i] <= right[j]:
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            j += 1

    result.extend(left[i:])
    result.extend(right[j:])

    if explain:
        steps.append(f"Merged → {result}")

    return result


def _merge_sort(arr, steps, explain):
    if len(arr) <= 1:
        return arr

    mid = len(arr) // 2
    left = _merge_sort(arr[:mid], steps, explain)
    right = _merge_sort(arr[mid:], steps, explain)

    return _merge(left, right, steps, explain)


def run_merge_sort(arr, explain=False, profile=False):
    """
    Merge Sort

    Time Complexity: O(n log n)
    Space Complexity: O(n)
    """

    def _run():
        steps = []
        result = _merge_sort(arr[:], steps, explain)
        return result, steps

    if profile:
        (result, steps), exec_time = measure_time(_run)
    else:
        result, steps = _run()
        exec_time = None

    return build_result(
        algorithm="Merge Sort",
        result=result,
        steps=steps if explain else None,
        execution_time_ms=round(exec_time, 3) if exec_time is not None else None,
        expected_complexity="O(n log n)"
    )
