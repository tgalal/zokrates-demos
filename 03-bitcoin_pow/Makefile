# Prove that a Bitcoin block header double-hashes to a given block hash, without
# revealing the header. Values are block 505400; helper.py serializes them and
# prints all 88 arguments (80 header bytes, then the 8 u32s of the hash).

include ../common.mk

inputs.txt: helper.py
	$(PYTHON) helper.py > inputs.txt
