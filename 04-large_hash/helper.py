import os
import re
import struct
import sys
from hashlib import sha256

# Same proof as simple_preimage, but over a file.
#
# N is read back out of main.zok rather than repeated here: the circuit fixes
# the length at compile time, so it is the one place the size is decided. The
# file is hashed exactly as it is on disk -- no padding involved.

HERE = os.path.dirname(os.path.abspath(__file__))
def here(name): return os.path.join(HERE, name)

N = int(re.search(r"const u32 N = (\d+)", open(here("main.zok")).read()).group(1))

path = here(sys.argv[1] if len(sys.argv) > 1 else "sample.txt")
data = open(path, "rb").read()
assert len(data) == N, (
    f"{os.path.basename(path)} is {len(data)} bytes but main.zok fixes N = {N}; "
    f"`rm {os.path.basename(path)} && make inputs.txt` rebuilds it at the right size"
)

digest = sha256(data).digest()

# encode the file as N unsigned byte values: the private input, and the only
# argument main takes (the hash is its public output)
print(" ".join(map(str, struct.unpack(f"{N}B", data))))

# sha256 consumes 512-bit blocks and the circuit unrolls one full compression
# per block -- this count is what the constraint total tracks
blocks = (N * 8 + 65) // 512 + 1
print(f"file   : {os.path.basename(path)} ({N} bytes)", file=sys.stderr)
print(f"sha256 : {digest.hex()}", file=sys.stderr)
print(f"blocks : {blocks} x 512-bit compression, unrolled into constraints", file=sys.stderr)
