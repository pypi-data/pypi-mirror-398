from algopract.core.profiler import measure_time
from algopract.core.result import build_result


class Stack:
    def __init__(self):
        self._items = []

    def push(self, value):
        self._items.append(value)

    def pop(self):
        if not self._items:
            raise IndexError("Pop from empty stack")
        return self._items.pop()

    def peek(self):
        if not self._items:
            raise IndexError("Peek from empty stack")
        return self._items[-1]

    def is_empty(self):
        return len(self._items) == 0


def run_stack_operations(operations, explain=False, profile=False):
    """
    Stack Operations

    Time Complexity:
    push, pop, peek → O(1)
    """

    def _run():
        steps = []
        stack = Stack()
        results = []

        for op in operations:
            action = op[0]

            if action == "push":
                stack.push(op[1])
                results.append(None)
                if explain:
                    steps.append(f"Pushed {op[1]} → {stack._items}")

            elif action == "pop":
                val = stack.pop()
                results.append(val)
                if explain:
                    steps.append(f"Popped {val} → {stack._items}")

            elif action == "peek":
                val = stack.peek()
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
        algorithm="Stack",
        result=result,
        steps=steps if explain else None,
        execution_time_ms=round(exec_time, 3) if exec_time is not None else None,
        expected_complexity="O(1) per operation"
    )
