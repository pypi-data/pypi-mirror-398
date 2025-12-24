import math
from algopract.core.profiler import measure_time
from algopract.core.result import build_result


def _jump_search(arr, target, explain=False):
    steps = []
    n = len(arr)
    step = int(math.sqrt(n))
    prev = 0

    if explain:
        steps.append(f"Array size = {n}, jump step = {step}")

    while prev < n and arr[min(step, n) - 1] < target:
        if explain:
            steps.append(
                f"Jumping from index {prev} to {min(step, n) - 1}"
            )
        prev = step
        step += int(math.sqrt(n))
        if prev >= n:
            if explain:
                steps.append("Exceeded array bounds, target not found")
            return -1, steps

    if explain:
        steps.append(
            f"Linear search in block from index {prev} to {min(step, n) - 1}"
        )

    for i in range(prev, min(step, n)):
        if explain:
            steps.append(f"Checking index {i}: value {arr[i]}")
        if arr[i] == target:
            if explain:
                steps.append(f"Target {target} found at index {i}")
            return i, steps

    if explain:
        steps.append(f"Target {target} not found in array")

    return -1, steps


def run_jump_search(arr, target, explain=False, profile=False):
    """
    Performs Jump Search on a sorted array.

    Time Complexity: O(√n)
    Space Complexity: O(1)
    """

    if profile:
        (result, steps), exec_time = measure_time(
            _jump_search, arr, target, explain
        )
    else:
        result, steps = _jump_search(arr, target, explain)
        exec_time = None

    return build_result(
        algorithm="Jump Search",
        result=result,
        steps=steps if explain else None,
       execution_time_ms=round(exec_time, 3) if exec_time is not None else None,

        expected_complexity="O(√n)"
    )
