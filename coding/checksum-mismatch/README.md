# Checksum Mismatch

## Category

Coding

## Difficulty

Very Easy

## Challenge Description

Anika intercepts a firmware update batch destined for relay stations across the coalition's infrastructure. Someone has been quietly modifying packets in transit — altering payloads while leaving the metadata untouched to avoid triggering format checks.

During the opening hours of Project Nightfall, Anika's pipeline flags something subtle: packets arriving from a trusted firmware distribution node are passing format validation but failing silent integrity checks. Someone — or something — has been modifying payloads in transit and updating the metadata to look clean.

Each packet carries a byte payload and a stored checksum. The checksum is supposed to be the XOR of every byte in the payload. A mismatch means the packet was tampered with after it was signed.

Anika needs a count: how many packets in this batch are corrupted? The number feeds directly into the incident severity score and determines whether the distribution node gets quarantined before the next update cycle fires.

The first line contains a single integer N — the number of packets in the batch.

Each of the next N lines describes one packet with L+2 space-separated integers:
  L b0 b1 ... b(L-1) checksum

L is the number of bytes in the payload.
b0 through b(L-1) are the payload bytes, each in the range [0, 255].
checksum is the stored checksum byte, in the range [0, 255].

A packet is corrupted if its stored checksum does not equal the XOR of all its payload bytes.

Print a single integer: the number of corrupted packets in the batch.

Constraints:
- 1 <= N <= 10000
- 2 <= L <= 32
- 0 <= each byte <= 255
- 0 <= checksum <= 255

**Creator:** Xclow3n

## Summary

A firmware update batch has been tampered with in transit. The task is to count how many packets have a stored checksum that does not match the XOR of their payload bytes, revealing which packets were corrupted.

## Provided Files

None (Docker instance only).

## Tools Used

- Python 3

## Walkthrough

1. Read the number of packets N.

2. For each packet, read the line and parse it as a list of integers. The first integer is L (payload length). The next L integers are the payload bytes. The integer after the payload is the stored checksum.

3. Compute the XOR of all payload bytes by folding with the XOR operator, starting from zero.

4. Compare the computed XOR to the stored checksum. If they differ, increment a counter.

5. Print the final count.

```python
n = int(input())
count = 0
for _ in range(n):
    nums = list(map(int, input().split()))
    L = nums[0]
    payload = nums[1:L+1]
    stored = nums[L+1]
    xor = 0
    for b in payload:
        xor ^= b
    if xor != stored:
        count += 1
print(count)
```

No external libraries are needed. The solution runs in O(N * L) time, which is optimal since every byte must be read at least once.

## Key Findings

- XOR is self-inverse, so a single linear pass over the payload bytes is sufficient to verify the checksum.
- The input format packs the length, payload, and checksum on a single line, requiring careful index arithmetic when slicing.
- No sorting or auxiliary data structures are needed.

## Final Answer

`Flag: HTB{xor_7h3_truth_fr0m_7h3_n01s3}`

## Lessons Learned

XOR checksums are trivially computed with a single pass and no state beyond one accumulator variable. The challenge tests basic bit manipulation and input parsing under time constraints.
