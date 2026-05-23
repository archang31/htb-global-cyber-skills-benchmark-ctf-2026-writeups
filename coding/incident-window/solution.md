# Incident Window

## Category

Coding

## Difficulty

Easy

## Summary

Given a stream of timestamped authentication events, count how many 1-second-aligned windows of width W contain at least K suspicious events. The approach uses a prefix sum over a count array indexed by integer timestamp, enabling O(1) per-window queries after an O(N) build phase.

## Provided Files

None (Docker instance only).

## Tools Used

- Python 3

## Walkthrough

1. Read N, W, and K from the first line of input.

2. Allocate a count array of size 10001 (covering all valid integer timestamps). For each of the N events, parse the timestamp and type. If the type is `S` (suspicious), increment `count[timestamp]`.

3. Build a prefix sum array of size 10002 where `prefix[i+1] = prefix[i] + count[i]`. This allows the number of suspicious events in any half-open interval `[t, t+W)` to be computed as `prefix[t+W] - prefix[t]` in O(1).

4. Iterate over every anchor timestamp t from 0 to `10000 - W` inclusive. If `prefix[t+W] - prefix[t] >= K`, increment the answer counter.

5. Print the answer.

```python
n, w, k = map(int, input().split())
count = [0] * 10001
for _ in range(n):
    ts, typ = input().split()
    if typ == 'S':
        count[int(ts)] += 1

prefix = [0] * 10002
for i in range(10001):
    prefix[i+1] = prefix[i] + count[i]

ans = 0
for t in range(10001 - w):
    if prefix[t+w] - prefix[t] >= k:
        ans += 1
print(ans)
```

Total time complexity is O(N + T) where T = 10001 is the timestamp range. With N up to 50,000 and T fixed, this easily fits within any reasonable time limit.

## Key Findings

- Because timestamps are bounded integers (not arbitrary floats), a dense count array is more efficient than a sorted event list with binary-search range queries.
- A prefix sum collapses every window query to two array accesses and one subtraction, making the exhaustive scan over all anchor points trivial.
- The two-pointer (sliding window) technique would also work but requires more bookkeeping; prefix sums are simpler when the range is fixed and all anchors must be evaluated.

## Final Answer

`Flag: HTB{sl1d3_th3_w1nd0w_s1l3nc3_th3_n0d3}`

## Lessons Learned

Sliding window problems over fixed integer ranges are best solved with prefix sums rather than two-pointer techniques, as the range is bounded and queries are exhaustive. Building the prefix array costs O(T) regardless of N, so the approach remains efficient even when N is small relative to T.
