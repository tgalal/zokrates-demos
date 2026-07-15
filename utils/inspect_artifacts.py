#!/usr/bin/env python3
"""
Deserialize the ZoKrates 0.8.8 artifacts in this folder into human-readable JSON.

This does NOT trust any documentation about "what the files contain" -- it reads
the actual bytes and decodes them according to their on-disk formats:

  out.r1cs  : iden3/snarkjs R1CS binary format (magic b"r1cs")
  out.wtns  : iden3/snarkjs witness   binary format (magic b"wtns")
  witness   : ZoKrates-native binary witness: count + (i64 index, 32B value) pairs
  out       : ZoKrates compiled program (magic b"ZOK\\0" + version + serialized body)
  proving.key : Groth16 proving key -- opaque serialized elliptic-curve points
  *.json    : already text, echoed through with light annotation

Run:  python3 inspect_artifacts.py [DIR] [--max N]
Emits *.decoded.json next to each binary file and prints a summary.
DIR defaults to this script's own folder; the demo Makefiles pass their own.

Everything is always parsed in full; --max only caps how much is written out,
which keeps the JSON readable for the sha256 circuits (tens of thousands of
constraints). Truncation is always recorded in the output, never silent.
"""
import argparse, json, struct, os, sys

def parse_cli():
    ap = argparse.ArgumentParser(description="Decode ZoKrates 0.8.8 artifacts.")
    ap.add_argument("dir", nargs="?",
                    default=os.path.dirname(os.path.abspath(__file__)),
                    help="folder holding the artifacts (default: this script's folder)")
    ap.add_argument("--max", type=int, default=64, metavar="N",
                    help="cap list entries written to JSON; 0 means no cap (default: 64)")
    return ap.parse_args()

CLI = parse_cli()
HERE = os.path.abspath(CLI.dir)
MAX = CLI.max
def path(name): return os.path.join(HERE, name)

def cap(items):
    """Shorten a list for output. Returns it untouched when it fits under MAX,
    otherwise a self-describing wrapper -- so a truncated dump can never be
    mistaken for a complete one."""
    if MAX <= 0 or len(items) <= MAX:
        return items
    return {
        "_truncated": True,
        "total": len(items),
        "shown": MAX,
        "note": f"{len(items) - MAX} more not shown; re-run with --max 0 for all",
        "items": items[:MAX],
    }

# BN254 / bn128 scalar field modulus (the field ZoKrates + Groth16 work over)
BN254_R = 21888242871839275222246405745257275088548364400416034343698204186575808495617

def to_signed(v, p=BN254_R):
    """Show a field element as a small signed integer when it is close to p."""
    return v - p if v > p // 2 else v

def rd_u32(b, o): return struct.unpack_from("<I", b, o)[0], o + 4
def rd_u64(b, o): return struct.unpack_from("<Q", b, o)[0], o + 8
def rd_i64(b, o): return struct.unpack_from("<q", b, o)[0], o + 8
def rd_field(b, o, n8):
    v = int.from_bytes(b[o:o + n8], "little")
    return v, o + n8

# ---------------------------------------------------------------- out.r1cs ----
def parse_r1cs(fn):
    b = open(fn, "rb").read()
    assert b[:4] == b"r1cs", f"bad magic: {b[:4]!r}"
    o = 4
    version, o = rd_u32(b, o)
    n_sections, o = rd_u32(b, o)

    header, constraints, wire2label = None, None, None
    for _ in range(n_sections):
        stype, o = rd_u32(b, o)
        ssize, o = rd_u64(b, o)
        body = b[o:o + ssize]
        end = o + ssize
        if stype == 1:      # header
            header = parse_r1cs_header(body)
        elif stype == 2:    # constraints (parsed after we know n8)
            constraints_raw = body
        elif stype == 3:    # wire id -> label id map
            wire2label = list(struct.unpack_from("<%dQ" % (ssize // 8), body, 0))
        o = end

    n8 = header["field_size_bytes"]
    constraints = parse_r1cs_constraints(constraints_raw, n8, header["n_constraints"])
    return {
        "magic": "r1cs", "version": version, "n_sections": n_sections,
        "header": header, "wire_to_label_id": cap(wire2label),
        "constraints": cap(constraints),
    }

def parse_r1cs_header(b):
    o = 0
    n8, o = rd_u32(b, o)
    prime, o = rd_field(b, o, n8)
    n_wires, o = rd_u32(b, o)
    n_pub_out, o = rd_u32(b, o)
    n_pub_in, o = rd_u32(b, o)
    n_prv_in, o = rd_u32(b, o)
    n_labels, o = rd_u64(b, o)
    n_constraints, o = rd_u32(b, o)
    return {
        "field_size_bytes": n8,
        "prime": hex(prime),
        "prime_is_bn254_scalar_field": prime == BN254_R,
        "n_wires": n_wires, "n_pub_out": n_pub_out, "n_pub_in": n_pub_in,
        "n_prv_in": n_prv_in, "n_labels": n_labels, "n_constraints": n_constraints,
    }

def parse_r1cs_constraints(b, n8, n_constraints):
    o = 0
    out = []
    def read_lc():
        nonlocal o
        n_terms, oo = rd_u32(b, o); o = oo
        terms = []
        for _ in range(n_terms):
            wire, oo = rd_u32(b, o); o = oo
            coeff, oo = rd_field(b, o, n8); o = oo
            terms.append({"wire": wire, "coeff": to_signed(coeff)})
        return cap(terms)
    for _ in range(n_constraints):
        A, B, C = read_lc(), read_lc(), read_lc()
        out.append({"A": A, "B": B, "C": C})
    return out

# ---------------------------------------------------------------- out.wtns ----
def parse_wtns(fn):
    b = open(fn, "rb").read()
    assert b[:4] == b"wtns", f"bad magic: {b[:4]!r}"
    o = 4
    version, o = rd_u32(b, o)
    n_sections, o = rd_u32(b, o)
    n8, prime, n_witness = None, None, None
    values = []
    for _ in range(n_sections):
        stype, o = rd_u32(b, o)
        ssize, o = rd_u64(b, o)
        end = o + ssize
        if stype == 1:      # header
            n8, o = rd_u32(b, o)
            prime, o = rd_field(b, o, n8)
            n_witness, o = rd_u32(b, o)
        elif stype == 2:    # witness values, one field element per wire
            oo = o
            while oo < end:
                v, oo = rd_field(b, oo, n8)
                values.append(v)
        o = end
    return {
        "magic": "wtns", "version": version, "n_sections": n_sections,
        "field_size_bytes": n8, "prime": hex(prime),
        "n_witness": n_witness,
        "witness_vector": cap([{"wire": i, "value": to_signed(v)}
                               for i, v in enumerate(values)]),
    }

# ---------------------------------------------------------------- witness -----
def parse_zokrates_witness(fn):
    b = open(fn, "rb").read()
    o = 0
    count, o = rd_u64(b, o)
    entries = []
    for _ in range(count):
        idx, o = rd_i64(b, o)
        val, o = rd_field(b, o, 32)
        entries.append({"variable_index": idx, "value": to_signed(val)})
    return {
        "note": "ZoKrates-native witness: u64 count, then (i64 variable index, 32B LE value) pairs",
        "count": count, "trailing_bytes": len(b) - o, "entries": cap(entries),
    }

# ---------------------------------------------------------------- out ---------
def parse_out(fn):
    b = open(fn, "rb").read()
    assert b[:4] == b"ZOK\x00", f"bad magic: {b[:4]!r}"
    version, _ = rd_u32(b, 4)
    # Body is ZoKrates' own serialization (section table + CBOR-encoded constraints
    # and solver directives). We surface magic/version/size and the readable ASCII
    # tokens so the structure is visible without a full ZoKrates decoder.
    tokens, cur = [], bytearray()
    for ch in b[8:]:
        if 0x20 <= ch < 0x7f:
            cur.append(ch)
        else:
            if len(cur) >= 3:
                tokens.append(cur.decode())
            cur = bytearray()
    return {
        "magic": "ZOK\\0", "version": version, "total_bytes": len(b),
        "note": "Compiled program: serialized constraint system + solver directives "
                "(ZoKrates-internal CBOR framing).",
        "readable_tokens": cap(tokens),
    }

# ---------------------------------------------------------------- proving.key -
def parse_proving_key(fn):
    b = open(fn, "rb").read()
    # Groth16 proving key: a fixed set of G1/G2 points (alpha, beta, delta ...) plus
    # the query vectors. It is a raw ark-serialize/bellman dump of curve points with
    # no self-describing header, so we report size + structure rather than fake fields.
    return {
        "note": "Groth16 proving key -- opaque serialized elliptic-curve points "
                "(no magic/header). Not JSON by design; only the prover consumes it.",
        "total_bytes": len(b),
        "first_32_bytes_hex": b[:32].hex(),
        "last_32_bytes_hex": b[-32:].hex(),
    }

# ---------------------------------------------------------------- driver ------
def main():
    jobs = [
        ("out.r1cs", parse_r1cs, "out.r1cs.decoded.json"),
        ("out.wtns", parse_wtns, "out.wtns.decoded.json"),
        ("witness", parse_zokrates_witness, "witness.decoded.json"),
        ("out", parse_out, "out.decoded.json"),
        ("proving.key", parse_proving_key, "proving.key.decoded.json"),
    ]
    for src, fn, dst in jobs:
        p = path(src)
        if not os.path.exists(p):
            print(f"skip {src} (missing)"); continue
        data = fn(p)
        with open(path(dst), "w") as f:
            json.dump(data, f, indent=2)
        print(f"{src:14s} -> {dst}")
    print("\nverification.key / proof.json / abi.json are already JSON (read directly).")

if __name__ == "__main__":
    main()
