# Global Cyber Skills Benchmark CTF 2026: Project Nightfall Writeups

This repository contains public writeups for challenges solved during the Hack The Box Global Cyber Skills Benchmark CTF 2026: Project Nightfall. All solutions were completed in an authorized, competitive environment. Flags, credentials, and environment-specific values are redacted throughout.

---

## Event Information

| Field | Value |
|-------|-------|
| Event | Global Cyber Skills Benchmark CTF 2026: Project Nightfall |
| Platform | Hack The Box |
| Start | May 15, 2026, 09:00 AM UTC |
| End | May 20, 2026, 09:00 AM UTC |
| Event Page | https://ctf.hackthebox.com/event/details/global-cyber-skills-benchmark-ctf-2026-project-nightfall-3296 |
| Scoreboard | https://ctf.hackthebox.com/event/3296/scoreboard |

---

## About Project Nightfall

"Secure the dependencies. Save the state."

In a world where influence is measured by control of shared dependencies rather than territory, Project Nightfall represents the front line of nation-state cyber operations. Rival coalitions and APT units have spent years embedded within virtualization stacks, identity providers, and supplier ecosystems to gain strategic leverage. While state-enabled proxies launch high-visibility distractions, the true threat remains deniable, quietly shaping infrastructure from within.

As part of Task Force Nightfall, the mission was to embed within critical infrastructure operators, root out deep-seated persistence in vendor tooling, and maintain national resilience against rising global interference.

---

## Results

![Project Nightfall Event Banner](assets/project-nightfall-banner.jpg)

![Results: ATA — Global Rank #65, US Rank #13, Score 65,125, Flags 111/126](assets/results.png)

---

## Repository Structure

Each challenge folder follows this layout:

```
<category>/<challenge-name>/
  solution.md     - Polished writeup: Summary, Walkthrough, Key Findings, Lessons Learned
  work/           - Solve scripts and helper tools used during the solve
  screenshots/    - Images referenced in the writeup (if applicable)
```

Challenge-provided artifacts (binaries, archives, PCAPs, disk images) are not committed to this repository due to file size and licensing. Each writeup lists what was provided.

---

## Writeups

| Challenge | Category | Status |
|-----------|----------|--------|
| [Lotus Registry](ai/lotus-registry/solution.md) | AI | Solved |
| [Grant Registry](blockchain/grant-registry/solution.md) | Blockchain | Solved |
| [Exposed Supply](cloud/exposed-supply/solution.md) | Cloud | Solved |
| [Ghost Access](cloud/ghost-access/solution.md) | Cloud | Solved |
| [Privilege Chain](cloud/privilege-chain/solution.md) | Cloud | Solved |
| [Cascade Depth](coding/cascade-depth/solution.md) | Coding | Solved |
| [Checksum Mismatch](coding/checksum-mismatch/solution.md) | Coding | Solved |
| [Choke Point](coding/choke-point/solution.md) | Coding | Solved |
| [Incident Window](coding/incident-window/solution.md) | Coding | Solved |
| [Surge Protocol](coding/surge-protocol/solution.md) | Coding | Solved |
| [Once or Nothing](crypto/once-or-nothing/solution.md) | Cryptography | Solved |
| [Pow Pow](crypto/pow-pow/solution.md) | Cryptography | Solved |
| [Twice or Nothing](crypto/twice-or-nothing/solution.md) | Cryptography | Solved |
| [COMfortable Exfiltration](forensics/comfortable-exfiltration/solution.md) | Forensics | Solved |
| [Open Wound](forensics/open-wound/solution.md) | Forensics | Solved |
| [Stay Hydrated](forensics/stay-hydrated/solution.md) | Forensics | Solved |
| [The Gilded Ghost](forensics/the-gilded-ghost/solution.md) | Forensics | Solved |
| [Trust and Betrayal](forensics/trust-and-betrayal/solution.md) | Forensics | Solved |
| [Orion](fullpwn/orion/solution.md) | FullPwn | Solved |
| [NECVISION](hardware/necvision/solution.md) | Hardware | Solved |
| [VoltGrid CSMS](hardware/voltgrid-csms/solution.md) | Hardware | Solved |
| [Sector Blackout](ics/sector-blackout/solution.md) | ICS | Solved |
| [Watermark](ml/watermark/solution.md) | Machine Learning | Solved |
| [Flashpoint](pwn/flashpoint/solution.md) | Pwn | Solved |
| [Relay](pwn/relay/solution.md) | Pwn | Solved |
| [Unverified Patch](pwn/unverified-patch/solution.md) | Pwn | Solved |
| [Ghost Splicer](quantum/ghost-splicer/solution.md) | Quantum | Solved |
| [Operator Silence](quantum/operator-silence/solution.md) | Quantum | Solved |
| [Dudsat](reversing/dudsat/solution.md) | Reverse Engineering | Solved |
| [Sysprobe](reversing/sysprobe/solution.md) | Reverse Engineering | Solved |
| [Ariadne's Hand](secure-coding/ariadnes-hand/solution.md) | Secure Coding | Solved |
| [Le Paradis et L'Enfer](secure-coding/le-paradis-et-lenfer/solution.md) | Secure Coding | Solved |
| [The Dark Night](secure-coding/the-dark-night/solution.md) | Secure Coding | Solved |
| [Trust Fall](web/trust-fall/solution.md) | Web | Solved |

---

## Disclaimer

All writeups in this repository were produced during an authorized, time-limited Capture the Flag competition hosted by Hack The Box. The techniques described are shared for educational purposes and to advance understanding of offensive and defensive security. None of the techniques described here should be applied against systems without explicit written authorization from the system owner.
