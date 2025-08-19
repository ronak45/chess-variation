# ========================= tests/test_rook_vs_bishop.py =========================
# Run with:  pytest -q

import pytest

# Import the module under test. Save the main code as `rook_vs_bishop.py` to use this import.
import main as rvb


def test_pos_algebraic_roundtrip():
    p = rvb.Pos.from_algebraic("c3")
    assert p.to_algebraic() == "c3"


def test_pos_step_wrap_right_and_up():
    start = rvb.Pos.from_algebraic("h1")
    # RIGHT by 9 -> wraps to a1 (since (7 + 9) % 8 == 0)
    assert start.step_wrap(*rvb.Direction.RIGHT.delta, 9).to_algebraic() == "a1"
    # UP by 9 -> wraps to h2 (since (0 + 9) % 8 == 1)
    assert start.step_wrap(*rvb.Direction.UP.delta, 9).to_algebraic() == "h2"
    # UP by 8 -> back to h1
    assert start.step_wrap(*rvb.Direction.UP.delta, 8).to_algebraic() == "h1"


def test_bishop_attacks_diagonal_true_false():
    b = rvb.Bishop(rvb.Pos.from_algebraic("c3"))
    assert b.attacks(rvb.Pos.from_algebraic("b2"))
    assert b.attacks(rvb.Pos.from_algebraic("d4"))
    assert b.attacks(rvb.Pos.from_algebraic("e1"))
    # Same-square is not considered an attack in current implementation
    assert not b.attacks(rvb.Pos.from_algebraic("c3"))


def test_rook_attacks_same_file_or_rank():
    r = rvb.Rook(rvb.Pos.from_algebraic("h1"))
    assert r.attacks(rvb.Pos.from_algebraic("h5"))  # same file
    assert r.attacks(rvb.Pos.from_algebraic("d1"))  # same rank
    assert not r.attacks(rvb.Pos.from_algebraic("h1"))  # XOR prevents same-square being counted


@pytest.mark.xfail(reason="Current design treats same-square as non-capture; enable if rule changes.")
def test_same_square_capture_optional():
    board = rvb.Board(
        bishop=rvb.Bishop(rvb.Pos.from_algebraic("c3")),
        rook=rvb.Rook(rvb.Pos.from_algebraic("c3")),
    )
    assert board.bishop_can_capture_rook() is True


def test_simulation_reproducible_with_seed():
    g1 = rvb.RookSurvivalGame(seed=42)
    g2 = rvb.RookSurvivalGame(seed=42)
    res1 = g1.simulate(rounds=15)
    res2 = g2.simulate(rounds=15)
    # Winners and move traces should match exactly with the same seed
    assert res1.winner == res2.winner
    assert [m.to_sq for m in res1.moves] == [m.to_sq for m in res2.moves]


def test_simulation_bishop_can_win_via_a1(monkeypatch):
    """Force Tails and sum=9 so rook moves h1->a1, which is on c3's diagonal (a1..c3..h8)."""
    game = rvb.RookSurvivalGame(seed=0)
    monkeypatch.setattr(game, "toss_coin", lambda: "T")
    monkeypatch.setattr(game, "roll_dice", lambda: (3, 6))  # sum = 9
    result = game.simulate(rounds=1)
    assert result.winner == "BISHOP"
    assert result.moves[-1].to_sq == "a1"
    assert result.moves[-1].bishop_can_capture is True


def test_simulation_rook_survives_simple_pattern(monkeypatch):
    """Always Heads and sum=2 -> rook climbs the h-file; never hits h8 within 15 rounds."""
    game = rvb.RookSurvivalGame(seed=0)
    monkeypatch.setattr(game, "toss_coin", lambda: "H")
    monkeypatch.setattr(game, "roll_dice", lambda: (1, 1))  # sum = 2
    result = game.simulate(rounds=15)
    assert result.winner == "ROOK"
    # Ensure none of the recorded moves were capturable by the bishop
    assert all(not m.bishop_can_capture for m in result.moves)


def test_invalid_square_raises():
    with pytest.raises(ValueError):
        rvb.Pos.from_algebraic("z9")
