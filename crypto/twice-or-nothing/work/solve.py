#!/usr/bin/env python3
"""
Lamport forgery against "twice_or_nothing".

Fix from previous challenge: the message is SHA-256 hashed before bit-indexing,
and only 6 signing queries are allowed (BURN_LIMIT = 5, check is > 5).

Attack — set cover:
  H_target = SHA256("d9_netadmin")  (fixed, 256 bits)
  Each signing query for message M reveals:
      token[i] = s_{SHA256(M)[i]}[i]   for i in 0..255
  A query is "useful" for position i if SHA256(M)[i] == H_target[i].

  Goal: find ≤6 messages that, together, are useful for EVERY position.
  Strategy:
    - 5 greedy rounds: each tries 50k random messages, keeps the one
      covering the most remaining uncovered positions.
    - 1 brute-force round (if needed): random search until the remaining
      few positions (typically <8) are all covered in one hash.
"""

import hashlib
import os
import re
import socket
import subprocess
import sys
import threading

TARGET_MSG  = "d9_netadmin"
N           = 256
MAX_QUERIES = 6          # BURN_LIMIT=5 → issue_count 0..5 → 6 total issues
BINARY = (
    "/home/kali/ctfs/htb/crypto/twice-or-nothing"
    "/crypto_twice_or_nothing/target/debug/twice_or_nothing"
)


# ── crypto helpers ────────────────────────────────────────────────────────────

def sha256_bits(data: bytes) -> list[int]:
    h = hashlib.sha256(data).digest()
    bits = []
    for byte in h:
        for shift in range(7, -1, -1):
            bits.append((byte >> shift) & 1)
    return bits


def parse_token(output: str | bytes) -> list[str]:
    if isinstance(output, bytes):
        output = output.decode(errors="replace")
    matches = re.findall(r"Uint\(0x([0-9A-Fa-f]+)\)", output)
    assert len(matches) == N, f"Expected {N} token segments, got {len(matches)}"
    return [m.upper().zfill(64) for m in matches]


# ── offline set-cover search ──────────────────────────────────────────────────

def find_cover_messages(target_bits: list[int]) -> list[bytes]:
    """Return ≤ MAX_QUERIES messages whose SHA-256 hashes cover all 256 positions."""
    uncovered = set(range(N))
    messages  = []

    for rnd in range(MAX_QUERIES - 1):
        if not uncovered:
            break
        best_msg   = None
        best_cover = frozenset()

        for _ in range(50_000):
            msg    = os.urandom(32)
            h_bits = sha256_bits(msg)
            cover  = frozenset(i for i in uncovered if h_bits[i] == target_bits[i])
            if len(cover) > len(best_cover):
                best_cover = cover
                best_msg   = msg
                if len(best_cover) == len(uncovered):
                    break  # perfect — stop early

        messages.append(best_msg)
        uncovered -= best_cover
        print(f"  round {rnd+1}: covered {len(best_cover):3d} → {len(uncovered):3d} remaining")

    # Final brute-force pass for whatever is left (usually 0–8 positions)
    if uncovered:
        constraints = [(i, target_bits[i]) for i in sorted(uncovered)]
        print(f"  brute-force: targeting {len(constraints)} positions …", end="", flush=True)
        tries = 0
        while True:
            msg    = os.urandom(32)
            h_bits = sha256_bits(msg)
            if all(h_bits[i] == b for i, b in constraints):
                messages.append(msg)
                print(f" found after {tries:,} tries")
                break
            tries += 1

    assert len(messages) <= MAX_QUERIES, "Need more queries than allowed"
    return messages


# ── interactive I/O ───────────────────────────────────────────────────────────

class Connection:
    """Wraps a subprocess or TCP socket for interactive I/O."""

    def __init__(self, proc=None, sock=None):
        self._proc = proc
        self._sock = sock
        self._buf  = b""
        self._lock = threading.Lock()
        if proc:
            t = threading.Thread(target=self._read_loop, daemon=True)
            t.start()

    def _read_loop(self):
        raw = self._proc.stdout.raw
        while True:
            chunk = raw.read(4096)
            if not chunk:
                break
            with self._lock:
                self._buf += chunk

    def recv_until(self, marker: bytes, timeout: float = 60) -> bytes:
        import time
        deadline = time.monotonic() + timeout
        while True:
            with self._lock:
                idx = self._buf.find(marker)
                if idx != -1:
                    data = self._buf[: idx + len(marker)]
                    self._buf = self._buf[idx + len(marker):]
                    return data
            if time.monotonic() > deadline:
                raise TimeoutError(f"Timeout waiting for {marker!r}")
            if self._sock:
                try:
                    chunk = self._sock.recv(4096)
                    if chunk:
                        with self._lock:
                            self._buf += chunk
                except Exception:
                    pass
            else:
                time.sleep(0.01)

    def send(self, data: str):
        raw = (data + "\n").encode()
        if self._proc:
            self._proc.stdin.write(raw)
            self._proc.stdin.flush()
        else:
            self._sock.sendall(raw)

    def close(self):
        if self._proc:
            try:
                self._proc.stdin.close()
                self._proc.wait(timeout=5)
            except Exception:
                pass
        if self._sock:
            try:
                self._sock.close()
            except Exception:
                pass


# ── main attack ───────────────────────────────────────────────────────────────

def attack(conn: Connection, query_messages: list[bytes]) -> str:
    target_bits = sha256_bits(TARGET_MSG.encode())

    # Sign each query message and collect tokens
    conn.recv_until(b"> ")
    tokens = []
    for i, msg in enumerate(query_messages):
        hex_msg = msg.hex()
        conn.send("1")
        conn.recv_until(b"hex: ")
        conn.send(hex_msg)
        raw = conn.recv_until(b"> ")
        raw_str = raw.decode(errors="replace")
        if "BURNOUT" in raw_str or "REJECTED" in raw_str:
            raise RuntimeError(f"Query {i} rejected/burned: {raw_str[:80]}")
        tok = parse_token(raw_str)
        tokens.append(tok)
        print(f"  [+] token {i+1}/{len(query_messages)}: {tok[0][:16]}…")

    # Build source map: position i → which query index gave the right secret
    source = {}
    for j, msg in enumerate(query_messages):
        h_bits = sha256_bits(msg)
        for i in range(N):
            if i not in source and h_bits[i] == target_bits[i]:
                source[i] = j

    assert len(source) == N, f"Only {len(source)}/256 positions covered!"

    # Forge token
    forged    = [tokens[source[i]][i] for i in range(N)]
    token_str = ",".join(forged)
    print(f"[*] Forged token ({len(token_str):,} chars), submitting…")

    conn.send("2")
    conn.recv_until(b"message to validate: ")
    conn.send(TARGET_MSG)
    conn.recv_until(b"comma-separated hex): ")
    conn.send(token_str)
    result = conn.recv_until(b"> ")

    conn.send("3")
    return result.decode(errors="replace")


def main():
    target_bits = sha256_bits(TARGET_MSG.encode())
    print(f"[*] H_target = {hashlib.sha256(TARGET_MSG.encode()).hexdigest()}")
    print(f"    ones={sum(target_bits)}, zeros={256-sum(target_bits)}")

    print("[*] Finding cover messages offline…")
    cover_msgs = find_cover_messages(target_bits)
    print(f"[+] {len(cover_msgs)} messages needed")

    if len(sys.argv) == 3:
        host, port = sys.argv[1], int(sys.argv[2])
        print(f"[*] Connecting to {host}:{port}")
        sock = socket.create_connection((host, port), timeout=30)
        conn = Connection(sock=sock)
    else:
        print(f"[*] Spawning local binary")
        proc = subprocess.Popen(
            [BINARY],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        )
        conn = Connection(proc=proc)

    result = attack(conn, cover_msgs)
    conn.close()

    print("[+] Server response:")
    print(result)


if __name__ == "__main__":
    import hashlib
    main()
