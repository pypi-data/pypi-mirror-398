from algopract.core.profiler import measure_time
from algopract.core.result import build_result


def _interpolation_search(arr, target, explain=False):
    steps = []
    low = 0
    high = len(arr) - 1

    if explain:
        steps.append(
            f"Starting interpolation search on array of size {len(arr)}"
        )

    while low <= high and arr[low] <= target <= arr[high]:
        if arr[high] == arr[low]:
            break

        pos = low + int(
            ((target - arr[low]) * (high - low)) /
            (arr[high] - arr[low])
        )

        if explain:
            steps.append(
                f"low={low}, high={high}, pos={pos}, arr[pos]={arr[pos]}"
            )

        if arr[pos] == target:
            if explain:
                steps.append(f"Target {target} found at index {pos}")
            return pos, steps

        if arr[pos] < target:
            low = pos + 1
            if explain:
                steps.append(
                    f"Target greater than {arr[pos]} → move low to {low}"
                )
        else:
            high = pos - 1
            if explain:
                steps.append(
                    f"Target smaller than {arr[pos]} → move high to {high}"
                )

    if explain:
        steps.append(f"Target {target} not found in array")

    return -1, steps


def run_interpolation_search(arr, target, explain=False, profile=False):
    """
    Performs Interpolation Search on a sorted array.

    Average Time Complexity: O(log log n)
    Worst Case: O(n)
    Space Complexity: O(1)
    """

    if profile:
        (result, steps), exec_time = measure_time(
            _interpolation_search, arr, target, explain
        )
    else:
        result, steps = _interpolation_search(arr, target, explain)
        exec_time = None

    return build_result(
        algorithm="Interpolation Search",
        result=result,
        steps=steps if explain else None,
        execution_time_ms=round(exec_time, 3) if exec_time is not None else None,
        expected_complexity="O(log log n) (avg), O(n) (worst)"
    )
