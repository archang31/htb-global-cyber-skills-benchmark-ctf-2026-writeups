# Sysprobe

## Category
Reverse Engineering

## Difficulty
Hard

## Challenge Description

Task Force Nightfall has intercepted a binary pulled from a compromised monitoring node inside a critical infrastructure operator. On the surface it is exactly what it claims to be  a routine diagnostics utility, the kind deployed silently across thousands of managed endpoints. Clean signature, legitimate-looking output, nothing that trips an alert. But the node it was found on had no business running it. And the traffic logs don't match what a diagnostics tool should produce.

**Creator:** Xclow3n

## Summary
A multi-stage ELF binary embeds a compressed secondary payload. The inner payload encodes the
flag using a base-4 scheme with a 256-entry `QB_REAL` lookup table. Extracting, decompressing,
and decoding the payload recovers the flag.

## Provided Files
- reversing_sysprobe.zip (contains `sysprobe` binary)

## Tools Used
- Python 3 (zlib, struct)
- Ghidra

## Walkthrough

**Stage 1: locating the embedded ELF**

The outer binary has 8 segments. Segment 7 at file offset `0x4000` is a standalone ELF loader.
All meaningful logic resides there; the outer binary is only a carrier.

**Stage 2: extracting the compressed payload**

Within the embedded ELF, a raw DEFLATE-compressed payload starts at offset `0xf98` relative to
the segment base, with length `0x1001` bytes. It has no zlib or gzip header; use
`wbits=-15` (raw inflate).

```python
import zlib

data = open('sysprobe', 'rb').read()
comp = data[0x4000 + 0xf98 : 0x4000 + 0xf98 + 0x1001]
out = zlib.decompress(comp, -15)
open('/tmp/decompressed.bin', 'wb').write(out)
```

**Stage 3: decoding the QB_REAL table**

The `QB_REAL` table is at offset `0x1260` in the decompressed payload (1024 bytes = 128 entries
of 8 bytes each). The table contains 4 distinct 8-byte values representing base-4 digits:

| Digit | Bytes (hex)        |
|-------|--------------------|
| 0     | 0000000000000000   |
| 1     | 4035940158b04d06   |
| 2     | 58b04d06c0ca6bfe   |
| 3     | 99e5e107187bb904   |

Groups of 4 digits decode to one byte:
`byte = (d0 << 6) | (d1 << 4) | (d2 << 2) | d3`

**Full decoder:**

```python
import struct

data = open('/tmp/decompressed.bin', 'rb').read()
qb = data[0x1260 : 0x1260 + 1024]

vals = [
    bytes.fromhex('0000000000000000'),
    bytes.fromhex('4035940158b04d06'),
    bytes.fromhex('58b04d06c0ca6bfe'),
    bytes.fromhex('99e5e107187bb904'),
]
lookup = {v: i for i, v in enumerate(vals)}
symbols = [lookup[bytes(qb[i:i+8])] for i in range(0, 1024, 8)]

result = []
for i in range(0, len(symbols), 4):
    g = symbols[i:i+4]
    result.append((g[0] << 6) | (g[1] << 4) | (g[2] << 2) | g[3])

print(bytes(result).rstrip(b'\x00').decode())
```

## Key Findings

- The outer binary is a loader; all logic is in segment 7, which is itself a complete ELF
- The compressed payload uses raw DEFLATE (`wbits=-15`) without a zlib or gzip wrapper
- The `QB_REAL` encoding is base-4 with IEEE 754 double values as digit symbols; each output
  byte requires four table lookups (32 bytes of encoded data)
- The 4 symbol values are distinct IEEE 754 doubles chosen to be visually distinguishable in a
  hex dump

## Final Answer

`Flag: HTB{TH15_TH3_END_0R_WH4T}`

## Lessons Learned

Multi-stage loaders pack all complexity into embedded segments; identifying and extracting those
segments is the first and most important step. Recognizing raw DEFLATE vs. zlib vs. gzip
requires checking the first two bytes: `0x78 0x9C` is zlib, `0x1F 0x8B` is gzip, and anything
else starting a valid block is likely raw DEFLATE requiring `wbits=-15`. Custom encoding schemes
using floating-point constants as symbols are identifiable by their fixed 8-byte patterns
repeated throughout `.rodata`.
