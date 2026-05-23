# Open Wound

## Category
Forensics

## Difficulty
Hard (1 flag)

## Summary
An IIS server was compromised via a malicious native module (`RewriterModule.dll`). The flag is split across two delivery channels: the first half is inside a GPG-encrypted document on disk, and the second half is embedded in shellcode within a C2-uploaded archive transmitted over encrypted HTTP. Recovery requires GPG key extraction, AES-CBC traffic decryption, archive reassembly, and shellcode analysis.

## Provided Files
- `disk.ad1` (FTK forensic image)
- `traffic.pcap` (network capture)

## Tools Used
- dissect/evidence (AD1 parsing)
- Python 3
- gpg
- Capstone / Ghidra
- Wireshark / Scapy
- pycryptodome

## Walkthrough

### Step 1: Mount the Disk Image

Parse `disk.ad1` with `dissect.evidence` and navigate the NTFS structure to access the Windows user profile and IIS directories.

### Step 2: Extract GPG Private Keys

Two unprotected `.key` files are located at:

```
Users/Administrator/AppData/Roaming/gnupg/private-keys-v1.d/
```

Import both keys into a local GPG keyring:

```bash
gpg --import *.key
```

### Step 3: Decrypt the Document and Recover the First Flag Half

Decrypt the encrypted document:

```bash
gpg --decrypt StyleNet_Retail_Network_Design.docx.gpg > StyleNet_Retail_Network_Design.docx
```

Extract `word/document.xml` from the DOCX archive and grep for the HTB flag prefix to find the first half of the flag (approximately 20 characters).

### Step 4: Locate the Malicious IIS Module

`RewriterModule.dll` is present on disk as the registered IIS native module. It intercepts HTTP traffic in-process with SYSTEM privileges.

### Step 5: Extract the AES Key

In the `.data` section of `RewriterModule.dll`, locate the C++ `std::string` SSO (small-string optimization) buffer adjacent to the RTTI string `"?AVHttpModule"`. The 16-byte AES-128 key is stored directly in this buffer.

### Step 6: Decrypt C2 Traffic

The C2 protocol uses AES-128-CBC with the following structure:

- **Commands:** `base64([FIXED_IV:16][AES-CBC-CT])` where plaintext = `[8 zero bytes][command\x00]`
- **Responses:** `base64([RANDOM_IV:16][AES-CBC-CT])` where plaintext = `[content_len:4][content]`

Decrypt all C2 streams in `traffic.pcap` using the extracted key:

```python
from Crypto.Cipher import AES
import base64

def decrypt_response(b64_blob, key):
    raw = base64.b64decode(b64_blob)
    iv, ct = raw[:16], raw[16:]
    return AES.new(key, AES.MODE_CBC, iv).decrypt(ct)
```

### Step 7: Reassemble the Uploaded Archive

The C2 responses contain 18 upload chunks totaling 70,286 bytes, each with the structure:

```
[chunk_size:4][path_len:4][path][data]
```

Reassemble the chunks in order to reconstruct `iisupdate.zip`.

### Step 8: Extract and Analyze the Shellcode

Extract `Scdaemon.dll` from `iisupdate.zip`. The embedded shellcode begins at offset `0x27` and is XOR-encrypted with an 8-byte repeating key found at the start of the encrypted blob.

Decrypt and disassemble with Capstone. The shellcode contains a `net user` command string that holds the second half of the flag.

Combining both halves yields the complete flag.

## Key Findings
- The flag was intentionally split across two delivery channels (encrypted document on disk and shellcode in a C2-uploaded archive) to require full chain reconstruction.
- The IIS native module communicated over standard HTTP, using encrypted `Cache-Control` headers to blend into legitimate traffic.
- The AES key was stored as a C++ `std::string` SSO buffer in `.data`, identifiable by its proximity to an RTTI string.
- The upload protocol used a fixed 4-byte length-prefixed chunk format across 18 sequential transmissions.

## Final Answer
`Flag: HTB{D1rty_IIS_n4t1v3_m0dul3_0n_7hE_l04D}`

## Lessons Learned
Malicious IIS native modules operate in-process with SYSTEM privileges and can intercept, modify, or log all HTTP traffic on the server. Splitting a payload across multiple delivery channels (encrypted document plus C2 upload) increases analyst effort significantly. SSO buffers and RTTI strings are reliable anchors for locating embedded cryptographic keys in C++ binaries without symbols. AES-128-CBC with a static key and predictable IV scheme is vulnerable to full traffic decryption once the key is recovered from the binary.
