#!/usr/bin/env python3
"""
Exploit: ledger_hash(data) = (a * bytes_to_long(data) + b) % n is linear.

For each block we need:
  hash = (a * bytes_to_long(prev_hash_bytes + blockdata + nonce) + b) % n
       = (a * (prefix_int * 2^256 + nonce_int) + b) % n  == 0  (mod n)

Solve algebraically: nonce_int = -a_inv * (a * prefix_int * 2^256 + b) mod n
Then decrypt the flag the same way (one more linear inversion).
"""
from hashlib import sha256
from Crypto.Util.number import long_to_bytes, bytes_to_long
import socket
import re

HOST = '<target-ip>'
PORT = 30783

GENESIS = sha256(b"Korvia command channel genesis").digest()
BATCH_MARKER = b'Validate proxy transaction batch:\n'
PROMPT       = b'Enter block nonce in hex: '
END_MARKER   = b'\n\nEnter block nonce in hex: '


def connect():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((HOST, PORT))
    s.settimeout(20)
    return s


def recv_until(s, marker, buf):
    """Read from s until marker is in buf. Returns (data_up_to_marker, leftover)."""
    while marker not in buf:
        chunk = s.recv(4096)
        if not chunk:
            raise ConnectionError("closed")
        buf += chunk
    idx = buf.index(marker) + len(marker)
    return buf[:idx], buf[idx:]


def solve():
    s = connect()
    buf = b''

    # Banner
    data, buf = recv_until(s, b'\n', buf)
    print(data.decode().strip())

    # Parameters line
    data, buf = recv_until(s, b'\n', buf)
    print(data.decode().strip())

    m = re.search(rb'a = (\d+), b = (\d+) and n = (\d+)', data)
    a, b_val, n = int(m.group(1)), int(m.group(2)), int(m.group(3))

    a_inv         = pow(a, -1, n)
    pow2_256_modn = pow(2, 256, n)

    prev_hash = (a * bytes_to_long(GENESIS) + b_val) % n

    for block_num in range(100):
        chunk, buf = recv_until(s, PROMPT, buf)

        # Extract exact blockdata (what the server passed to validate_block)
        batch_idx = chunk.index(BATCH_MARKER) + len(BATCH_MARKER)
        end_idx   = chunk.index(END_MARKER)
        blockdata = chunk[batch_idx : end_idx + 1]  # include trailing \n

        prefix_bytes = long_to_bytes(prev_hash) + blockdata
        prefix_int   = bytes_to_long(prefix_bytes)

        C_base    = (a * prefix_int * pow2_256_modn + b_val) % n
        nonce_int = (-a_inv * C_base) % n
        nonce_bytes = nonce_int.to_bytes(32, 'big')

        # Sanity check
        x = bytes_to_long(prefix_bytes + nonce_bytes)
        assert (a * x + b_val) % n == 0

        s.sendall((nonce_bytes.hex() + '\n').encode())
        prev_hash = 0

        response, buf = recv_until(s, b'\n', buf)
        print(f"Block {block_num + 1:3d}: {response.strip().decode()}")

        if b'SUCCESS' in response:
            m2 = re.search(rb'Flag payload: ([0-9a-f]+)', response)
            if m2:
                flag_hash = int(m2.group(1), 16)
                flag_int  = (a_inv * (flag_hash - b_val)) % n
                print(f"\nFLAG: {long_to_bytes(flag_int).decode()}")
            break

        if b'REJECTED' in response or b'TIMEOUT' in response:
            print("FAILED")
            break

    s.close()


if __name__ == '__main__':
    solve()
