from algopract.core.profiler import measure_time
from algopract.core.result import build_result


def _partition(a, low, high, steps, explain):
    pivot = a[high]
    i = low - 1

    if explain:
        steps.append(f"Pivot chosen: {pivot} at index {high}")

    for j in range(low, high):
        if explain:
            steps.append(f"Comparing a[{j}]={a[j]} with pivot {pivot}")
        if a[j] <= pivot:
            i += 1
            a[i], a[j] = a[j], a[i]
            if explain:
                steps.append(f"Swapped a[{i}] and a[{j}] → {a}")

    a[i + 1], a[high] = a[high], a[i + 1]
    if explain:
        steps.append(f"Placed pivot at index {i + 1} → {a}")

    return i + 1


def _quick_sort(a, low, high, steps, explain):
    if low < high:
        pi = _partition(a, low, high, steps, explain)
        _quick_sort(a, low, pi - 1, steps, explain)
        _quick_sort(a, pi + 1, high, steps, explain)


def run_quick_sort(arr, explain=False, profile=False):
    """
    Quick Sort

    Average Time Complexity: O(n log n)
    Worst Case: O(n^2)
    Space Complexity: O(log n) [recursion stack]
    """

    def _run():
        steps = []
        a = arr[:]
        _quick_sort(a, 0, len(a) - 1, steps, explain)
        return a, steps

    if profile:
        (result, steps), exec_time = measure_time(_run)
    else:
        result, steps = _run()
        exec_time = None

    return build_result(
        algorithm="Quick Sort",
        result=result,
        steps=steps if explain else None,
        execution_time_ms=round(exec_time, 3) if exec_time is not None else None,
        expected_complexity="O(n log n) avg, O(n^2) worst"
    )
