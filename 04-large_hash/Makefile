# The same preimage proof as simple_preimage, but over a 320-byte file: ten
# times the data, to show what hashing bulk input costs inside a circuit.
#
# Measured on this machine (ZoKrates 0.8.8, bn128), compile only:
#
#     input    constraints   compile   peak RSS
#      32 B         26,635      ~1s            <- simple_preimage
#     128 B         79,718      ~4s
#     320 B        180,680    ~14s     3.3 GB  <- here
#     512 B        294,841     ~40s
#       1 KB            --    >2min, gave up
#
# Constraints roughly track the data, but time and memory grow much faster. This
# is the whole point of the demo: "large" for a SNARK means kilobytes, not
# megabytes. A megabyte-scale file is simply not provable this way.
#
# Mind the 3.3 GB: 320 bytes of data needs gigabytes to compile, and `setup` on
# 180k constraints costs more again. On a small laptop, demo this one from
# pre-built artifacts rather than live.
#
# The size lives in main.zok (const u32 N), and sample.txt is checked in at that
# size. helper.py reads N back and refuses to run if the two disagree.

include ../common.mk

inputs.txt: helper.py main.zok sample.txt
	$(PYTHON) helper.py > inputs.txt

# sample.txt is checked in, so this only fires when the file is missing -- it
# deliberately has no prerequisites, so editing main.zok can never silently
# overwrite an input you are holding. Change N and helper.py stops with a size
# mismatch; `rm sample.txt && make inputs.txt` refills it. `clean` leaves it
# alone: it is an input, not a build artifact.
sample.txt:
	$(PYTHON) -c "import re, sys; n = int(re.search(r'const u32 N = (\d+)', open('main.zok').read()).group(1)); sys.stdout.write(('cedarcrypt' * (n // 10 + 1))[:n])" > $@
