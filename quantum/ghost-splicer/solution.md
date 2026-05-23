# Ghost Splicer

## Category
Quantum

## Difficulty
Medium

## Summary
A quantum teleportation API exposes 16 rounds of entanglement swapping. Correctly applying
Pauli corrections after each ceremony and teleport round maintains fidelity of 1.0 across all
rounds and unlocks the flag.

## Provided Files
- quantum_ghost_splicer.zip

## Tools Used
- Python 3
- requests

## Walkthrough

The challenge simulates quantum entanglement swapping and teleportation over 16 rounds. Each
round has two phases.

**Phase 1: fire_ceremony (entanglement swap)**

The server returns classical measurement results `s1` and `s2`. The standard entanglement
swapping correction is Z^s1 X^s2 applied to the receiver qubit (qubit 4).

**Phase 2: teleport_round (quantum teleportation)**

The server returns classical bits `c1` and `c2` from the Bell measurement. The standard
teleportation correction is Z^c1 X^c2 applied to qubit 4.

**Per-round protocol:**

1. POST `/api/prepare` with `phantom_state="PLUS"`
2. POST `/api/braid` with `gate="CNOT"`, `control=4`, `target=1`
3. POST `/api/ceremony` to get `s1`, `s2`; apply Z^s1 X^s2 correction
4. POST `/api/correct_swap` with the computed gate sequence
5. POST `/api/teleport_round` to get `c1`, `c2`; apply Z^c1 X^c2 correction
6. POST `/api/submit` with the gate sequence

**Gate sequence helper:**

```python
def gate_seq(z, x, qubit=4):
    seq = []
    if z:
        seq.append({'gate': 'Z', 'qubit': qubit})
    if x:
        seq.append({'gate': 'X', 'qubit': qubit})
    return seq or [{'gate': 'I', 'qubit': qubit}]
```

**Full exploit:**

```python
import requests

BASE = "http://<target-ip>:<target-port>/api"

r = requests.post(f"{BASE}/session")
data = r.json()
sid = data['session_id']

for rnd in range(data['rounds_required']):
    requests.post(f"{BASE}/prepare",
                  json={"session_id": sid, "phantom_state": "PLUS"})
    requests.post(f"{BASE}/braid",
                  json={"session_id": sid, "gate": "CNOT", "control": 4, "target": 1})
    cer = requests.post(f"{BASE}/ceremony", json={"session_id": sid}).json()
    requests.post(f"{BASE}/correct_swap",
                  json={"session_id": sid, "gate_sequence": gate_seq(cer['s1'], cer['s2'])})
    tel = requests.post(f"{BASE}/teleport_round", json={"session_id": sid}).json()
    sub = requests.post(f"{BASE}/submit",
                        json={"session_id": sid,
                              "gate_sequence": gate_seq(tel['c1'], tel['c2'])}).json()
    print(sub)
```

## Key Findings

- Standard quantum teleportation correction: Z^c1 X^c2 applied to the receiver qubit (qubit 4)
- Standard entanglement swapping correction: Z^s1 X^s2 applied after `fire_ceremony`
- Fidelity 1.0 is achievable deterministically because the Pauli corrections are exact, not
  probabilistic
- 16 rounds with fidelity 1.0 unlocks the flag

## Final Answer

`Flag: HTB{gh0st_1n_th3_sw4p_1s_n3v3r_4l0n3}`

## Lessons Learned

Quantum teleportation and entanglement swapping follow deterministic Pauli correction rules
derived from classical measurement outcomes. Implementing the standard correction protocol
exactly as specified in quantum information theory produces perfect fidelity in the absence of
noise. The key insight is that the classical bits transmitted after each measurement fully
determine which Pauli operator restores the quantum state.
