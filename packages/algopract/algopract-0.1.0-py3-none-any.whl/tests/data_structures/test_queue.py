from algopract.data_structures.queue import run_queue_operations


def test_queue_operations():
    ops = [
        ("enqueue", 1),
        ("enqueue", 2),
        ("peek",),
        ("dequeue",),
        ("dequeue",)
    ]

    result = run_queue_operations(ops)
    assert result["result"] == [None, None, 1, 1, 2]
