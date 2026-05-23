# Orion

## Category
FullPwn (User + Root)

## Difficulty
Easy

## Challenge Description

N/A

**Creator:** yuriD

## Summary
A two-flag machine. User access is obtained via SSH with credentials discovered through enumeration. Root is achieved by exploiting CVE-2026-24061, an authentication bypass in GNU inetutils telnetd running on localhost, where the USER environment variable is passed unsanitized to PAM autologin.

## Provided Files
None (live machine)

## Tools Used
- SSH
- sshpass
- telnet

## Walkthrough

### User Flag

Enumerate the machine and identify the SSH service. The user account `adam` has credentials discoverable through standard enumeration.

```bash
sshpass -p 'darkangel' ssh adam@<target-ip>
cat ~/user.txt
```

### Root Flag

Once inside, inspect running services. GNU inetutils telnetd is running on localhost port 23, and the installed version is affected by CVE-2026-24061.

CVE-2026-24061 is an authentication bypass. The inetutils telnetd reads the USER environment variable to determine the autologin username and passes it directly to the PAM autologin mechanism without sanitizing a leading dash. Setting `USER="-f root"` causes the value to be interpreted as a flag argument (`-f root`) by the underlying `login` call, bypassing password authentication entirely.

The `telnet -a` flag triggers automatic login using the current USER value:

```bash
USER="-f root" telnet -a 127.0.0.1 23
cat /root/root.txt
```

## Key Findings
- GNU inetutils telnetd interprets the USER environment variable without sanitizing a leading dash, allowing flag injection into the autologin path
- The `-a` flag in telnet triggers automatic login using the current USER environment variable value
- Telnetd running as root on localhost with no reconnection restriction is the privilege escalation path

## Final Answer
User flag: `HTB{Cr4ftyB3ginnIngS/}`
Root flag: `HTB{T3ln3tIs0utD4t3D!}`

## Lessons Learned
Legacy network services like telnetd should never run as root, even on loopback interfaces. Environment variable injection into authentication libraries (PAM) is a well-known attack class; argument validation must be enforced before passing user-controlled values to system calls. The pattern of prepending a dash to user-controlled input to inject flags into downstream executables appears across many CVEs and should be a standard code review check for any code that interpolates external input into a command invocation.
