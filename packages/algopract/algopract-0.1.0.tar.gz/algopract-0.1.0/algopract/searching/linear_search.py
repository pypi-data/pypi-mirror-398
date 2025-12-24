from algopract.core.profiler import measure_time
from algopract.core.result import build_result


def _linear_search(arr, target, explain=False):
    steps = []

    for index, value in enumerate(arr):
        if explain:
            steps.append(
                f"Checking index {index}: value {value}"
            )

        if value == target:
            if explain:
                steps.append(f"Target {target} found at index {index}")
            return index, steps

    if explain:
        steps.append(f"Target {target} not found in array")

    return -1, steps


def run_linear_search(arr, target, explain=False, profile=False):
    """
    Performs Linear Search on the given array.

    Time Complexity: O(n)
    Space Complexity: O(1)
    """

    if profile:
        (result, steps), exec_time = measure_time(
            _linear_search, arr, target, explain
        )
    else:
        result, steps = _linear_search(arr, target, explain)
        exec_time = None

    return build_result(
        algorithm="Linear Search",
        result=result,
        steps=steps if explain else None,
        execution_time_ms=round(exec_time, 3) if exec_time is not None else None,
        expected_complexity="O(n)"
    )
