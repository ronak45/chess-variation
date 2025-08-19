## Rook vs Bishop — Chess Variation

A tiny simulation of a rook trying to survive against a stationary bishop on an 8×8 toroidal board. Each round the rook moves either UP or RIGHT by the sum of two dice, and the board wraps around. If after any move the bishop can capture (same diagonal), the bishop wins; otherwise the rook survives after the configured number of rounds.

### Setup t works
- **Board**: 8×8 with wrap-around in both directions.
- **Rook move**: Each round, a fair coin decides direction (UP or RIGHT), and two dice determine steps; wrap-around is applied. Output is printed.
- **Capture**: Bishop captures if the rook ends on a square the bishop attacks. Same-square landings result in an immediate capture handled by the game loop.

## Project layout
- `main.py`: Core implementation and a simple CLI.
- `tests.py`: Pytest-based unit tests and examples.

## Key design decisions and trade-offs
- **Immutability by default**
  - `Pos` and `MoveRecord` are frozen dataclasses for safety and clarity.
  ---- Once created, values cannot change, eliminating accidental in-place mutations and aliasing bugs + trustworthy history
  - `Rook.move` returns a new `Rook` instance (no in-place mutation), making state transitions explicit and easier to reason about.

- **Same-square capture rule**
  - Assumption: `Bishop.attacks(target)` game logic treats a post-move same-square as an immediate capture. 

- **Enums for clarity and determinism**
  - `Winner` and `CoinFace` are `Enum`s (subclassing `str`) for strong typing and easy comparison/printing.
  - Tests that compare to string literals (e.g., "BISHOP") continue to work because enums are string-like.

- **Configuration vs. logic**
  - Magic values are extracted into constants and parameters: `DEFAULT_ROUNDS`, `ROOK_START_POS`, `BISHOP_START_POS`.
  - `RookSurvivalGame` accepts `rounds`, `rook_start`, and `bishop_start`, decoupling configuration from the core logic.
  - This makes future changes to these parameters clean and consistent. 

- **Performance**
  - The board is small; per-move checks are O(1) and fast. If needed, you can precompute the bishop’s attacked squares
    once and use set membership. Given 64 squares total, this is a micro-optimization and left as a future option.

## Configuration and CLI
The CLI exposes the key configuration points so you can explore different scenarios.

```bash
python3 main.py --help
```

Flags:
- `--seed`: RNG seed for reproducible runs (default: None)
- `--rounds`: number of rounds to simulate (default: `DEFAULT_ROUNDS`)
- `--rook-start`: rook starting square in algebraic notation (default: `ROOK_START_POS`)
- `--bishop-start`: bishop starting square in algebraic notation (default: `BISHOP_START_POS`)

Example:
```bash
python3 main.py --seed 42 --rounds 5 --rook-start h1 --bishop-start c3
```

## Determinism and testing
- Deterministic runs: set `--seed` or pass `seed=` to `RookSurvivalGame`.
- Unit tests: run with pytest.

```bash
pip install pytest
pytest -q tests.py
```
## Debugging:
Create a python vm if you run into issues.


The tests include (I used AI to create these):
- Algebraic coordinate round-trip and wrap-around checks.
- Bishop/rook attack semantics.
- Reproducibility with a fixed seed.
- Monkeypatched scenarios to force specific outcomes.

## Coding conventions
- **Types first**: Public APIs and key functions are type-annotated.
- **Dataclasses and enums**: Prefer small immutable value types (`frozen=True`) for clarity and predictability.
- **Naming**: Descriptive, full-word names for readability.
- **Control flow**: Guard clauses and early returns; shallow nesting.
- **Error handling**: Validate inputs (e.g., `Pos.from_algebraic`) and fail fast.
- **Formatting**: Keep lines readable and avoid unrelated refactors in edits.

## Quick API tour
- `Pos.from_algebraic("c3")` / `Pos.to_algebraic()`
- `Direction.UP/RIGHT` with `.delta` for movement vectors
- `Bishop.attacks(target: Pos) -> bool`
- `Rook.move(direction, steps) -> Rook` (returns a new rook)
- `Board.bishop_can_capture_rook() -> bool`
- `RookSurvivalGame(seed=None, rounds=DEFAULT_ROUNDS, rook_start=ROOK_START_POS, bishop_start=BISHOP_START_POS)`
- `RookSurvivalGame.simulate(rounds: Optional[int] = None) -> GameResult`

## Future ideas
- Precompute bishop attack set for marginal speedups and simpler capture checks.
- Record simulations of gameplay and look at probability of winning for each, etc. 
