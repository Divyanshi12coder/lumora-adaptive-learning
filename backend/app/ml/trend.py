"""Performance trend analysis: least-squares slope over a rolling accuracy curve."""

from dataclasses import dataclass

import numpy as np


@dataclass
class TrendResult:
    slope: float  # change in rolling accuracy per answer
    r_squared: float
    direction: str  # improving | steady | dipping | not_enough_data
    rolling: list[float]


def accuracy_trend(outcomes: list[bool], window: int = 5) -> TrendResult:
    if len(outcomes) < 4:
        return TrendResult(0.0, 0.0, "not_enough_data", [float(x) for x in outcomes])
    arr = np.asarray(outcomes, dtype=float)
    w = min(window, len(arr))
    kernel = np.ones(w) / w
    rolling = np.convolve(arr, kernel, mode="valid")
    if len(rolling) < 2:
        return TrendResult(0.0, 0.0, "not_enough_data", rolling.tolist())
    x = np.arange(len(rolling), dtype=float)
    slope, intercept = np.polyfit(x, rolling, 1)
    pred = slope * x + intercept
    ss_res = float(np.sum((rolling - pred) ** 2))
    ss_tot = float(np.sum((rolling - rolling.mean()) ** 2))
    r2 = 1 - ss_res / ss_tot if ss_tot > 1e-12 else 0.0
    if slope > 0.015:
        direction = "improving"
    elif slope < -0.015:
        direction = "dipping"
    else:
        direction = "steady"
    return TrendResult(float(slope), float(r2), direction, [round(float(v), 3) for v in rolling])
