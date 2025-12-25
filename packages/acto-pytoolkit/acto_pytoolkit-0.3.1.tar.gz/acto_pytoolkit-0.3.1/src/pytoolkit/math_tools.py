from typing import Iterable, List, Sequence


def moving_average(values: Sequence[float], window: int) -> List[float]:
    """Compute a simple moving average over a sequence of values.

    The output has the same length as the input. Values before the first full
    window are averaged over the available prefix.
    """
    if window <= 0:
        raise ValueError("window must be positive")
    result: List[float] = []
    acc = 0.0
    for i, v in enumerate(values):
        acc += v
        if i >= window:
            acc -= values[i - window]
        count = min(i + 1, window)
        result.append(acc / count)
    return result


def normalize(values: Iterable[float]) -> List[float]:
    """Normalize values to the range 0 to 1.

    If all values are the same, they are mapped to 0.5.
    """
    values_list = list(values)
    if not values_list:
        return []
    min_v = min(values_list)
    max_v = max(values_list)
    if max_v == min_v:
        return [0.5 for _ in values_list]
    return [(v - min_v) / (max_v - min_v) for v in values_list]


def percentage_change(old: float, new: float) -> float:
    """Compute the percentage change from old to new.

    The result is expressed as a percentage. For example, from 100 to 110
    returns 10.0.
    """
    if old == 0:
        raise ZeroDivisionError("old value must not be zero")
    return (new - old) / old * 100.0


def scale_value(value: float, old_min: float, old_max: float, new_min: float, new_max: float) -> float:
    """Scale a value from one range into another."""
    if old_max == old_min:
        raise ZeroDivisionError("old_max and old_min must not be equal")
    ratio = (value - old_min) / (old_max - old_min)
    return new_min + ratio * (new_max - new_min)
