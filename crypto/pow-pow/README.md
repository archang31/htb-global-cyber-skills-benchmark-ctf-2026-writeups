# Pow Pow

## Category
Cryptography

## Difficulty
Medium

## Challenge Description

Beneath the transit layer, the DeadDrop Cartel routes proxy payments through a validation chain that demands rapid sequential approval. The checkpoint window is narrow, and the route will shift if you linger.

**Creator:** Xclow3n

## Summary
A blockchain ledger requires mining 100 blocks in 30 seconds, each with 50 leading zero bits in a custom hash. The hash function is an affine map over Z_n, making it a bijection. Rather than brute-forcing 2^50 nonces, each valid nonce is derived analytically via a single modular inversion per block.

## Provided Files
- `crypto_pow_pow.zip` (challenge server source)

## Tools Used
- Python 3
- pwntools

## Walkthrough

### Hash Function

The server reveals 256-bit parameters `a`, `b`, `n` at connection time and defines:

```
ledger_hash(data) = (a * bytes_to_long(data) + b) mod n
```

Each block is hashed as:

```
hash = ledger_hash(long_to_bytes(prev_hash) + blockdata + nonce)
```

The 50-leading-zero requirement means `hash < 2^206` (256-bit output).

### Vulnerability

Because `a` is invertible mod `n`, `ledger_hash` is a bijection over Z_n. Given any target output value, the exact input that produces it can be computed directly. There is no computational hardness, and brute force is unnecessary.

### Attack

Let `prefix_bytes = long_to_bytes(prev_hash) + blockdata` and `prefix_int` be its integer value. The full input to `ledger_hash` is:

```
x = prefix_int * 2^256 + nonce_int
```

Setting `target = 0` (trivially satisfies the leading-zero requirement), the required nonce satisfies:

```
(a * (prefix_int * 2^256 + nonce_int) + b) ≡ 0  (mod n)

nonce_int = ((-a * prefix_int * 2^256 - b) * pow(a, -1, n)) % n
```

This is computed in O(1) per block using Python's built-in `pow(a, -1, n)`.

### Solve Script

```bash
python3 work/solve.py <target-ip> <target-port>
```

Core per-block logic:

```python
a_inv = pow(a, -1, n)

def solve_nonce(prev_hash, blockdata):
    prefix = long_to_bytes(prev_hash) + blockdata
    prefix_int = bytes_to_long(prefix)
    # target = 0: choose nonce so hash = 0
    nonce_int = ((-a * prefix_int * pow(2, 256, n) - b) * a_inv) % n
    return long_to_bytes(nonce_int)
```

With 100 blocks solved analytically, the 30-second window is trivially met.

## Key Findings
- The "proof of work" is trivially invertible because the hash function is a bijection over Z_n.
- No brute force is needed; each nonce is computed analytically in O(1) per block.
- The 30-second time window is irrelevant once the algebraic structure is identified.

## Final Answer
`Flag: HTB{50wing_7h3_s33d5_0f_my_pow}`

## Lessons Learned
Proof-of-work schemes are only secure if the underlying hash function is a one-way function. An affine map over Z_n is invertible by construction; the entire difficulty claim collapses to a single modular inverse. Cryptographically secure PoW must use a function for which no efficient inversion algorithm is known, such as SHA-256 with proper domain separation and no exploitable algebraic structure.
