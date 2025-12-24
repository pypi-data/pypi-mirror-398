from algopract.core.profiler import measure_time
from algopract.core.result import build_result


def _binary_search(arr, target, explain=False):
    steps = []
    low = 0
    high = len(arr) - 1

    if explain:
        steps.append(
            f"Starting binary search on array of size {len(arr)}"
        )

    while low <= high:
        mid = (low + high) // 2

        if explain:
            steps.append(
                f"low={low}, high={high}, mid={mid}, arr[mid]={arr[mid]}"
            )

        if arr[mid] == target:
            if explain:
                steps.append(f"Target {target} found at index {mid}")
            return mid, steps

        elif arr[mid] < target:
            low = mid + 1
            if explain:
                steps.append(
                    f"Target greater than {arr[mid]} → move low to {low}"
                )
        else:
            high = mid - 1
            if explain:
                steps.append(
                    f"Target smaller than {arr[mid]} → move high to {high}"
                )

    if explain:
        steps.append(f"Target {target} not found in array")

    return -1, steps


def run_binary_search(arr, target, explain=False, profile=False):
    """
    Performs Binary Search on a sorted array.

    Time Complexity: O(log n)
    Space Complexity: O(1)
    """

    if profile:
        (result, steps), exec_time = measure_time(
            _binary_search, arr, target, explain
        )
    else:
        result, steps = _binary_search(arr, target, explain)
        exec_time = None

    return build_result(
        algorithm="Binary Search",
        result=result,
        steps=steps if explain else None,
        execution_time_ms=round(exec_time, 3) if exec_time is not None else None,
        expected_complexity="O(log n)"
    )
