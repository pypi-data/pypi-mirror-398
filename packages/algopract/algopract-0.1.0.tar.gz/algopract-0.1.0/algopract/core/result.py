def build_result(
    algorithm: str,
    result,
    steps=None,
    execution_time_ms=None,
    expected_complexity: str = ""
):
    data = {
    "algorithm": algorithm,
    "result": result,
    "steps": steps,
    "execution_time_ms": execution_time_ms,
    "expected_complexity": expected_complexity
}

    return {k: v for k, v in data.items() if v is not None}

