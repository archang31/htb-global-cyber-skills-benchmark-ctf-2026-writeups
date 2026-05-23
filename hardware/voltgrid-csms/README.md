# VoltGrid CSMS

## Category
Hardware

## Difficulty
Hard

## Challenge Description

Below the threshold of war, critical infrastructure is the bargaining surface. Infiltrate the VoltGrid CSMS to sever state-backed proxy access. Demonstrate your control by halting the active transaction at Monastiraki Station for exactly one minute.

**Creator:** Xclow3n

## Summary
A WebAuthn-protected EV charging station management system (CSMS) using OCPP exposes two chained vulnerabilities: a WebAuthn credential ownership bypass that grants admin authentication, followed by an OCPP WebSocket session hijack that forces the server to return the flag after holding the connection open for 70 seconds.

## Provided Files
None (Docker instance only)

## Tools Used
- Python 3
- cbor2
- fido2

## Walkthrough

### Part 1: WebAuthn Authentication Bypass

The `/login/begin` endpoint accepts a `username` parameter and returns a challenge. The `allowCredentials` field in the response is set to `[]`, meaning any credential is accepted. The server verifies that the submitted signature is cryptographically valid but does not check whether the submitted credential ID belongs to the claimed user.

Attack steps:
1. Register a new account with a self-generated EC P-256 keypair
2. Call `/login/begin` with `username=admin` to receive the admin's challenge
3. Sign the challenge with the attacker's private key
4. Submit the attacker's `credentialId` in the authentication response

The server accepts the signature (valid against the attacker's registered public key) and grants a session as `admin`.

### Part 2: OCPP Session Hijack

The Monastiraki Station connects to the CSMS via WebSocket at:

```
ws://<target-ip>:<target-port>/a8e1d4c9-52f7-4b3a-b6e0-9d2c8f1a7e35
```

The endpoint is secured only by the UUID in the URL. Connecting to this path kicks the legitimate station off the WebSocket.

Sequence after connecting:
1. Send `BootNotification` to register the attacker as the station
2. Send `StopTransaction` with `txn_id=1001` to close any active session
3. Send `StatusNotification` with status `Available`
4. Reject any `RemoteStartTransaction` requests from the server
5. Hold the connection open for 70 seconds to prevent the legitimate station from reconnecting

After 60 seconds of continuous control, poll `/api/flag` to retrieve the flag.

```bash
pip install cbor2 fido2
python3 work/hold_connection.py
```

## Key Findings
- WebAuthn's security model requires that the server validate the credential ID against the user's registered credentials; the missing ownership check is a critical implementation flaw
- OCPP station endpoints are identified only by a UUID in the WebSocket path; there is no mutual TLS or token-based authentication
- Holding the WebSocket connection prevents the legitimate station from re-establishing, giving the attacker persistent control

## Final Answer
`Flag: HTB{p4ssk3y_1llus10ns_&_ocpp_c0nfu510ns}`

## Lessons Learned
WebAuthn implementations must validate credential ownership, not just signature validity. A valid signature from any registered credential is not sufficient proof of identity for a specific user. OCPP endpoints secured only by a UUID in the URL are vulnerable to session hijacking by any party who learns the URL; mutual TLS or per-session token authentication is required for production deployments. Timing-dependent flags (requiring sustained control) are common in ICS challenges and reflect real-world scenarios where an attacker must maintain access to achieve an objective.
