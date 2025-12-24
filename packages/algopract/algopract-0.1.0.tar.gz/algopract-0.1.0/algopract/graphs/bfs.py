from collections import deque
from algopract.core.profiler import measure_time
from algopract.core.result import build_result


def _bfs(graph, start, explain=False):
    visited = set()
    queue = deque([start])
    order = []
    steps = []

    if explain:
        steps.append(f"Starting BFS from node {start}")

    visited.add(start)

    while queue:
        node = queue.popleft()
        order.append(node)

        if explain:
            steps.append(f"Visited {node}, queue={list(queue)}")

        for neighbor in graph.get(node, []):
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append(neighbor)
                if explain:
                    steps.append(f"Added {neighbor} to queue")

    return order, steps


def run_bfs(graph, start, explain=False, profile=False):
    """
    Breadth-First Search (BFS)

    Time Complexity: O(V + E)
    Space Complexity: O(V)
    """

    if profile:
        (result, steps), exec_time = measure_time(
            _bfs, graph, start, explain
        )
    else:
        result, steps = _bfs(graph, start, explain)
        exec_time = None

    return build_result(
        algorithm="Breadth-First Search",
        result=result,
        steps=steps if explain else None,
        execution_time_ms=round(exec_time, 3) if exec_time is not None else None,
        expected_complexity="O(V + E)"
    )
