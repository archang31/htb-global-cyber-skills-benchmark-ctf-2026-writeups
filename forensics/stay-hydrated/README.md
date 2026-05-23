# Stay Hydrated

## Category
Forensics

## Difficulty
Hard (1 flag)

## Challenge Description

Horizon Trust Solutions is panicking after a disguised wiper attack encrypted deployment servers. The perpetrators, using the DeadDrop Cartel proxy, left no ransom note, exposing their motive as state-sponsored sabotage. Directorate 9 operatives lurked in our network for months, mapping federation trusts and harvesting credentials to orchestrate this deep-seated assault. At stake is the core validation framework for the Trusted Supply Chain Act, built for the National Election Commission. With polls opening in days, the pristine deployment package was finalized for handover. In a calculated move, Vane's forces struck at the eleventh hour to maximize public panic and disruption. The geopolitical repercussions are immense; failing to deliver compromises the election and cements Korvia's leverage. Task Force Nightfall implores your expertise to recover the uncorrupted release package from the crippled staging environment.

**Creator:** c4n0pus

## Summary
A deleted 7z archive and a deleted keylogger file must be recovered from a Windows Data Deduplication (WDS) volume. Standard forensic tools see only empty MFT records for deleted deduplicated files. Recovery requires parsing the WDS Smap index and Ckhr chunk store directly, reassembling LZXPRESS-compressed chunks, decoding keystroke events to recover a KeePass master password, and then decrypting the archive to extract the flag.

## Provided Files
- `D.E01` (EWF disk image, data volume with WDS)
- `C.vhdx` (system volume)

## Tools Used
- ewfmount
- Sleuth Kit (`fls`, `icat`)
- dissect.util (LZXPRESS decompression)
- pykeepass
- python-7zip
- Python 3

## Walkthrough

### Step 1: Mount the EWF Image

```bash
ewfmount D.E01 /mnt/ewf
```

### Step 2: Identify Key Inodes

Run `fls` against the mounted NTFS volume to find relevant inodes:

```bash
fls -r -p /mnt/ewf/ewf1
```

Key inodes located:

| File | Inode |
|------|-------|
| `Dev.kdbx` (KeePass database) | 5156 |
| Deleted 7z archive | 161 |
| `dev02.dat` (keylogger, deleted) | 159 |
| Smap index | 71 |
| Ckhr chunk store | 77 |

### Step 3: Extract the WDS Containers

```bash
icat /mnt/ewf/ewf1 71 > smap.bin
icat /mnt/ewf/ewf1 77 > ckhr.bin
```

### Step 4: Locate WDS Stream IDs via Reparse Points

For deleted deduplicated files, the MFT record contains a `$REPARSE_POINT` attribute (tag `0x80000013`). The WDS stream ID is stored at byte offset 148 of the reparse data payload.

- Inode 161 (deleted 7z): stream ID 161
- Inode 159 (`dev02.dat`): stream ID 162

### Step 5: Reassemble the Deleted 7z Archive

Parse Smap block 161 to locate the chunk entries for the 7z file. For each chunk, check whether it is compressed (LZXPRESS) or stored raw, then decompress and concatenate:

```python
from dissect.util.compression import lzxpress

def reassemble_stream(smap_block, ckhr_data):
    chunks = parse_smap_block(smap_block)
    output = b""
    for chunk in chunks:
        raw = extract_chunk(ckhr_data, chunk.offset, chunk.length)
        if chunk.is_compressed:
            output += lzxpress.decompress(raw, chunk.original_size)
        else:
            output += raw
    return output
```

The resulting file is 240,726 bytes; verify against the expected size parsed from the Smap header.

### Step 6: Recover the KeePass Master Password from the Keylogger

Parse Smap block 162 and reassemble `dev02.dat` by the same method. The file contains keystroke events in the format:

```
["key_name", Key.x pressed]
["key_name", Key.x released]
```

Process only `pressed` events. Apply `Key.backspace` to remove the last character and `Key.enter` to append a newline. The master password appears in the sequence typed immediately after the string `keepass` is entered.

```python
def decode_keylog(events):
    buf = ""
    for name, action in events:
        if "pressed" not in action:
            continue
        if name == "backspace":
            buf = buf[:-1]
        elif name == "enter":
            buf += "\n"
        elif len(name) == 1:
            buf += name
        # handle shift, caps, etc. as appropriate
    return buf
```

### Step 7: Open the KeePass Database

```python
from pykeepass import PyKeePass

kp = PyKeePass("Dev.kdbx", password=recovered_master_password)
entry = kp.find_entries(title="StarlineTicketing", first=True)
archive_password = entry.password
```

### Step 8: Extract the Flag

```bash
7z e -p"<archive-password>" /tmp/StarlineTicketing.7z .env -so
```

The `.env` file contains the flag.

## Key Findings
- Deleted files on Windows with Data Deduplication leave no recoverable data in MFT records; all content resides in the WDS Smap/Ckhr stores and is fully recoverable if those stores have not been garbage-collected.
- The WDS stream ID at byte 148 of the `$REPARSE_POINT` payload is the critical link between an MFT inode and its WDS block.
- A deleted keylogger file in the same dedup store provided the KeePass master password required to unlock the archive password.
- LZXPRESS decompression via `dissect.util` is necessary for compressed chunks; not all chunks are compressed.

## Final Answer
`Flag: HTB{d4t@_d3dupl1c4t10n_1s_sup3r_und3rRat3d}`

## Lessons Learned
Windows Data Deduplication is a forensic blind spot for tools that do not implement WDS stream reassembly. Deleted files may still be fully recoverable from the chunk store if the Smap index and Ckhr container have not been garbage-collected. Keylogger artifacts stored on the same volume as the secrets they capture create a single point of recovery for an analyst. The multi-step chain (WDS recovery, keylog decode, KeePass, 7z) is a good model for defense in depth that still fails when each link is recoverable from the same evidence source.
