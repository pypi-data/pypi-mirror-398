from algopract.core.profiler import measure_time
from algopract.core.result import build_result


def _dfs(node, graph, visited, order, steps, explain):
    visited.add(node)
    order.append(node)

    if explain:
        steps.append(f"Visited {node}")

    for neighbor in graph.get(node, []):
        if neighbor not in visited:
            if explain:
                steps.append(f"Going deeper from {node} to {neighbor}")
            _dfs(neighbor, graph, visited, order, steps, explain)


def _dfs_runner(graph, start, explain=False):
    visited = set()
    order = []
    steps = []

    if explain:
        steps.append(f"Starting DFS from node {start}")

    _dfs(start, graph, visited, order, steps, explain)
    return order, steps


def run_dfs(graph, start, explain=False, profile=False):
    """
    Depth-First Search (DFS)

    Time Complexity: O(V + E)
    Space Complexity: O(V)
    """

    if profile:
        (result, steps), exec_time = measure_time(
            _dfs_runner, graph, start, explain
        )
    else:
        result, steps = _dfs_runner(graph, start, explain)
        exec_time = None

    return build_result(
        algorithm="Depth-First Search",
        result=result,
        steps=steps if explain else None,
        execution_time_ms=round(exec_time, 3) if exec_time is not None else None,
        expected_complexity="O(V + E)"
    )
