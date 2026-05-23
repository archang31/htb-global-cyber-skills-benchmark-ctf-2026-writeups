# Twice or Nothing

## Category
Cryptography

## Difficulty
Medium

## Summary
A hardened variant of Once or Nothing adds two mitigations: messages are SHA-256 hashed before signing, and the server terminates after 6 signing queries (BURN_LIMIT = 5). SHA-256 pre-hashing defeats the trivial all-zeros/all-ones attack, but key reuse persists. A greedy set-cover strategy over random query messages recovers all 256 key positions within 4 queries on average, leaving 2 spare queries under the limit.

## Provided Files
- `crypto_twice_or_nothing.zip` (challenge server source)

## Tools Used
- Python 3
- pwntools
- hashlib

## Walkthrough

### Changes from Once or Nothing

1. The server hashes the message with SHA-256 before signing: `h = SHA256(m)`, then `token[i] = s_{h[i]}[i]`.
2. The server enforces `BURN_LIMIT = 5`, terminating after `issue_count > 5` (6 total queries including the forgery attempt).

### Target Hash

The forgery target is `"d9_netadmin"`. Its SHA-256 digest is computed offline:

```
H_target = SHA256(b"d9_netadmin")
         = fe84ada17e67e2929b468c7f17392d4535d8851821c092fe74d7ac4a836148dd
```

This determines, for each position `i`, which secret (`s0[i]` or `s1[i]`) is needed.

### Set-Cover Key Recovery

Signing a message `M` reveals `s_{h[i]}[i]` for each `i`, where `h = SHA256(M)`. A position `i` is useful for the forgery only when `SHA256(M)[i] == H_target[i]`. On average, each random message covers approximately 128 positions, but the relevant half is those where the bit agrees with `H_target`. Expected coverage per query is around 128 positions on a fresh key, declining as uncovered positions shrink.

**Greedy selection:** Before each query, generate 50,000 random 32-byte candidate messages. For each candidate, count how many uncovered positions its SHA-256 hash would reveal. Select the candidate with the highest count and issue the query.

Expected coverage progression:

| Round | New positions covered | Remaining |
|-------|-----------------------|-----------|
| 1     | ~165                  | ~91       |
| 2     | ~70                   | ~24       |
| 3     | ~22                   | ~3        |
| 4     | ~3                    | 0         |

Four queries typically suffice; rounds 5 and 6 are spare.

### Token Forgery

After collecting tokens from the query messages:

```python
# source[i] = index j of the query message that covers position i
source = {}
for j, msg in enumerate(query_messages):
    h = sha256_bits(msg)
    for i in range(256):
        if i not in source and h[i] == target_bits[i]:
            source[i] = j

forged = [tokens[source[i]][i] for i in range(256)]
submit_token("d9_netadmin", forged)
```

### Solve Script

```bash
python3 work/solve.py <target-ip> <target-port>
```

The script runs the greedy set-cover loop, issues at most 4-5 queries, assembles the forged token, and submits.

## Key Findings
- SHA-256 pre-hashing prevents the trivial all-zeros/all-ones attack but does not prevent set-cover key recovery.
- Greedy set cover with 50,000 candidates per round achieves full coverage in 4 queries on average.
- The BURN_LIMIT of 5 queries is far too low to be secure against set cover; at least 257 queries would be needed to make the attack impractical.

## Final Answer
`Flag: HTB{y0u_kn0w_1t_1s_c4ll3d_0n3_t1m3_s1gn4tur3_f0r_4_r34s0n_273ba0a00cb49557b0fc69f409a3a897}`

## Lessons Learned
Lamport's one-time property cannot be patched by adding a pre-hash. As long as multiple signatures are permitted under the same key, an adversary can always collect enough partial information to forge any target message. The correct fix is to use a distinct key pair for each message, or to migrate to a scheme with provable multi-use security such as XMSS or SPHINCS+. The burn limit mitigation is ineffective because it does not reduce coverage below 100% within the allowed query budget.
