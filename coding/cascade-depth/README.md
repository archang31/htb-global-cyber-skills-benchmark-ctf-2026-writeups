# Cascade Depth

## Category

Coding

## Difficulty

Medium

## Challenge Description

Anika's dependency mapper has traced the vendor graph and found chains of trust that nobody ever audited. A single compromised supplier can propagate exposure silently through every platform that depends on it — and the question is how deep that cascade can run.

**Creator:** Xclow3n

## Summary

Given a weighted directed acyclic graph representing a compromised vendor dependency graph, find the longest weighted path from any source node. The answer reflects how deep a cascade of exposure can propagate from a single compromised supplier.

## Provided Files

None (Docker instance only).

## Tools Used

- Python 3
- `collections.deque` for BFS queue

## Walkthrough

1. Parse the first line to read N (nodes) and V (edges). Parse V subsequent lines, each containing `from to weight`, and build an adjacency list. Simultaneously compute the in-degree of every node.

2. Initialize a DP array `dp` of size N with all zeros. `dp[v]` will hold the maximum weighted path length ending at node v.

3. Seed the BFS queue with every node whose in-degree is zero (sources with no predecessors).

4. Process each node u dequeued in topological order: for each outgoing edge `(u, v, w)`, apply the relaxation `dp[v] = max(dp[v], dp[u] + w)`. Decrement the in-degree of v; when it reaches zero, enqueue v.

5. The answer is `max(dp)`.

The algorithm is Kahn's topological sort combined with a single-pass DP relaxation, running in O(V + E) time.

```python
import sys
from collections import deque

def solve():
    input_data = sys.stdin.read().split()
    idx = 0
    N = int(input_data[idx]); idx += 1
    V = int(input_data[idx]); idx += 1

    adj = [[] for _ in range(N)]
    indegree = [0] * N

    for _ in range(V):
        u = int(input_data[idx]); idx += 1
        v = int(input_data[idx]); idx += 1
        w = int(input_data[idx]); idx += 1
        adj[u].append((v, w))
        indegree[v] += 1

    dp = [0] * N
    queue = deque(i for i in range(N) if indegree[i] == 0)

    while queue:
        u = queue.popleft()
        for v, w in adj[u]:
            if dp[u] + w > dp[v]:
                dp[v] = dp[u] + w
            indegree[v] -= 1
            if indegree[v] == 0:
                queue.append(v)

    print(max(dp))

solve()
```

## Key Findings

- Because the graph is a DAG, topological ordering guarantees that when node u is processed, all paths leading to u have already been finalized, making the DP relaxation exact.
- In-degree tracking via Kahn's algorithm eliminates the need for a separate DFS-based topological sort.
- A single pass over all edges suffices; no re-relaxation is required.

## Final Answer

`Flag: HTB{c4sc4d3_d3pth_d4g_dp_0pt1m4l}`

## Lessons Learned

Longest path in a DAG is solvable in linear time by combining Kahn's topological sort with a forward DP relaxation. The critical property is that a DAG guarantees each node is processed only after all its predecessors, so every relaxation is permanent when applied.
