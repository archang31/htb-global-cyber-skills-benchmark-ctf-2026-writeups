# Once or Nothing

## Category
Cryptography

## Difficulty
Very Easy

## Challenge Description

Dr. Qureshi intercepted traffic from a D9 authentication node hidden in the transit grid. The gateway predates the latest hardening directive, and the tokens it issues follow an older pattern. Secure administrative access before the patrol cycle resets.

**Creator:** Xclow3n

## Summary
A legacy D9 authentication gateway issues Lamport one-time signature tokens. The server allows the same key pair to sign multiple messages, which fatally violates the one-time property of Lamport signatures. Two oracle queries exposing all-zeros and all-ones bit patterns recover the entire 512-secret key, enabling forgery of an arbitrary target message.

## Provided Files
- `crypto_once_or_nothing.zip` (challenge server source)

## Tools Used
- Python 3
- pwntools (or raw socket)

## Walkthrough

### Key Generation

The server generates 256 pairs `(s0[i], s1[i])` of 256-bit random secrets. The public key is `(H(s0[i]), H(s1[i]))` for each position `i`. To sign a message `m` (padded to 32 bytes), the server returns:

```
token[i] = s0[i]  if bit i of m == 0
token[i] = s1[i]  if bit i of m == 1
```

### Attack

**Step 1.** Sign `0x00 * 32` (all-zeros message). Every bit is 0, so the server returns `s0[i]` for all 256 positions.

**Step 2.** Sign `0xFF * 32` (all-ones message). Every bit is 1, so the server returns `s1[i]` for all 256 positions.

At this point the complete key `{s0[i], s1[i]}` for `i in 0..255` is known.

**Step 3.** Compute the bit pattern of the target string `"d9_netadmin"` padded to 32 bytes with null bytes. The string is 11 bytes; bits 0-167 correspond to those characters and bits 168-255 are all zero (null padding).

**Step 4.** For each position `i`, select `s0[i]` if the target bit is 0, or `s1[i]` if it is 1. Submit the forged token for `"d9_netadmin"`.

### Solve Script

```bash
python3 work/solve.py <target-ip> <target-port>
```

Core forgery logic:

```python
zeros_token = sign(b"\x00" * 32)   # recovers all s0[i]
ones_token  = sign(b"\xff" * 32)   # recovers all s1[i]

target = b"d9_netadmin" + b"\x00" * 21
forged = []
for i in range(256):
    byte_idx, bit_idx = divmod(i, 8)
    bit = (target[byte_idx] >> (7 - bit_idx)) & 1
    forged.append(ones_token[i] if bit else zeros_token[i])

submit_token("d9_netadmin", forged)
```

## Key Findings
- Two oracle queries are sufficient to recover the full Lamport key.
- The flag text encoded in the challenge name hints at the intended lesson: `d0n7_f0rg3t_t0_h4sh_b3f0r3_4nyth1ng_3ls3`.
- Lamport keys must never be reused; one key pair must produce at most one signature.

## Final Answer
`Flag: HTB{d0n7_f0rg3t_t0_h4sh_b3f0r3_4nyth1ng_3ls3_3bb475641973590d880e86a770420cc3}`

## Lessons Learned
Lamport's one-time signature scheme is secure for exactly one signature but catastrophically broken on reuse. Two queries covering complementary all-zeros and all-ones bit patterns expose every secret value in the key. Additionally, signing must operate on `H(m)` rather than raw `m` to prevent an attacker from choosing messages with trivially useful bit patterns. The correct countermeasure is strict enforcement of the one-time property, or migration to a stateful hash-based scheme such as XMSS or SPHINCS+.
