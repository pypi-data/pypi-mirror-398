from algopract.core.profiler import measure_time
from algopract.core.result import build_result


def _selection_sort(arr, explain=False):
    steps = []
    a = arr[:]
    n = len(a)

    for i in range(n):
        min_idx = i
        if explain:
            steps.append(f"Selecting minimum from index {i} to {n-1}")

        for j in range(i + 1, n):
            if explain:
                steps.append(f"Comparing a[{j}]={a[j]} with current min a[{min_idx}]={a[min_idx]}")
            if a[j] < a[min_idx]:
                min_idx = j
                if explain:
                    steps.append(f"New minimum found at index {min_idx}")

        if min_idx != i:
            a[i], a[min_idx] = a[min_idx], a[i]
            if explain:
                steps.append(f"Swapped index {i} with min index {min_idx} → {a}")

    return a, steps


def run_selection_sort(arr, explain=False, profile=False):
    """
    Selection Sort

    Time Complexity: O(n^2)
    Space Complexity: O(1)
    """

    if profile:
        (result, steps), exec_time = measure_time(
            _selection_sort, arr, explain
        )
    else:
        result, steps = _selection_sort(arr, explain)
        exec_time = None

    return build_result(
        algorithm="Selection Sort",
        result=result,
        steps=steps if explain else None,
        execution_time_ms=round(exec_time, 3) if exec_time is not None else None,
        expected_complexity="O(n^2)"
    )
