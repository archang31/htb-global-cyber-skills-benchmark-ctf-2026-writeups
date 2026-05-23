# The Dark Night

## Category
Secure Coding

## Difficulty
Hard

## Score
100/100 (Hard: 60/60, Soft: 40/40)

## Summary
A Python ECDSA signing module uses a deterministic but catastrophically broken nonce:
`k = SHA-256(payload) mod n`, which is identical to the signing hash `e`. Because `k = e`, the
private key is recoverable from any single signature via one modular inversion. The fix replaces
the broken `sign()` implementation with RFC 6979 deterministic nonce derivation using the
`ecdsa` library's `sign_deterministic()` method.

## Provided Files
- Git repository at `http://<target-ip>:<target-port>/git/core_application.git`

## Tools Used
- Git
- Python 3
- curl

## Walkthrough

**Vulnerability analysis:**

The vulnerable code in `darkauth/signer.py`:

```python
def _derive_nonce(payload: str) -> int:
    return int(hashlib.sha256(payload.encode()).hexdigest(), 16) % SECP256K1_ORDER

def sign(payload: str) -> str:
    k = _derive_nonce(payload)
    # ECDSA signs: s = k^-1 * (e + r*d) mod n
    # e is computed internally as SHA-256(payload) mod n
    # Since k = e, rearranging gives: d = e*(s-1) * r^-1 mod n
```

`_derive_nonce` returns `SHA-256(payload) mod n`. ECDSA computes the signing hash `e` as
`SHA-256(payload) mod n` over the same payload using the same hash function. Therefore `k = e`
for every signing operation.

With `k = e`, the ECDSA equation `s = k^-1 * (e + r*d) mod n` rearranges to:

```
d = e * (s - 1) * r^-1 mod n
```

The private key `d` is recoverable from any single public signature using only the public
parameters `(r, s)` and the message hash `e`.

**Fix:**

Replace `sign()` with `sign_deterministic()` from the `ecdsa` library (RFC 6979). Remove
`_derive_nonce` entirely. RFC 6979 derives `k` from
`HMAC-DRBG(private_key, message_hash)`, making `k` independent of `e` and unpredictable to
any observer who does not know the private key.

```python
def sign(payload: str) -> str:
    signature = _SIGNING_KEY.sign_deterministic(
        payload.encode(),
        hashfunc=hashlib.sha256,
        sigencode=sigencode_string,
    )
    return signature.hex()
```

The public API signature is unchanged. No other files require modification.

**Deployment:**

```bash
git clone http://htb_developer:HTBDeveloperPassword@<target-ip>:<target-port>/git/core_application.git
cd core_application
git checkout -b developer origin/developer
# Edit darkauth/signer.py: replace sign(), remove _derive_nonce
git add darkauth/signer.py
git commit -m "fix: replace broken deterministic nonce with RFC 6979 in ECDSA signing"
git push -u origin developer
curl -s http://<target-ip>:<target-port>/flag
```

## Key Findings

- When `k = e` in ECDSA, private key recovery requires only one signature and one modular
  inversion; no brute force or lattice attack is needed
- `_derive_nonce` returns `SHA-256(payload) mod n`, which is byte-for-byte identical to the
  signing hash `e` computed internally by the `ecdsa` library
- RFC 6979 derives `k` from `HMAC-DRBG(private_key || message_hash)`, making `k`
  unpredictable to any party who does not know the private key
- The fix removes one function and changes one call site; the public API and all callers are
  unaffected

## Final Answer

`Flag: HTB{BORN_IN_1T_M01D3D_BY_17_5a6ca96fa6d71afe694040adf9c7b98a}`

## Lessons Learned

ECDSA nonce reuse or predictability is a total break: a single signature leaks the private key.
The nonce `k` must be generated from a source that is both secret and independent of the
signing hash `e`. RFC 6979 provides both security and reproducibility without requiring an
external entropy source at signing time. Using a library primitive (`sign_deterministic`) over
a hand-rolled nonce derivation eliminates an entire class of vulnerability at zero performance
cost.
