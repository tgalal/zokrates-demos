# ZoKrates Cheatcheat

Getting Started: [https://zokrates.github.io/gettingstarted.html](https://zokrates.github.io/gettingstarted.html)


## Install

```bash
curl -LSfs get.zokrat.es | sh
```

Update path as instructed.

## Usage

```bash
# compile
zokrates compile -i root.zok
# perform the setup phase
zokrates setup
# execute the program
zokrates compute-witness -a 337 113569
# generate a proof of computation
zokrates generate-proof
# export a solidity verifier
zokrates export-verifier
# or verify natively
zokrates verify
```

Or use the Makefile in each demo:

```bash
cd 01-workshop_example

# everything (compile, setup, compute-witness, generate-proof..etc)
make
make compile
make setup
make prove
make witness
make verify

# Special one, decodes binaries to json
make decode

# cleanup
make clean
```
