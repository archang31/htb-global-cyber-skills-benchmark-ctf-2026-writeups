# Flashpoint

## Category
Pwn

## Difficulty
Medium

## Summary
A firmware updater binary exposes a write primitive that can be redirected to overwrite a function pointer in a memory-mapped region. Because no ASLR or PIE is enabled, the function pointer address is fixed and can be overwritten with the address of the flag-printing function.

## Provided Files
`pwn_flashpoint.zip` containing the challenge binary

## Tools Used
- Python 3
- pwntools
- GDB with pwndbg

## Walkthrough

### Step 1: Reverse the Binary

Analyze the firmware update handler. The updater reads an update packet that contains a destination address and payload data. The destination address field is taken from the packet header and used as the write target without bounds checking.

### Step 2: Identify the Target

A function pointer lives at `0x00018000` in the binary's memory-mapped region. This pointer is called after every successful update operation.

A separate function (the win/flag function) prints the flag when called directly. Its address is fixed due to the absence of ASLR and PIE.

### Step 3: Craft the Payload

Build an update packet that:
1. Sets the destination address to `0x00018000`
2. Sets the payload to the address of the flag function (4 bytes, little-endian)

### Step 4: Trigger the Function Pointer

Send the crafted update packet to the service. The updater writes the flag function's address over the function pointer at `0x00018000`, then calls it as part of normal post-update processing. The flag is printed to stdout.

```bash
python3 work/exploit.py <target-ip> <target-port>
```

## Key Findings
- The update packet's destination address field is used directly as a write target with no bounds checking against legitimate flash regions
- The function pointer at `0x00018000` is invoked after every update, making it an ideal hijack target
- No ASLR or PIE is present; all addresses are static and deterministic

## Final Answer
`Flag: HTB{th3_upd4t3r_1s_th3_w34p0n_0x00018000}`

## Lessons Learned
Firmware update handlers must validate write destinations against an explicit allowlist of legitimate flash regions before performing any write. Unrestricted write primitives combined with in-memory function pointers create reliable code execution paths without requiring stack-based exploitation or information leaks. Enabling PIE and ASLR alone is insufficient when a write primitive allows targeting arbitrary addresses; bounds enforcement at the application level is required.
