# Choke Point

## Category

Coding

## Difficulty

Insane

## Challenge Description

Anika has been staring at the dependency map long enough to see the shape underneath it. Not every node matters equally — some are load-bearing in a way the architects never documented. Take one out and an entire cluster of platforms loses its only route to the source, going dark without a single additional strike.

**Creator:** Xclow3n

## Summary

Given a dependency DAG with a designated root, identify the non-root node whose removal causes the largest number of other nodes to lose reachability from the root. This is the dominator tree problem: the answer is the non-root node with the largest dominator subtree.

## Provided Files

None (Docker instance only).

## Tools Used

- Python 3
- Lengauer-Tarjan dominator tree algorithm

## Walkthrough

1. Parse the graph and root node from input. Build an adjacency list for the forward graph and a reverse adjacency list for the DFS parent computation.

2. Run a DFS from the root to assign DFS discovery order (the `semi` array indexed by DFS number), record DFS parents, and map between vertex labels and DFS numbers.

3. Compute semi-dominators using the Lengauer-Tarjan `eval` and `link` functions with path compression. For each vertex w in reverse DFS order, iterate over all predecessors v of w; the semi-dominator of w is the minimum DFS number reachable via a path whose intermediate nodes all have higher DFS numbers than that minimum.

4. Use the bucket-based algorithm to compute immediate dominators: for each vertex w in reverse DFS order, assign `idom[w]` based on whether the semi-dominator ancestor equals the semi-dominator of w, or propagate through the idom chain.

5. Build the dominator tree from the `idom` array. Compute subtree sizes with a post-order traversal.

6. The answer is the maximum subtree size among all non-root nodes. This equals the number of nodes that the critical node dominates, i.e., the count that lose connectivity if it is removed.

```python
import sys
from collections import defaultdict

def solve():
    data = sys.stdin.read().split()
    idx = 0
    N = int(data[idx]); idx += 1
    E = int(data[idx]); idx += 1
    root = int(data[idx]); idx += 1

    succ = defaultdict(list)
    pred = defaultdict(list)
    for _ in range(E):
        u = int(data[idx]); idx += 1
        v = int(data[idx]); idx += 1
        succ[u].append(v)
        pred[v].append(u)

    # Lengauer-Tarjan
    n = N
    vertex = [0] * (n + 1)   # DFS order -> node
    parent = [0] * (n + 1)   # DFS parent (by DFS order)
    semi = [0] * (n + 1)     # semi-dominator (DFS number)
    idom = [0] * (n + 1)
    ancestor = [0] * (n + 1)
    best = list(range(n + 1))
    bucket = defaultdict(list)

    # Use explicit stack DFS to avoid recursion limit
    dfs_num = [0] * (n + 1)
    visited = [False] * (n + 1)
    timer = [0]
    stack = [(root, 0)]
    visited[root] = True
    order = []
    par = [0] * (n + 1)

    while stack:
        u, state = stack.pop()
        if state == 0:
            timer[0] += 1
            dfs_num[u] = timer[0]
            semi[timer[0]] = timer[0]
            vertex[timer[0]] = u
            order.append(u)
            stack.append((u, 1))
            for v in succ[u]:
                if not visited[v]:
                    visited[v] = True
                    par[v] = u
                    stack.append((v, 0))

    total = timer[0]

    # Map node -> dfs index
    w_of = dfs_num  # dfs_num[node] = dfs index

    def compress(v):
        if ancestor[v] != 0 and ancestor[ancestor[v]] != 0:
            compress(ancestor[v])
            if semi[best[ancestor[v]]] < semi[best[v]]:
                best[v] = best[ancestor[v]]
            ancestor[v] = ancestor[ancestor[v]]

    def eval_lt(v):
        if ancestor[v] == 0:
            return v
        compress(v)
        return best[v]

    def link_lt(u, v):
        ancestor[v] = u

    # Process in reverse DFS order
    for i in range(total, 0, -1):
        w = vertex[i]
        w_idx = i
        # Compute semi-dominator
        for v in pred[w]:
            if w_of[v] == 0:
                continue  # v not reachable
            u = eval_lt(w_of[v])
            if semi[u] < semi[w_idx]:
                semi[w_idx] = semi[u]
        bucket[vertex[semi[w_idx]]].append(w)
        p = par[w]
        if p:
            link_lt(w_of[p], w_idx)
        # Process bucket of parent
        for v in bucket[p]:
            u = eval_lt(w_of[v])
            idom[w_of[v]] = w_of[p] if semi[u] >= semi[w_of[p]] else u
        bucket[p].clear()

    # Finalize idoms
    for i in range(2, total + 1):
        w = vertex[i]
        if idom[i] != semi[i]:
            idom[i] = idom[idom[i]]

    # Build dominator tree and compute subtree sizes
    dom_children = defaultdict(list)
    for i in range(2, total + 1):
        dom_children[idom[i]].append(i)

    subtree_size = [1] * (total + 1)
    # Post-order
    topo = []
    stk = [1]
    while stk:
        u = stk.pop()
        topo.append(u)
        for c in dom_children[u]:
            stk.append(c)
    for u in reversed(topo):
        for c in dom_children[u]:
            subtree_size[u] += subtree_size[c]

    ans = max(subtree_size[i] for i in range(2, total + 1)) if total > 1 else 0
    print(ans)

solve()
```

## Key Findings

- Articulation-point algorithms do not apply here because the graph is directed; a node can be a dominator without being an undirected bridge.
- Lengauer-Tarjan computes all immediate dominators in O((V + E) log V) using semi-dominator theory and path-compressed ancestor queries.
- The subtree size of a node in the dominator tree equals exactly the count of nodes that require it as an intermediary on every path from the root, making it the direct measure of impact upon removal.
- Iterative DFS with an explicit stack is necessary in Python to avoid hitting the default recursion limit on large inputs.

## Final Answer

`Flag: HTB{l3nGu3r_t4rj4n_ch0k3_p01nt_f0und}`

## Lessons Learned

Finding critical nodes in a directed graph requires dominator tree analysis rather than the articulation-point or bridge algorithms that apply to undirected graphs. Lengauer-Tarjan is the standard O((V + E) log V) solution and is worth implementing from scratch for this problem class.
