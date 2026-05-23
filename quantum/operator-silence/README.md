# Operator Silence

## Category
Quantum

## Difficulty
Hard

## Challenge Description

a cryogenic photonic implant codenamed **GLASSWING** has been seated inside a Halcyon Dynamics HELIX HSM. The HSM co-signs every firmware bundle a hostile mining consortium pushes to its fleet, and its anti-replay counter-signature module rides on the multiplicative order `r` of a secret `g` modulo a secret semiprime `N`. GLASSWING cannot read `N`, cannot read `g`, cannot read `r`  the tamper cage refuses  but it _can_ schedule our gates on top of the HSM's own order-finding circuit and relay one measurement shot back to us out-of-band.

**Creator:** Xclow3n

## Summary
A quantum order-finding service simulates Shor's algorithm with 512 qubits. Submitting the
correct order `r` such that the modular exponentiation gate becomes the identity
(`is_annihilator` is true) retrieves the flag. The period is extracted from quantum phase
estimation output via continued fraction approximation.

## Provided Files
- hardware_quantum_operator_silence.zip

## Tools Used
- Python 3
- requests
- fractions (stdlib)

## Walkthrough

The challenge exposes a `/circuit` endpoint that runs a full Shor-style quantum circuit
(Hadamard, controlled_modexp, QFT_inverse, measure_all) and returns measurement shots. The
period `r` is extracted via continued fraction approximation of the measured value divided by
2^512.

**Circuit construction:**

The eigenstate qubit (qubit 512) is initialized with an X gate. All 512 control qubits receive
Hadamard gates. The circuit then applies `controlled_modexp`, `qft_inverse`, and `measure_all`
in sequence.

**Post-processing:**

The QFT output concentrates probability at multiples of 2^512 / r. For each valid measurement
`m`, computing `Fraction(m, 2^512).limit_denominator(2^256)` recovers a fraction whose
denominator is a candidate for `r`. Voting across multiple shots and selecting the most
frequent denominator gives a robust estimate. Noisy shots (flagged by `noise_flag`) and zero
measurements are discarded.

**Full exploit:**

```python
import requests
from fractions import Fraction
from collections import Counter

BASE = "http://<target-ip>:<target-port>"
HEADERS = {"X-Session-Id": "solve", "Content-Type": "application/json"}

gates = [{"op": "x", "qubit": 512}]
for j in range(512):
    gates.append({"op": "h", "qubit": j})
gates += [{"op": "controlled_modexp"}, {"op": "qft_inverse"}, {"op": "measure_all"}]

measurements = []
for _ in range(15):
    r = requests.post(f"{BASE}/circuit", headers=HEADERS, json={"gates": gates}).json()
    if not r.get("noise_flag") and r.get("shot"):
        m = int(r["shot"][::-1], 2)
        if m > 0:
            measurements.append(m)

order_counts = Counter()
for m in measurements:
    approx = Fraction(m, 2**512).limit_denominator(2**256)
    if approx.denominator > 1:
        order_counts[approx.denominator] += 1

for r_cand, _ in order_counts.most_common():
    ev = requests.post(f"{BASE}/classical_eval",
                       headers=HEADERS, json={"x": r_cand}).json()
    if ev.get("is_annihilator"):
        result = requests.post(f"{BASE}/verify",
                               headers=HEADERS, json={"order": r_cand}).json()
        print(result["flag"])
        break
```

## Key Findings

- The QFT output concentrates probability at multiples of 2^512 / r; continued fraction
  expansion recovers `r` from any such multiple
- The `noise_flag` field identifies shots corrupted by simulated quantum noise; these must be
  discarded before post-processing
- Multiple shots are needed because a single measurement may land on a multiple of 2^512 / r
  with a non-coprime numerator, masking the true period
- Voting across 15 shots and taking the most frequent denominator gives a robust period estimate
- Bit reversal of the measurement string is required because the server returns qubits in
  little-endian order

## Final Answer

`Flag: HTB{sh0r_0rd3r_f0und_m0dul4r_p3r10d_r3c0v3r3d}`

## Lessons Learned

Shor's algorithm extracts the period `r` via quantum phase estimation followed by continued
fraction reduction. The classical post-processing (fraction reduction, majority voting) is as
important as the quantum circuit itself. Real quantum hardware requires many more shots to
overcome noise; the challenge models this with the `noise_flag` mechanism. Discarding noisy
shots rather than attempting to correct them is the correct approach when the noise model is
unknown.
