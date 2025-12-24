from collections import deque
from algopract.core.profiler import measure_time
from algopract.core.result import build_result


class Queue:
    def __init__(self):
        self._items = deque()

    def enqueue(self, value):
        self._items.append(value)

    def dequeue(self):
        if not self._items:
            raise IndexError("Dequeue from empty queue")
        return self._items.popleft()

    def peek(self):
        if not self._items:
            raise IndexError("Peek from empty queue")
        return self._items[0]

    def is_empty(self):
        return len(self._items) == 0


def run_queue_operations(operations, explain=False, profile=False):
    """
    Queue Operations

    Time Complexity:
    enqueue, dequeue, peek → O(1)
    """

    def _run():
        steps = []
        queue = Queue()
        results = []

        for op in operations:
            action = op[0]

            if action == "enqueue":
                queue.enqueue(op[1])
                results.append(None)
                if explain:
                    steps.append(f"Enqueued {op[1]} → {list(queue._items)}")

            elif action == "dequeue":
                val = queue.dequeue()
                results.append(val)
                if explain:
                    steps.append(f"Dequeued {val} → {list(queue._items)}")

            elif action == "peek":
                val = queue.peek()
                results.append(val)
                if explain:
                    steps.append(f"Peeked {val}")

        return results, steps

    if profile:
        (result, steps), exec_time = measure_time(_run)
    else:
        result, steps = _run()
        exec_time = None

    return build_result(
        algorithm="Queue",
        result=result,
        steps=steps if explain else None,
        execution_time_ms=round(exec_time, 3) if exec_time is not None else None,
        expected_complexity="O(1) per operation"
    )
