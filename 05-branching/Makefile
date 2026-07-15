# The running example: prove you know x with x**3 + x + 5 == 35.
#
# x = 3 is the satisfying assignment. main asserts rather than returns, so it has
# no public output at all: the proof carries an empty "inputs" list, and a wrong
# X fails at `compute-witness` -- you cannot even build a proof of a false claim.
X ?= 0

include ../common.mk

inputs.txt:
	echo '$(X)' > inputs.txt
