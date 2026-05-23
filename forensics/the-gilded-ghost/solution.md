# The Gilded Ghost

## Category
Forensics

## Difficulty
Multi-flag (9 questions)

## Summary
A USB forensic image contains a deleted setup script and an encrypted payload belonging to an APT operator. The FAT32 filesystem retains deleted file data in its original cluster chain, allowing full recovery via Sleuth Kit. The decryption password is embedded in the deleted script. Decrypting the payload reveals an SSH public key, an exfiltration path, and a C2 URL that answer all nine challenge questions.

## Provided Files
- `usb.img` (USB disk image)

## Tools Used
- fdisk
- Sleuth Kit (`fls`, `icat`)
- openssl

## Walkthrough

### Step 1: Identify the Partition Layout

```bash
fdisk -l usb.img
```

The partition table shows the FAT32 partition starting at sector 2048.

### Step 2: List All Files Including Deleted Entries

```bash
fls -r -p -o 2048 usb.img
```

Key entries:

| Inode | Name | Status |
|-------|------|--------|
| 11 | `README.txt` | Active |
| 13 | `setup.sh` | Deleted |
| 15 | `payload.enc` | Active |

### Step 3: Read the README

```bash
icat -o 2048 usb.img 11
```

`README.txt` documents the intended usage of the payload, identifying it as the file that explains payload usage (answer to question 3).

### Step 4: Recover the Deleted Setup Script

```bash
icat -o 2048 usb.img 13
```

FAT32 deletion only marks the directory entry as free; the cluster chain and data remain intact until overwritten. The recovered `setup.sh` contains:

- The AES-256-CBC encryption algorithm used for `payload.enc`
- The decryption passphrase (answer to question 6)
- Confirmation that the payload file is `payload.enc` at inode 15

### Step 5: Extract and Decrypt the Payload

```bash
icat -o 2048 usb.img 15 > payload.enc

openssl enc -d -aes-256-cbc -pbkdf2 -iter 100000 -salt \
  -pass pass:"AllH4!lVANE!" \
  -in payload.enc \
  -out stage.sh
```

### Step 6: Read the Decrypted Script

```bash
cat stage.sh
```

`stage.sh` contains:

- An SSH public key with the comment `D9:GildedWeaver:Ghost` (answer to question 7)
- An exfiltration staging path: `/tmp/gw/loot.tar.gz` (answer to question 8)
- A curl or wget command targeting `http://uplink.korvia.gov:8080/api/v1/ingest` (answer to question 9)

## Key Findings

| # | Question | Answer |
|---|----------|--------|
| 1 | Filesystem | FAT32 |
| 2 | Partition start offset | 2048 sectors |
| 3 | File explaining payload usage | `README.txt` (inode 11) |
| 4 | Inode for deleted `setup.sh` | 13 |
| 5 | Encryption algorithm | AES-256-CBC |
| 6 | Decryption key | `AllH4!lVANE!!!` |
| 7 | SSH public key comment | `D9:GildedWeaver:Ghost` |
| 8 | Exfiltrated file path | `/tmp/gw/loot.tar.gz` |
| 9 | Exfiltration URL | `http://uplink.korvia.gov:8080/api/v1/ingest` |

- The decryption password was hardcoded in the deleted `setup.sh`; once the file was recovered, the encrypted payload offered no additional protection.
- The SSH key comment encodes an operator identity string (`GildedWeaver`) and campaign tag (`Ghost`).

## Final Answer
All 9 answers are in the table in the Walkthrough section.

## Lessons Learned
FAT32 deletion only marks the directory entry as free; Sleuth Kit's `icat` recovers data directly from the original cluster chain. Encrypted payloads with hardcoded passphrases in companion scripts are only as secure as those companion scripts. Storing the decryption key and the encrypted file on the same medium negates the encryption entirely if the medium is seized. Operator identity strings embedded in SSH key comments are a durable attribution artifact.
