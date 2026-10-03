"""Bayesian Knowledge Tracing (Corbett & Anderson, 1994).

An interpretable, well-established model of topic mastery. P(known) is updated
after every answer using four parameters: prior, learn, slip and guess.
Guess probability is tied to the number of answer options shown, and a correct
answer given *after a hint* is treated as weaker evidence of mastery.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class BKTParams:
    p_init: float = 0.2
    p_learn: float = 0.15
    p_slip: float = 0.1
    # Guess is derived from option count when not given explicitly.
    p_guess: float | None = None


DEFAULT_PARAMS = BKTParams()


def update_mastery(
    p_known: float,
    correct: bool,
    *,
    option_count: int = 4,
    hints_used: int = 0,
    params: BKTParams = DEFAULT_PARAMS,
) -> float:
    guess = params.p_guess if params.p_guess is not None else 1.0 / max(2, option_count)
    slip = params.p_slip
    if correct and hints_used > 0:
        # A hinted success is closer to a guess: raise guess toward 0.6.
        guess = min(0.6, guess + 0.15 * hints_used)

    if correct:
        num = p_known * (1 - slip)
        den = num + (1 - p_known) * guess
    else:
        num = p_known * slip
        den = num + (1 - p_known) * (1 - guess)
    posterior = num / den if den > 0 else p_known
    learned = posterior + (1 - posterior) * params.p_learn
    return float(min(0.995, max(0.005, learned)))


def mastery_from_sequence(outcomes: list[tuple[bool, int, int]], params: BKTParams = DEFAULT_PARAMS) -> float:
    """outcomes: (correct, option_count, hints_used) in chronological order."""
    p = params.p_init
    for correct, options, hints in outcomes:
        p = update_mastery(p, correct, option_count=options, hints_used=hints, params=params)
    return p
