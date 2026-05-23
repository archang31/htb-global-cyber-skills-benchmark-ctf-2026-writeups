import sys
from collections import defaultdict

def solve():
    data = sys.stdin.read().split()
    idx = 0
    V = int(data[idx]); idx += 1
    E = int(data[idx]); idx += 1
    S = int(data[idx]); idx += 1

    succ = [[] for _ in range(V)]
    pred = [[] for _ in range(V)]

    for _ in range(E):
        u = int(data[idx]); idx += 1
        v = int(data[idx]); idx += 1
        succ[u].append(v)
        pred[v].append(u)

    # DFS to number vertices
    dfnum = [-1] * V
    vertex = []
    parent = [-1] * V

    dfnum[S] = 0
    vertex.append(S)
    counter = 1

    stack = [(S, iter(succ[S]))]
    while stack:
        node, it = stack[-1]
        w = next(it, None)
        if w is None:
            stack.pop()
        elif dfnum[w] == -1:
            dfnum[w] = counter
            vertex.append(w)
            parent[w] = node
            counter += 1
            stack.append((w, iter(succ[w])))

    n = counter

    # Lengauer-Tarjan semi-dominator / idom computation
    semi = list(range(V))
    idom = [-1] * V
    ancestor = [-1] * V
    best = list(range(V))
    bucket = [[] for _ in range(V)]

    def compress(v):
        path = []
        x = v
        while ancestor[x] != -1 and ancestor[ancestor[x]] != -1:
            path.append(x)
            x = ancestor[x]
        for node in reversed(path):
            anc = ancestor[node]
            if dfnum[semi[best[anc]]] < dfnum[semi[best[node]]]:
                best[node] = best[anc]
            ancestor[node] = ancestor[anc]

    def eval_node(v):
        if ancestor[v] == -1:
            return best[v]
        compress(v)
        return best[v]

    for i in range(n - 1, 0, -1):
        w = vertex[i]
        p = parent[w]

        for v in pred[w]:
            if dfnum[v] == -1:
                continue
            u = eval_node(v)
            if dfnum[semi[u]] < dfnum[semi[w]]:
                semi[w] = semi[u]

        bucket[semi[w]].append(w)
        ancestor[w] = p  # link

        for v in bucket[p]:
            u = eval_node(v)
            if dfnum[semi[u]] < dfnum[semi[v]]:
                idom[v] = u
            else:
                idom[v] = p
        bucket[p].clear()

    for i in range(1, n):
        w = vertex[i]
        if idom[w] != semi[w]:
            idom[w] = idom[idom[w]]

    idom[S] = S

    # Build dominator tree and sum subtree sizes
    dom_children = [[] for _ in range(V)]
    for i in range(1, n):
        w = vertex[i]
        dom_children[idom[w]].append(w)

    subtree_size = [1] * V
    total = 0
    stack = [(S, False)]
    while stack:
        node, processed = stack.pop()
        if processed:
            for child in dom_children[node]:
                subtree_size[node] += subtree_size[child]
            total += subtree_size[node]
        else:
            stack.append((node, True))
            for child in dom_children[node]:
                stack.append((child, False))

    print(total)

solve()
