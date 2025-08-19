from __future__ import annotations

import argparse
import enum
import random
from dataclasses import dataclass
from typing import List, Tuple, Optional

FILES = "abcdefgh"
RANKS = "12345678"
BOARD_SIZE = 8

# ------------------------------ Configuration -------------------------------
DEFAULT_ROUNDS = 15
ROOK_START_POS = "h1"
BISHOP_START_POS = "c3"


# ------------------------------- Core types ---------------------------------
@dataclass(frozen=True)
class Pos:
    f: int  # 0..7 for a..h
    r: int  # 0..7 for 1..8

    def __post_init__(self) -> None:
        if not (0 <= self.f < BOARD_SIZE and 0 <= self.r < BOARD_SIZE):
            raise ValueError(f"Invalid board coordinates: ({self.f}, {self.r})")

    @staticmethod
    def from_algebraic(square: str) -> "Pos":
        if len(square) != 2 or square[0] not in FILES or square[1] not in RANKS:
            raise ValueError(f"Invalid square: {square}")
        f = FILES.index(square[0])
        r = RANKS.index(square[1])
        return Pos(f, r)

    def to_algebraic(self) -> str:
        return f"{FILES[self.f]}{RANKS[self.r]}"

    def step_wrap(self, df: int, dr: int, steps: int) -> "Pos":
        """Move `steps` times by (df, dr) with toroidal wrap-around."""
        nf = (self.f + df * steps) % BOARD_SIZE
        nr = (self.r + dr * steps) % BOARD_SIZE
        return Pos(nf, nr)


class Direction(enum.Enum):
    UP = (0, 1)
    RIGHT = (1, 0)

    @property
    def delta(self) -> Tuple[int, int]:
        return self.value


class CoinFace(str, enum.Enum):
    HEADS = "H"
    TAILS = "T"


# ----------------------------- Pieces & Board -------------------------------
@dataclass
class Piece:
    pos: Pos


@dataclass
class Bishop(Piece):
    def attacks(self, target: Pos) -> bool:
        # On a clear board, bishop attacks any square on the same diagonal
        df = abs(self.pos.f - target.f)
        dr = abs(self.pos.r - target.r)
        return df == dr and df != 0


@dataclass
class Rook(Piece):
    def attacks(self, target: Pos) -> bool:
        return (self.pos.f == target.f) ^ (self.pos.r == target.r)  # same file or rank, not both

    def move(self, direction: Direction, steps: int) -> "Rook":
        df, dr = direction.delta
        new_pos = self.pos.step_wrap(df, dr, steps)
        return Rook(new_pos)


@dataclass
class Board:
    bishop: Bishop
    rook: Rook

    def bishop_can_capture_rook(self) -> bool:
        return self.bishop.attacks(self.rook.pos)

    def rook_can_capture_bishop(self) -> bool:
        return self.rook.attacks(self.bishop.pos)


# ------------------------------- Simulation ---------------------------------
@dataclass(frozen=True)
class MoveRecord:
    round_no: int
    coin: CoinFace  # H for heads (UP), T for tails (RIGHT)
    dice: Tuple[int, int]
    steps: int
    direction: Direction
    from_sq: str
    to_sq: str
    bishop_can_capture: bool


class Winner(str, enum.Enum):
    BISHOP = "BISHOP"
    ROOK = "ROOK"


@dataclass(frozen=True)
class GameResult:
    winner: Winner
    moves: List[MoveRecord]


class RookSurvivalGame:
    """
    Simulates the 'Rook vs Bishop' survival game on a toroidal 8x8 board.

    Rules encoded from the prompt:
      - Rook starts at h1 and moves for 15 rounds.
      - Each round: coin toss -> H: move UP, T: move RIGHT.
      - Roll two 6-sided dice; their sum is the number of squares to move.
      - Board wraps around on top and right edges (toroidal in both axes).
      - Bishop is stationary at c3.
      - If *after* any rook move the bishop can capture the rook (i.e., same diagonal),
        the bishop wins immediately. Otherwise, if the rook survives all 15 rounds,
        the rook wins.
    """

    def __init__(self, seed: Optional[int] = None, rounds: int = DEFAULT_ROUNDS, *, rook_start: str = ROOK_START_POS, bishop_start: str = BISHOP_START_POS) -> None:
        self.rng = random.Random(seed)
        self.rounds = rounds
        self.board = Board(
            bishop=Bishop(Pos.from_algebraic(bishop_start)),
            rook=Rook(Pos.from_algebraic(rook_start)),
        )

    def toss_coin(self) -> CoinFace:
        return CoinFace.HEADS if self.rng.random() < 0.5 else CoinFace.TAILS

    def roll_dice(self) -> Tuple[int, int]:
        return self.rng.randint(1, 6), self.rng.randint(1, 6)

    def simulate(self, rounds: Optional[int] = None) -> GameResult:
        records: List[MoveRecord] = []
        rounds_to_play = self.rounds if rounds is None else rounds

        for i in range(1, rounds_to_play + 1):
            coin = self.toss_coin()
            d1, d2 = self.roll_dice()
            steps = d1 + d2
            direction = Direction.UP if coin is CoinFace.HEADS else Direction.RIGHT

            start = self.board.rook.pos
            self.board.rook = self.board.rook.move(direction, steps)
            end = self.board.rook.pos

            # Immediate same-square capture: bishop and rook on the same square
            if self.board.rook.pos == self.board.bishop.pos:
                records.append(
                    MoveRecord(
                        round_no=i,
                        coin=coin,
                        dice=(d1, d2),
                        steps=steps,
                        direction=direction,
                        from_sq=start.to_algebraic(),
                        to_sq=end.to_algebraic(),
                        bishop_can_capture=True,
                    )
                )
                return GameResult(Winner.BISHOP, records)

            bishop_can_capture = self.board.bishop_can_capture_rook()

            records.append(
                MoveRecord(
                    round_no=i,
                    coin=coin,
                    dice=(d1, d2),
                    steps=steps,
                    direction=direction,
                    from_sq=start.to_algebraic(),
                    to_sq=end.to_algebraic(),
                    bishop_can_capture=bishop_can_capture,
                )
            )

            if bishop_can_capture:
                return GameResult(Winner.BISHOP, records)

        return GameResult(Winner.ROOK, records)


# --------------------------------- CLI --------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Rook vs Bishop survival simulation")
    parser.add_argument("--seed", type=int, default=None, help="Optional RNG seed for reproducibility")
    parser.add_argument("--rounds", type=int, default=DEFAULT_ROUNDS, help=f"Number of rounds to simulate (default {DEFAULT_ROUNDS})")
    parser.add_argument("--rook-start", type=str, default=ROOK_START_POS, help=f"Rook starting square (default {ROOK_START_POS})")
    parser.add_argument("--bishop-start", type=str, default=BISHOP_START_POS, help=f"Bishop starting square (default {BISHOP_START_POS})")
    args = parser.parse_args()

    game = RookSurvivalGame(seed=args.seed, rounds=args.rounds, rook_start=args.rook_start, bishop_start=args.bishop_start)
    result = game.simulate()

    for rec in result.moves:
        dir_str = "UP" if rec.direction is Direction.UP else "RIGHT"
        print(
            f"Round {rec.round_no:2d}: coin={rec.coin.value} ({dir_str}), "
            f"dice={rec.dice} -> steps={rec.steps:2d}, "
            f"rook: {rec.from_sq} -> {rec.to_sq}, "
            f"bishop_can_capture={rec.bishop_can_capture}"
        )

    print(f"\nWinner: {result.winner.value}")


if __name__ == "__main__":
    main()
