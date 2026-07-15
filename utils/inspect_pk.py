#!/usr/bin/env python3
"""
Deserialize ZoKrates 0.8.8's Groth16 `proving.key` (ark backend, BN254).

Layout is ark-serialize UNCOMPRESSED:
  G1 = x||y, each 32B little-endian     (64B)
  G2 = x(c0||c1) || y(c0||c1)           (128B)
  Vec<T> = u64 little-endian length prefix, then elements

  ProvingKey {
    vk: VerifyingKey { alpha_g1: G1, beta_g2: G2, gamma_g2: G2, delta_g2: G2,
                       gamma_abc_g1: Vec<G1> },
    beta_g1: G1, delta_g1: G1,
    a_query: Vec<G1>, b_g1_query: Vec<G1>, b_g2_query: Vec<G2>,
    h_query: Vec<G1>, l_query: Vec<G1>,
  }

The layout is *verified*, not assumed: the vk fields parsed out of proving.key are
compared against the independently-produced verification.key JSON.

Run:  python3 inspect_pk.py [DIR] [--max N]

The key is always parsed and cross-checked in full; --max only caps how many
points get written to JSON. The sha256 circuits carry one point per wire, so an
uncapped dump runs to tens of MB.
"""
import argparse, json, struct, os, sys

def parse_cli():
    ap = argparse.ArgumentParser(description="Decode a ZoKrates 0.8.8 Groth16 proving.key.")
    ap.add_argument("dir", nargs="?",
                    default=os.path.dirname(os.path.abspath(__file__)),
                    help="folder holding proving.key + verification.key")
    ap.add_argument("--max", type=int, default=64, metavar="N",
                    help="cap points written to JSON; 0 means no cap (default: 64)")
    return ap.parse_args()

CLI = parse_cli()
HERE = os.path.abspath(CLI.dir)
MAX = CLI.max
p = lambda n: os.path.join(HERE, n)

def cap(items):
    """Shorten a vector for output only -- parsing and the vk cross-check always
    run over every element. Truncation is recorded, never silent."""
    if MAX <= 0 or len(items) <= MAX:
        return items
    return {
        "_truncated": True,
        "total": len(items),
        "shown": MAX,
        "note": f"{len(items) - MAX} more not shown; re-run with --max 0 for all",
        "items": items[:MAX],
    }

def capped(pk):
    """A copy of the parsed key with its point vectors shortened for dumping."""
    out = {k: (cap(v) if isinstance(v, list) else v) for k, v in pk.items()}
    out["vk"] = dict(pk["vk"], gamma_abc_g1=cap(pk["vk"]["gamma_abc_g1"]))
    return out

class R:
    def __init__(self, b): self.b, self.o = b, 0
    def take(self, n):
        v = self.b[self.o:self.o + n]; self.o += n
        assert len(v) == n, "truncated"
        return v
    def u64(self): return struct.unpack("<Q", self.take(8))[0]
    def fq(self): return int.from_bytes(self.take(32), "little")
    def g1(self): return {"x": hex(self.fq()), "y": hex(self.fq())}
    def g2(self):
        x0, x1 = self.fq(), self.fq()
        y0, y1 = self.fq(), self.fq()
        return {"x": [hex(x0), hex(x1)], "y": [hex(y0), hex(y1)]}
    def vec(self, f):
        n = self.u64()
        return [f() for _ in range(n)]

def parse_pk(fn):
    r = R(open(fn, "rb").read())
    pk = {}
    pk["vk"] = {
        "alpha_g1": r.g1(), "beta_g2": r.g2(), "gamma_g2": r.g2(),
        "delta_g2": r.g2(), "gamma_abc_g1": r.vec(r.g1),
    }
    pk["beta_g1"] = r.g1()
    pk["delta_g1"] = r.g1()
    pk["a_query"] = r.vec(r.g1)
    pk["b_g1_query"] = r.vec(r.g1)
    pk["b_g2_query"] = r.vec(r.g2)
    pk["h_query"] = r.vec(r.g1)
    pk["l_query"] = r.vec(r.g1)
    assert r.o == len(r.b), f"leftover bytes: {len(r.b) - r.o}"
    return pk

def norm(h):  # "0x0a.." -> canonical int-hex for comparison
    return hex(int(h, 16))

def verify_against_vk(pk):
    """Cross-check: vk fields inside proving.key must equal verification.key."""
    vk = json.load(open(p("verification.key")))
    checks = []
    a = pk["vk"]["alpha_g1"]
    checks.append(("alpha", [a["x"], a["y"]], [norm(v) for v in vk["alpha"]]))
    for name, key in (("beta", "beta_g2"), ("gamma", "gamma_g2"), ("delta", "delta_g2")):
        g = pk["vk"][key]
        # Both ark and ZoKrates' JSON store Fq2 in (c0, c1) order -- no swap.
        got = [g["x"], g["y"]]
        exp = [[norm(v) for v in vk[name][0]], [norm(v) for v in vk[name][1]]]
        checks.append((name, got, exp))
    for i, g in enumerate(pk["vk"]["gamma_abc_g1"]):
        checks.append((f"gamma_abc[{i}]", [g["x"], g["y"]],
                       [norm(v) for v in vk["gamma_abc"][i]]))
    ok = True
    for name, got, exp in checks:
        good = got == exp
        ok &= good
        print(f"  {'OK  ' if good else 'FAIL'} {name}")
        if not good:
            print(f"       got {got}\n       exp {exp}")
    return ok

if __name__ == "__main__":
    pk = parse_pk(p("proving.key"))
    print("Parsed proving.key cleanly (no leftover bytes).")
    print("element counts:",
          {k: len(v) for k, v in pk.items() if isinstance(v, list)},
          "gamma_abc_g1:", len(pk["vk"]["gamma_abc_g1"]))
    print("\nCross-checking vk section against verification.key:")
    ok = verify_against_vk(pk)
    print("\nLayout", "CONFIRMED" if ok else "NOT confirmed")
    if ok:
        with open(p("proving.key.decoded.json"), "w") as f:
            json.dump(capped(pk), f, indent=2)
        note = "" if MAX <= 0 else f" (vectors capped at {MAX}; --max 0 for all)"
        print(f"wrote proving.key.decoded.json{note}")
    sys.exit(0 if ok else 1)
