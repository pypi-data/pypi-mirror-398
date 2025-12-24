# algopract

algopract is a learning-focused Python package that implements core algorithms
with optional step-by-step explanations and execution-time profiling.

It is designed to help understand *how* algorithms work internally,
not just produce final results.

---

## Installation

```bash
pip install algopract
```

### For local development:

```
pip install -e .
```

## Usage
## Searching Example

```from algopract import run_binary_search

result = run_binary_search(
    [1, 2, 3, 4, 5],
    3,
    explain=True,
    profile=True
)

print(result)
```


## Output format:
```
{
  "algorithm": "Binary Search",
  "result": 2,
  "steps": [...],
  "execution_time_ms": 0.012,
  "expected_complexity": "O(log n)"
}
```
# Sorting Example
```
from algopract import run_quick_sort

result = run_quick_sort([3, 1, 2])
print(result["result"])
```
## Graph Traversal Example
```
from algopract import run_bfs

graph = {
    "A": ["B", "C"],
    "B": ["D"],
    "C": [],
    "D": []
}

result = run_bfs(graph, "A")
print(result["result"])
```
## Design Principles

Algorithms return structured data, not printed output

Explanation and profiling are optional

Consistent API across all algorithms

Core logic is separated from presentation

This makes the library suitable for scripts, notebooks,
CLI tools, and future UI or visualization layers.

## Included Algorithms

Searching: Linear, Binary, Jump, Interpolation

Sorting: Bubble, Selection, Insertion, Merge, Quick

Data Structures: Stack, Queue

Graphs: BFS, DFS
