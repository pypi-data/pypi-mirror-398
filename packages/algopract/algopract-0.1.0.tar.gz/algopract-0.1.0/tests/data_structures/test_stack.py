from algopract.data_structures.stack import run_stack_operations


def test_stack_operations():
    ops = [
        ("push", 10),
        ("push", 20),
        ("peek",),
        ("pop",),
        ("pop",)
    ]

    result = run_stack_operations(ops)
    assert result["result"] == [None, None, 20, 20, 10]
