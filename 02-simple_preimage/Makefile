# Prove knowledge of a sha256 preimage: private preimage in, public hash out.
#
# The message to prove knowledge of. It is zero-padded to the 32 bytes main.zok
# expects. After changing it, run `make clean verify` -- inputs.txt is only
# rebuilt when helper.py changes, not when MESSAGE does.
MESSAGE ?= zero-knowledge

include ../common.mk

inputs.txt: helper.py
	$(PYTHON) helper.py '$(MESSAGE)' > inputs.txt
