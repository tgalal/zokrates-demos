import sys

# The classic example grids from Wikipedia's "Sudoku" article. 0 is a blank.
PUZZLE = [
    [5, 3, 0, 0, 7, 0, 0, 0, 0],
    [6, 0, 0, 1, 9, 5, 0, 0, 0],
    [0, 9, 8, 0, 0, 0, 0, 6, 0],
    [8, 0, 0, 0, 6, 0, 0, 0, 3],
    [4, 0, 0, 8, 0, 3, 0, 0, 1],
    [7, 0, 0, 0, 2, 0, 0, 0, 6],
    [0, 6, 0, 0, 0, 0, 2, 8, 0],
    [0, 0, 0, 4, 1, 9, 0, 0, 5],
    [0, 0, 0, 0, 8, 0, 0, 7, 9],
]
SOLUTION = [
    [5, 3, 4, 6, 7, 8, 9, 1, 2],
    [6, 7, 2, 1, 9, 5, 3, 4, 8],
    [1, 9, 8, 3, 4, 2, 5, 6, 7],
    [8, 5, 9, 7, 6, 1, 4, 2, 3],
    [4, 2, 6, 8, 5, 3, 7, 9, 1],
    [7, 1, 3, 9, 2, 4, 8, 5, 6],
    [9, 6, 1, 5, 3, 7, 2, 8, 4],
    [2, 8, 7, 4, 1, 9, 6, 3, 5],
    [3, 4, 5, 2, 8, 6, 1, 7, 9],
]


# The same checks main.zok makes, as a guard against typos in the grids above:
# helper.py must never hand the circuit a bad *honest* input.
def check(puzzle, solution):
    digits = set(range(1, 10))
    for i in range(9):
        row = solution[i]
        col = [solution[j][i] for j in range(9)]
        box = [solution[i // 3 * 3 + j // 3][i % 3 * 3 + j % 3] for j in range(9)]
        assert set(row) == set(col) == set(box) == digits
    for r in range(9):
        for c in range(9):
            assert puzzle[r][c] in (0, solution[r][c])


check(PUZZLE, SOLUTION)

# Each tamper mode violates exactly one of the circuit's three constraint
# families while leaving the other two satisfied.
tamper = sys.argv[1] if len(sys.argv) > 1 else "none"
solution = [row[:] for row in SOLUTION]
if tamper == "duplicate":
    # (0,2) is blank in the puzzle and 2 is a legal digit, but row 0 already
    # has a 2 at (0,8) -- only distinctness can reject this
    solution[0][2] = 2
elif tamper == "clue":
    # swap 1 and 2 everywhere: still a perfectly valid sudoku grid, just not
    # the one this puzzle pins down -- only the clue cells notice
    solution = [[{1: 2, 2: 1}.get(x, x) for x in row] for row in solution]
elif tamper == "range":
    # 0 duplicates nothing and (0,2) is blank, so only the 1..9 range check
    # can reject it
    solution[0][2] = 0
elif tamper != "none":
    sys.exit(f"unknown TAMPER mode {tamper!r}")

# 162 arguments: the 81 public puzzle cells, then the 81 private solution
# cells, row-major
flat = [x for row in PUZZLE for x in row] + [x for row in solution for x in row]
print(" ".join(map(str, flat)))


def show(grid):
    return "\n".join(" ".join(str(x) if x else "." for x in row) for row in grid)


print(f"puzzle (public):\n{show(PUZZLE)}", file=sys.stderr)
print(f"solution (private, TAMPER={tamper}):\n{show(solution)}", file=sys.stderr)
