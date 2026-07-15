import struct
from hashlib import sha256

def serialize_header(version: str, prevblock_hash: str, merkle_root: str, time: int, bits: int, nonce: int):
    return bytes.fromhex(version)[::-1] + \
        bytes.fromhex(prevblock_hash)[::-1] + \
        bytes.fromhex(merkle_root)[::-1] + \
        time.to_bytes(4, byteorder='little') + \
        bits.to_bytes(4, byteorder='little') + \
        nonce.to_bytes(4, byteorder='little')

# values (from https://www.blockchain.com/explorer/blocks/btc/505400)
serialized_block_header = serialize_header(
    version='20000000',
    prevblock_hash='00000000000000000022a664b3ff1e4f85140eddeebd0efcbe6a543d45c4135f',
    merkle_root='a3defcaa713d267eacab786c4cc9c0df895d8ac02066df6c84c7aec437ae17ae',
    time=1516561306,
    bits=394155916,
    nonce=2816816696
)

# double hashing
hash1 = sha256(serialized_block_header).digest()
hash2 = sha256(hash1).digest()

# encode block_data as 80 unsigned byte values
input_encoded = struct.unpack('80B', serialized_block_header)

# encode block_hash as 8 32bit integers
output_encoded = struct.unpack('>8I', hash2)

# format input and output as ZoKrates arguments
args = " ".join(map(str, input_encoded + output_encoded))

print(args)
