# COMfortable Exfiltration

## Category
Forensics

## Difficulty
Multi-flag (8 flags)

## Summary
A Windows memory dump and disk image reveal a sophisticated COM-based persistence and exfiltration chain. A malicious service binary (`updater.exe`) embeds a .NET DLL (`GrumpyFisherman.dll`) in its resource section and loads it via COM. The DLL hijacks `ADODB.Stream`, drops a secondary file, and communicates with a C2 server over HTTP. Full DPAPI forensics and password cracking recover browser-stored credentials for the final flag.

## Provided Files
- `disk.ad1` (FTK forensic image)
- `mem.elf` (Windows memory dump)

## Tools Used
- Volatility 3
- pypykatz
- python3-dissect
- Python 3
- Capstone
- hashcat
- sqlite3
- pycryptodome

## Walkthrough

### Flag 1: Malicious Service Binary Path

Scan running services from the memory image:

```bash
vol -f mem.elf windows.svcscan
```

The malicious service registers its binary at `C:\Temp\Microsoft Cache\updater.exe`.

### Flag 2: Hijacked COM Class

Scan the registry for HKCU COM registrations:

```bash
vol -f mem.elf windows.registry.printkey --recurse
```

The `ADODB.Stream` CLSID is overridden in `HKCU\Software\Classes\CLSID`, redirecting it to the attacker's DLL.

### Flag 3: Dropped Secondary File

Search for unusual file extensions in the memory file scan:

```bash
vol -f mem.elf windows.filescan | grep -i '.quh'
```

The secondary dropped file is `kathcjaz.quh`.

### Flag 4: GrumpyFisherman DLL GUID

Extract the embedded DLL from the `.rsrc` section of `updater.exe` at offset `0x150b0`. Parse the .NET metadata `#Blob` stream to find `GuidAttribute` values for each class. The result is:

```
GrumpyFisherman:{b3ccd9d8-ffec-4de0-8005-185a6364cedb}
```

### Flag 5: CryoPez COM CLSID

Disassemble `updater.exe` to locate `CoCreateInstance` call sites. The first call targets the CryoPez class, which handles service installation:

```
{0128ad20-af37-4421-851c-5c06de5c2b2c}
```

### Flag 6: FveUi BitLocker COM CLSID

A second `CoCreateInstance` call in `updater.exe` targets the OrangeDucky class, which interacts with BitLocker via FveUi:

```
{A7A63E5C-3877-4840-8727-C1EA9D7A4D50}
```

### Flag 7: C2 URL in GrumpyFisherman.dll

Parse the `#US` (user strings) heap of `GrumpyFisherman.dll`. Strings are obfuscated with a simple XOR scheme:

```python
decrypted[i] = low_byte[i] ^ (n - i)   # n = string length
```

Applying this to the relevant heap entry yields:

```
http://check.microsoftcloudservices.htb:8000/update/
```

### Flag 8: Recovered Credentials

Full DPAPI chain:

**Step 1.** Dump registry hives from memory and extract the NT hash:

```bash
vol -f mem.elf windows.registry.hivelist --dump

python3 /usr/share/doc/python3-impacket/examples/secretsdump.py \
  -sam registry.SAM.*.hive \
  -system registry.SYSTEM.*.hive \
  -security registry.SECURITY.*.hive LOCAL
```

**Step 2.** Crack the NT hash against rockyou:

```bash
hashcat -m 1000 <nt-hash> /usr/share/wordlists/rockyou.txt
```

**Step 3.** Generate DPAPI prekeys and decrypt the master key:

```bash
pypykatz dpapi prekey password <user-sid> <cracked-password> -o prekeys.txt
pypykatz dpapi masterkey mk_5915b1e9.bin prekeys.txt -o decrypted_mk.json
```

**Step 4.** Decrypt the AES-256-GCM browser encryption key from `Chrome/Thorium Local State` (`os_crypt.encrypted_key`) using the decrypted DPAPI master key.

**Step 5.** Use the AES-256-GCM key to decrypt entries in the `Login Data` SQLite database:

```bash
sqlite3 "Login Data" "SELECT origin_url, username_value, password_value FROM logins;"
```

Recovered credentials: `admin-03:yiz9yzf3HAnhw49hRCtxXEtsL`

## Key Findings
- `updater.exe` embedded `GrumpyFisherman.dll` in its `.rsrc` section and loaded it via COM hijacking of `ADODB.Stream` in HKCU, requiring no elevated privileges.
- The C2 URL was obfuscated using a length-XOR scheme in the .NET `#US` heap.
- Three distinct COM objects handled different malicious functions: `CryoPez` (service install), `HyperAlan` (C2 exfiltration), and `OrangeDucky` (BitLocker interaction via FveUi).
- The full DPAPI chain required memory-extracted hives and password cracking to recover the AES-256-GCM browser encryption key.

## Final Answer
All 8 flags are listed in the Walkthrough section. Final credential recovered:

`admin-03:yiz9yzf3HAnhw49hRCtxXEtsL`

## Lessons Learned
COM hijacking via HKCU registration requires no elevated privileges and persists across reboots. Browser credential stores protected by DPAPI are recoverable once the user password is known, making password hygiene and full-disk encryption critical but insufficient on their own. Full DPAPI forensics requires a memory dump (for hive extraction) combined with offline password cracking. .NET string obfuscation in the `#US` heap is easily reversed once the XOR scheme is identified.
