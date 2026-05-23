# Surge Protocol

## Category

Coding

## Difficulty

Hard

## Summary

Track urgency levels across thousands of infrastructure sensors in real time. The server sends interleaved range-update (add a value to all elements in [l, r]) and range-query (maximum over [l, r]) operations that must be answered online. A segment tree with lazy propagation solves both operation types in O(log N) each.

## Provided Files

None (Docker instance only).

## Tools Used

- Python 3
- Segment tree with lazy propagation (hand-rolled)

## Walkthrough

1. Read N (number of sensors) and Q (number of operations).

2. Build a segment tree over N leaf nodes. Each internal node stores the maximum value in its range. A parallel lazy array stores pending additive increments that have not yet been pushed to children.

3. For each update operation `U l r val`: apply range addition on `[l, r]` using lazy propagation. When a segment is fully covered by `[l, r]`, accumulate `val` into its lazy tag and add `val` to its stored maximum (since all values in the segment increase by `val`, the maximum increases by the same amount). When a segment is partially covered, push the current lazy value down to the two children before recursing.

4. For each query operation `Q l r`: return the maximum over `[l, r]`. Push lazy values down at each node before descending into children. Combine results from left and right subtrees by taking the maximum.

5. Print each query answer on its own line.

```python
import sys
input = sys.stdin.readline

def main():
    data = sys.stdin.buffer.read().split()
    idx = 0
    N = int(data[idx]); idx += 1
    Q = int(data[idx]); idx += 1

    size = 1
    while size < N:
        size <<= 1

    tree = [0] * (2 * size)
    lazy = [0] * (2 * size)

    def push_down(node):
        if lazy[node]:
            for child in (2 * node, 2 * node + 1):
                tree[child] += lazy[node]
                lazy[child] += lazy[node]
            lazy[node] = 0

    def update(node, node_l, node_r, l, r, val):
        if r < node_l or node_r < l:
            return
        if l <= node_l and node_r <= r:
            tree[node] += val
            lazy[node] += val
            return
        push_down(node)
        mid = (node_l + node_r) >> 1
        update(2 * node, node_l, mid, l, r, val)
        update(2 * node + 1, mid + 1, node_r, l, r, val)
        tree[node] = max(tree[2 * node], tree[2 * node + 1])

    def query(node, node_l, node_r, l, r):
        if r < node_l or node_r < l:
            return 0
        if l <= node_l and node_r <= r:
            return tree[node]
        push_down(node)
        mid = (node_l + node_r) >> 1
        return max(
            query(2 * node, node_l, mid, l, r),
            query(2 * node + 1, mid + 1, node_r, l, r)
        )

    out = []
    for _ in range(Q):
        op = data[idx]; idx += 1
        l = int(data[idx]); idx += 1
        r = int(data[idx]); idx += 1
        if op == b'U':
            val = int(data[idx]); idx += 1
            update(1, 0, size - 1, l, r, val)
        else:
            out.append(query(1, 0, size - 1, l, r))

    sys.stdout.write('\n'.join(map(str, out)) + '\n')

main()
```

For large N and Q (up to 10^5 each), the recursion depth may approach Python's default limit. If needed, set `sys.setrecursionlimit` accordingly, or rewrite the tree operations iteratively.

## Key Findings

- Lazy propagation defers propagation of range updates by storing pending values at internal nodes. The invariant is that `tree[node]` already reflects the pending value for that node's range, but children have not yet been updated.
- Pushing lazy values down before any descent into children preserves correctness without materializing all O(N) leaf updates eagerly.
- A naive O(N) update per operation would produce O(N * Q) total work, timing out for N = Q = 10^5. The segment tree reduces this to O(Q log N).
- Reading all input at once via `sys.stdin.buffer.read()` is important in Python to avoid per-line I/O overhead on large inputs.

## Final Answer

`Flag: HTB{l4zy_s3g_surG3_pr0t0c0l_p4ss3d}`

## Lessons Learned

Range update combined with range maximum query requires lazy propagation on a segment tree. Understanding that the lazy tag encodes a pending additive offset, and that pushing it down before any child access is sufficient to maintain correctness, is the key insight that separates this from a simpler point-update segment tree.
