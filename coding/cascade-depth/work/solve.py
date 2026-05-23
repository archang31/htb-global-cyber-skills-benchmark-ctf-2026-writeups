import sys
from collections import deque

input = sys.stdin.readline

def solve():
    V, E = map(int, input().split())
    graph = [[] for _ in range(V)]
    indegree = [0] * V

    for _ in range(E):
        u, v, w = map(int, input().split())
        graph[u].append((v, w))
        indegree[v] += 1

    dp = [0] * V
    queue = deque(i for i in range(V) if indegree[i] == 0)

    while queue:
        u = queue.popleft()
        for v, w in graph[u]:
            if dp[u] + w > dp[v]:
                dp[v] = dp[u] + w
            indegree[v] -= 1
            if indegree[v] == 0:
                queue.append(v)

    print(max(dp))

solve()
