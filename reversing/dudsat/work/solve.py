#!/usr/bin/env python3
"""
Dudsat solve script.
Recovers the flag from comms.dat by rebuilding the LCG S-box and computing
Doppler residuals for each of the 26 observation records.
"""
import struct


def lcg_next(state):
    return (state * 0x19660D + 0x3C6EF35F) & 0xFFFFFFFF


def build_sbox():
    sbox = list(range(256))
    state = 0x20FC8
    for i in range(255, -1, -1):
        state = lcg_next(state)
        j = state % (i + 1)
        sbox[i], sbox[j] = sbox[j], sbox[i]
    return sbox


def decode(path="comms.dat"):
    sbox = build_sbox()
    data = open(path, "rb").read()
    C = 418229116.0
    flag = []
    for i in range(len(data) // 48):
        rec = data[i * 48:(i + 1) * 48]
        ts, f0, range_rate, f_recv, elev, snr, idx = struct.unpack("<QdddffQ", rec)
        residual = f_recv - f0 * (1.0 + range_rate / C)
        flag.append(chr(sbox[int(residual) & 0xFF]))
    print("".join(flag))


if __name__ == "__main__":
    import sys
    decode(sys.argv[1] if len(sys.argv) > 1 else "comms.dat")
