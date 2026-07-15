Prove you know the solution to a public sudoku puzzle without revealing it:

```
make
```

Then hand the circuit a wrong solution and watch `compute-witness` refuse:

```
make clean; TAMPER=duplicate make
make clean; TAMPER=clue make
make clean; TAMPER=range make
```
