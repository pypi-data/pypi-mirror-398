from algopract.core.profiler import measure_time
from algopract.core.result import build_result


def _insertion_sort(arr, explain=False):
    steps = []
    a = arr[:]

    for i in range(1, len(a)):
        key = a[i]
        j = i - 1

        if explain:
            steps.append(f"Inserting element {key} at position {i}")

        while j >= 0 and a[j] > key:
            if explain:
                steps.append(f"{a[j]} > {key} → shifting {a[j]} to the right")
            a[j + 1] = a[j]
            j -= 1

        a[j + 1] = key
        if explain:
            steps.append(f"Placed {key} at position {j + 1} → {a}")

    return a, steps


def run_insertion_sort(arr, explain=False, profile=False):
    """
    Insertion Sort

    Time Complexity: O(n^2)
    Best Case: O(n)
    Space Complexity: O(1)
    """

    if profile:
        (result, steps), exec_time = measure_time(
            _insertion_sort, arr, explain
        )
    else:
        result, steps = _insertion_sort(arr, explain)
        exec_time = None

    return build_result(
        algorithm="Insertion Sort",
        result=result,
        steps=steps if explain else None,
        execution_time_ms=round(exec_time, 3) if exec_time is not None else None,
        expected_complexity="O(n^2)"
    )
