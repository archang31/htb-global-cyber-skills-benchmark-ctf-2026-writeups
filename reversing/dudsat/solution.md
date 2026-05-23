# Dudsat

## Category
Reverse Engineering

## Difficulty
Medium

## Summary
A stripped ELF binary processes satellite observation data from `comms.dat`. Each record
encodes one flag character via a Doppler residual mapped through a seeded LCG S-box. The
anti-debug ptrace check is bypassable; the S-box is reconstructable offline from constants in
`.rodata`.

## Provided Files
- rev_dudsat.zip (contains `lbproc` binary and `comms.dat`)

## Tools Used
- Python 3 (struct)
- Ghidra (static analysis)

## Walkthrough

**Initial analysis:**

Running `./lbproc comms.dat` outputs 26 windows. Windows 1 and 26 report NO-LOCK; windows 2-25
report LOCK. No flag is printed. The binary calls `ptrace(PTRACE_TRACEME)` at startup and exits
if a debugger is attached; static analysis is the intended approach.

**Record format** (26 records, 48 bytes each, little-endian):

| Offset | Type    | Field           |
|--------|---------|-----------------|
| 0x00   | uint64  | timestamp       |
| 0x08   | double  | f0 (ref. freq.) |
| 0x10   | double  | range_rate      |
| 0x18   | double  | f_received (Hz) |
| 0x20   | float   | elevation (deg) |
| 0x24   | float   | SNR (dB)        |
| 0x28   | uint64  | window index    |

**S-box reconstruction:**

The S-box is initialized in `.rodata` via a Fisher-Yates shuffle driven by an LCG with seed
`0x20FC8`, multiplier `0x19660D`, and addend `0x3C6EF35F`. The shuffle iterates `i` from 255
down to 0.

**Doppler residual computation:**

For each record, the residual is:

```
residual = f_received - f0 * (1 + range_rate / 418229116)
```

The divisor `418229116` is stored in `.rodata` at `0x402188`. The flag byte is
`sbox[int(residual) & 0xFF]`.

**Full solver:**

```python
import struct

def lcg_next(state):
    return (state * 0x19660D + 0x3C6EF35F) & 0xFFFFFFFF

sbox = list(range(256))
state = 0x20FC8
for i in range(255, -1, -1):
    state = lcg_next(state)
    j = state % (i + 1)
    sbox[i], sbox[j] = sbox[j], sbox[i]

data = open('comms.dat', 'rb').read()
C = 418229116.0

flag = []
for i in range(len(data) // 48):
    rec = data[i * 48:(i + 1) * 48]
    ts, d1, d2, d3, f1, f2, idx = struct.unpack('<QdddffQ', rec)
    residual = d3 - d1 * (1.0 + d2 / C)
    flag.append(chr(sbox[int(residual) & 0xFF]))

print(''.join(flag))
```

## Key Findings

- The LOCK/NO-LOCK status (elevation >= 5 deg, SNR >= 12 dB, |residual| <= 5000 Hz) is a
  distractor; all 26 windows contribute flag characters including the two NO-LOCK windows
- The S-box is reconstructable entirely offline from constants in `.rodata`; patching the
  ptrace call is unnecessary
- The Doppler divisor `418229116` encodes each character as a sub-Hz frequency residual

## Final Answer

`Flag: HTB{d0ppl3r_p3rm_l34k_h7b}`

## Lessons Learned

Anti-debug checks such as `ptrace(PTRACE_TRACEME)` can often be bypassed by analyzing the
binary statically and reconstructing secret parameters offline, making dynamic analysis
unnecessary. When a binary's output appears incomplete, look for computation paths that execute
unconditionally but only display results through a gated output function. LCG-based S-box
initialization is identifiable by the characteristic constant pair (multiplier, addend) in
`.rodata`.
