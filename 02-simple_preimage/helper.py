import struct
import sys
from hashlib import sha256

# The preimage slot in main.zok is a fixed 32 bytes, so a shorter message is
# zero-padded to fill it. The hash is over the padded 32 bytes -- which is
# exactly what the circuit recomputes.
#
# This padding is a demo shortcut, not a practice to copy: it is not injective,
# so "ab" and "ab\0" collide into the same preimage. Real code commits to the
# length, or hashes a variable-size encoding.
N = 32

message = (sys.argv[1] if len(sys.argv) > 1 else "zero-knowledge").encode()
assert len(message) <= N, f"message is {len(message)} bytes, max is {N}"
preimage = message.ljust(N, b"\x00")

digest = sha256(preimage).digest()

# encode preimage as 32 unsigned byte values: the private input, and the only
# argument main takes
input_encoded = struct.unpack(f"{N}B", preimage)

# the hash is main's public *output*, not an argument -- shown here only so you
# can match it against the "inputs" field of proof.json
output_encoded = struct.unpack(">8I", digest)

print(" ".join(map(str, input_encoded)))

print(f"message  : {message.decode()!r} ({len(message)} bytes, padded to {N})", file=sys.stderr)
print(f"sha256   : {digest.hex()}", file=sys.stderr)
print(f"as u32[8]: {' '.join(map(str, output_encoded))}", file=sys.stderr)
