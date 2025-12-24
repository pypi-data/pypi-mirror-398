from algopract.graphs.dfs import run_dfs


def test_dfs_basic():
    graph = {
        "A": ["B", "C"],
        "B": ["D"],
        "C": ["E"],
        "D": [],
        "E": []
    }

    result = run_dfs(graph, "A")
    assert result["result"] == ["A", "B", "D", "C", "E"]
