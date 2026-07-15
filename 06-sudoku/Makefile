# Prove knowledge of a sudoku solution without revealing it. The puzzle is the
# public input (81 cells, 0 = blank): it shows up as the "inputs" list in
# proof.json, so the verifier knows *which* puzzle was solved. The solution is
# private: it exists only inside compute-witness and never reaches the proof.
# The circuit is small (3,321 constraints on ZoKrates 0.8.8), so the whole
# pipeline runs in seconds.
#
# TAMPER hands the circuit a broken solution. Each mode violates exactly one
# of main.zok's three constraint families, and compute-witness names the
# failing assertion -- you cannot even produce a proof, let alone verify one:
#
#   TAMPER=duplicate   a repeated digit in a row        (distinctness)
#   TAMPER=clue        a valid grid for another puzzle  (clue match)
#   TAMPER=range       a 0 in a blank cell              (1..9 range)
#
# As in the other demos, inputs.txt is only rebuilt when helper.py changes, so
# run `make clean` when switching TAMPER.
TAMPER ?= none

include ../common.mk

inputs.txt: helper.py
	$(PYTHON) helper.py $(TAMPER) > inputs.txt
