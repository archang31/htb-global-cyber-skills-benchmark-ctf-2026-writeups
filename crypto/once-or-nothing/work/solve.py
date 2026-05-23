#!/usr/bin/env python3
"""
Lamport signature forgery attack on "once_or_nothing".

Attack:
  1. Sign all-zeros msg -> get s0[i] for every bit position
  2. Sign all-ones  msg -> get s1[i] for every bit position
  3. For target "d9_netadmin", pick s0[i] or s1[i] per bit and forge a token
"""

import re
import socket
import subprocess
import sys
import threading

TARGET_MSG = "d9_netadmin"
N = 256
BINARY = "/home/kali/ctfs/htb/crypto/once-or-nothing/crypto_once_or_nothing/target/debug/once_or_nothing"


def msg_to_bits(msg_bytes: bytes) -> list[int]:
    padded = b"\x00" * (N // 8 - len(msg_bytes)) + msg_bytes[: N // 8]
    bits = []
    for byte in padded:
        for shift in range(7, -1, -1):
            bits.append((byte >> shift) & 1)
    return bits


def parse_token(output: str | bytes) -> list[str]:
    if isinstance(output, bytes):
        output = output.decode(errors="replace")
    matches = re.findall(r"Uint\(0x([0-9A-Fa-f]+)\)", output)
    assert len(matches) == N, f"Expected {N} token segments, got {len(matches)}"
    return [m.upper().zfill(64) for m in matches]


class Connection:
    """Wraps a binary subprocess or TCP socket for interactive I/O."""

    def __init__(self, proc=None, sock=None):
        self._proc = proc
        self._sock = sock
        self._buf = b""
        self._lock = threading.Lock()
        if proc:
            self._reader_thread = threading.Thread(target=self._read_loop, daemon=True)
            self._reader_thread.start()

    def _read_loop(self):
        raw = self._proc.stdout.raw
        while True:
            chunk = raw.read(4096)
            if not chunk:
                break
            with self._lock:
                self._buf += chunk

    def recv_until(self, marker: bytes, timeout: float = 30) -> bytes:
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
                chunk = self._sock.recv(4096)
                if chunk:
                    with self._lock:
                        self._buf += chunk
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
            self._sock.close()


def attack(conn: Connection) -> str:
    target_bits = msg_to_bits(TARGET_MSG.encode())
    zeros_hex = "00" * (N // 8)
    ones_hex = "ff" * (N // 8)

    conn.recv_until(b"> ")

    # Step 1: sign all-zeros -> s0[i]
    conn.send("1")
    conn.recv_until(b"hex: ")
    conn.send(zeros_hex)
    raw0 = conn.recv_until(b"> ")
    token_zeros = parse_token(raw0)
    print(f"[+] s0[0] = {token_zeros[0][:16]}...")

    # Step 2: sign all-ones -> s1[i]
    conn.send("1")
    conn.recv_until(b"hex: ")
    conn.send(ones_hex)
    raw1 = conn.recv_until(b"> ")
    token_ones = parse_token(raw1)
    print(f"[+] s1[0] = {token_ones[0][:16]}...")

    # Step 3: forge token
    forged = [token_zeros[i] if bit == 0 else token_ones[i] for i, bit in enumerate(target_bits)]
    token_str = ",".join(forged)
    print(f"[*] Forged token ({len(token_str)} chars), submitting...")

    # Step 4: validate
    conn.send("2")
    conn.recv_until(b"message to validate: ")
    conn.send(TARGET_MSG)
    conn.recv_until(b"comma-separated hex): ")
    conn.send(token_str)
    result = conn.recv_until(b"> ")

    conn.send("3")
    return result.decode(errors="replace")


def main():
    target_bits = msg_to_bits(TARGET_MSG.encode())
    print(f"[*] Target bits 168-207: {''.join(str(b) for b in target_bits[168:208])}")

    if len(sys.argv) == 3:
        host, port = sys.argv[1], int(sys.argv[2])
        print(f"[*] Connecting to {host}:{port}")
        sock = socket.create_connection((host, port), timeout=30)
        conn = Connection(sock=sock)
    else:
        print(f"[*] Spawning local binary: {BINARY}")
        proc = subprocess.Popen(
            [BINARY],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        )
        conn = Connection(proc=proc)

    result = attack(conn)
    conn.close()

    print("[+] Server response:")
    print(result)


if __name__ == "__main__":
    main()
