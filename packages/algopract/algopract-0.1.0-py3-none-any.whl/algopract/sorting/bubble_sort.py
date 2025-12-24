from algopract.core.profiler import measure_time
from algopract.core.result import build_result


def _bubble_sort(arr, explain=False):
    steps = []
    a = arr[:]
    n = len(a)

    for i in range(n):
        if explain:
            steps.append(f"Pass {i+1}")
        swapped = False

        for j in range(0, n - i - 1):
            if explain:
                steps.append(f"Comparing a[{j}]={a[j]} and a[{j+1}]={a[j+1]}")
            if a[j] > a[j + 1]:
                a[j], a[j + 1] = a[j + 1], a[j]
                swapped = True
                if explain:
                    steps.append(f"Swapped → {a}")

        if not swapped:
            if explain:
                steps.append("No swaps in this pass → array is sorted")
            break

    return a, steps


def run_bubble_sort(arr, explain=False, profile=False):
    """
    Bubble Sort

    Time Complexity: O(n^2)
    Space Complexity: O(1)
    """

    if profile:
        (result, steps), exec_time = measure_time(
            _bubble_sort, arr, explain
        )
    else:
        result, steps = _bubble_sort(arr, explain)
        exec_time = None

    return build_result(
        algorithm="Bubble Sort",
        result=result,
        steps=steps if explain else None,
        execution_time_ms=round(exec_time, 3) if exec_time is not None else None,

        expected_complexity="O(n^2)"
    )
