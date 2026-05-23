#!/usr/bin/env python3
"""Operator Silence solver v2 — correct measurement parsing"""
import requests
from fractions import Fraction
from collections import Counter

BASE = "http://<target-ip>:<target-port>"
SID = "kali-solve-main"  # continue same session (already used 1 shot)
HEADERS = {"X-Session-Id": SID, "Content-Type": "application/json"}

def get(path):
    return requests.get(f"{BASE}{path}", headers=HEADERS).json()

def post(path, data):
    return requests.post(f"{BASE}{path}", headers=HEADERS, json=data).json()

N_CONTROL = 512
N_TARGET = 256
N_BITS = 256
MAX_R = 2**256

def build_qpe():
    gates = [{"op": "x", "qubit": N_CONTROL}]
    for j in range(N_CONTROL):
        gates.append({"op": "h", "qubit": j})
    gates.append({"op": "controlled_modexp"})
    gates.append({"op": "qft_inverse"})
    gates.append({"op": "measure_all"})
    return gates

def parse_shot(result):
    bits = result.get("shot", "")
    if not bits:
        return None
    # little-endian: bits[0]=2^0, bits[1]=2^1, ... => reverse for int()
    return int(bits[::-1], 2)

def cf_candidates(m, max_r):
    """Continued fraction convergents of m/2^512 with denominator <= max_r."""
    if m == 0:
        return []
    phase = Fraction(m, 2**N_CONTROL)
    approx = phase.limit_denominator(max_r)
    return [approx.denominator] if approx.denominator > 1 else []

def main():
    session = get("/session")
    circuit_budget = session["circuit_budget_remaining"]
    classical_budget = session["classical_budget_remaining"]
    print(f"Budget: circuit={circuit_budget}, classical={classical_budget}")

    gates = build_qpe()
    measurements = []

    for shot_num in range(circuit_budget):
        result = post("/circuit", {"gates": gates})
        if "error" in result:
            print(f"Error: {result['error']}")
            break

        noise_flag = result.get("noise_flag", False)
        budget_left = result.get("budget_left", 0)
        m = parse_shot(result)
        print(f"Shot {shot_num+1}: noise={noise_flag}, m={hex(m) if m else None}, budget_left={budget_left}")

        if not noise_flag and m is not None and m > 0:
            measurements.append(m)

        if budget_left <= 0:
            break

    print(f"\n=== {len(measurements)} clean measurements ===")

    if not measurements:
        print("No clean measurements!")
        return

    # Collect order candidates via continued fractions
    order_counts = Counter()
    for m in measurements:
        for c in cf_candidates(m, MAX_R):
            order_counts[c] += 1
        print(f"  m=0x{m:x}: candidates={cf_candidates(m, MAX_R)}")

    print(f"\nTop candidates: {order_counts.most_common(10)}")

    # Also try LCM of top candidates
    from math import lcm
    top10 = [r for r, _ in order_counts.most_common(10)]
    if len(top10) >= 2:
        lcm_val = top10[0]
        for x in top10[1:4]:
            lcm_val = lcm(lcm_val, x)
        if lcm_val != top10[0] and lcm_val <= MAX_R:
            top10.insert(1, lcm_val)
            print(f"LCM candidate: {lcm_val}")

    # Verify with classical_eval
    verified_r = None
    classical_left = classical_budget
    for r_cand in top10[:classical_budget]:
        if classical_left <= 0:
            break
        ev = post("/classical_eval", {"x": r_cand})
        classical_left -= 1
        is_ann = ev.get("is_annihilator", False)
        print(f"  g^{r_cand} ≡ 1? {is_ann} (budget_left={ev.get('classical_budget_left')})")
        if is_ann:
            verified_r = r_cand
            break

    if verified_r is None and top10:
        verified_r = top10[0]
        print(f"No classical verification, using best guess: {verified_r}")

    if verified_r is None:
        print("No candidate found!")
        return

    # Try to find minimal order
    r = verified_r
    while classical_left > 0 and r % 2 == 0:
        r_half = r // 2
        ev = post("/classical_eval", {"x": r_half})
        classical_left -= 1
        if ev.get("is_annihilator"):
            r = r_half
            print(f"Reduced r to {r}")
        else:
            break

    print(f"\nSubmitting r={r}")
    vr = post("/verify", {"order": r})
    print(f"Verify result: {vr}")

    if vr.get("flag"):
        print(f"\n FLAG: {vr['flag']}")
    elif vr.get("status") == "accepted":
        print(f"Accepted: {vr}")
    elif "halve" in str(vr.get("reason", "")):
        r //= 2
        print(f"Halving to r={r}")
        vr2 = post("/verify", {"order": r})
        print(f"Verify2: {vr2}")
        if vr2.get("flag"):
            print(f"\n FLAG: {vr2['flag']}")
    else:
        print(f"Rejected: {vr}")

if __name__ == "__main__":
    main()
