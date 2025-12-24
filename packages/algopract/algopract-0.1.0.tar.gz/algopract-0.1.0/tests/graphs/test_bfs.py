from algopract.graphs.bfs import run_bfs


def test_bfs_basic():
    graph = {
        "A": ["B", "C"],
        "B": ["D"],
        "C": ["E"],
        "D": [],
        "E": []
    }

    result = run_bfs(graph, "A")
    assert result["result"] == ["A", "B", "C", "D", "E"]
