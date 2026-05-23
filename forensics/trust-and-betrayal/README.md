# Trust and Betrayal

## Category
Forensics

## Difficulty
Multi-flag (8 questions)

## Challenge Description

Gabe Okoye has flagged a disturbing shift in our systems' lineage immediately following the deployment of VeldoriaPanel, an application we built internally with security in mind. Although the panel is a trusted service, its installation coincides with the appearance of malicious activity that feels too disciplined to be random. We need you to determine if this internal tool has been nudged to create a silent opening for the adversary. Your mission is to uncover if our own secure development path has been compromised to grant Silas Vane the permanent, quiet access he requires.

**Creator:** makelaris

## Summary
A developer workstation was compromised via a malicious npm package served from an attacker-controlled private registry. A trojanized version of `axios` bundled a malicious dependency (`simple-crypto-js`) whose postinstall script deployed a renamed PowerShell binary, a VBScript launcher, and a persistence payload. The attack is classified as MITRE ATT&CK T1195.001 (Supply Chain Compromise via Software Dependencies).

## Provided Files
- `forensics_trust_and_betrayal.zip` containing:
  - Volatility memory image
  - Windows user profile artifacts (NTUSER.DAT, event logs, `node_modules/`)

## Tools Used
- Volatility 3
- regipy
- Python 3

## Walkthrough

### Step 1: Identify the Malicious postinstall Script

Search the extracted `node_modules` tree for packages with a `postinstall` hook:

```bash
find node_modules -name "package.json" | xargs grep -l "postinstall" | grep -v esbuild
```

The result points to `node_modules/simple-crypto-js/package.json`, with its postinstall script referencing `scripts/setup.js`.

**Answer:** Malicious file (first stage) = `setup.js`

### Step 2: Identify the Malicious Package

The `postinstall` script is in `simple-crypto-js`.

**Answer:** Malicious package = `simple-crypto-js`

### Step 3: Identify the Top-Level Compromised Package

Check the project's `package.json` to find the direct dependency that pulled in `simple-crypto-js`:

```bash
cat Documents/VeldoriaPanel/package.json
```

The project depends on `axios 1.14.1`. The real axios does not include `simple-crypto-js`; the trojanized version from the attacker registry added it as a dependency.

**Answer:** Top-level compromised package = `axios`

### Step 4: Identify the Exfil and Payload Domain

Search PowerShell script block logs (Event ID 4104) in `Microsoft-Windows-PowerShell/Operational.evtx` for network activity:

The decrypted `6202033.ps1` script block contains references to `rustf.htb` for both payload download and data exfiltration.

**Answer:** Domain = `rustf.htb`

### Step 5: Identify the VBScript Filename

The postinstall `setup.js` creates a VBScript file in the user's temp directory:

```bash
grep -r "\.vbs" node_modules/simple-crypto-js/
```

**Answer:** VBScript filename = `6202033.vbs`

### Step 6: Identify the Original Binary Name

The setup script copies a system binary and renames it to `wt.exe` to evade name-based detection rules. Checking the PE metadata of `wt.exe` (via Volatility `windows.dlllist` or strings) reveals the original filename in the version info:

**Answer:** Original binary name = `powershell.exe`

### Step 7: MITRE ATT&CK Technique

The attack vector is a trojanized open-source package served from a private registry that masquerades as a legitimate version of `axios`. This is a textbook software supply chain compromise targeting a development dependency.

**Answer:** MITRE ATT&CK technique = `T1195.001`

### Step 8: Registry Persistence Key

Parse `NTUSER.DAT` for Run key entries:

```python
from regipy.registry import RegistryHive

reg = RegistryHive("C/Users/developer/NTUSER.DAT")
run_key = reg.get_key(
    "Software\\Microsoft\\Windows\\CurrentVersion\\Run"
)
for value in run_key.get_values():
    print(value.name, value.data)
```

A value named `MicrosoftUpdate` pointing to `C:\ProgramData\system.bat` is found.

**Answer:** Registry persistence key = `HKCU\Software\Microsoft\Windows\CurrentVersion\Run`

### Full Attack Chain

1. Developer runs `npm install` in the `VeldoriaPanel` project. The project's `package.json` references `axios 1.14.1`.
2. The attacker's private registry at `192.168.128.1:4873` serves a trojanized `axios 1.14.1` that lists `simple-crypto-js 4.2.1` as a dependency.
3. npm executes `simple-crypto-js`'s `postinstall` hook, running `setup.js` with the developer's full privileges.
4. `setup.js` copies `powershell.exe` to `wt.exe`, writes `6202033.vbs` and downloads `6202033.ps1` from `rustf.htb`.
5. `cscript.exe 6202033.vbs` launches `wt.exe` with execution policy bypass flags to run the PowerShell script.
6. The PS1 script writes `C:\ProgramData\system.bat` and persists it under `HKCU\...\Run\MicrosoftUpdate`.

## Key Findings

| # | Question | Answer |
|---|----------|--------|
| 1 | Malicious file (first stage) | `setup.js` |
| 2 | Malicious package | `simple-crypto-js` |
| 3 | Top-level compromised package | `axios` |
| 4 | Exfil and payload domain | `rustf.htb` |
| 5 | VBScript filename | `6202033.vbs` |
| 6 | Original binary name | `powershell.exe` |
| 7 | MITRE ATT&CK technique | `T1195.001` |
| 8 | Registry persistence key | `HKCU\Software\Microsoft\Windows\CurrentVersion\Run` |

- The attacker operated a private npm-compatible registry to serve the trojanized package, exploiting developer trust in package version pinning.
- Renaming `powershell.exe` to `wt.exe` bypasses name-based process monitoring rules.
- Persistence via HKCU Run key requires no elevated privileges and survives reboots.

## Final Answer
All 8 answers are in the table in the Walkthrough section.

## Lessons Learned
npm postinstall scripts execute automatically during package installation with the developer's full privileges, making them an effective first-stage execution vector. Pinning package versions alone is insufficient; the registry source and package integrity (via lockfile hash verification or npm audit signatures) must also be validated. T1195.001 attacks exploit trust in the development toolchain rather than the production environment, and are often invisible to endpoint controls that monitor only production hosts. Monitoring for unusual binary renames and HKCU Run key modifications on developer workstations is an effective detection layer.
