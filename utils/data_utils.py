from typing import List, Tuple
from math import nan
from datetime import timedelta, datetime, timezone

# Храним бары как tuples: (t_ms, open, high, low, close)
Bar = Tuple[int, float, float, float, float]

def compress_time_indices(bars: List[Bar]) -> List[int]:
    """
    Склейка времени: вместо datetime используем индекс 0..N-1.
    Так на графике не будет дыр на выходных.
    """
    return list(range(len(bars)))

def line_series_with_gaps(bars: List[Bar], tf_minutes: int) -> Tuple[List[int], List[float]]:
    """
    Для линейного графика можно вставлять NaN на больших разрывах,
    но мы уже «склеили» по индексу — потому просто берём Close.
    """
    x = compress_time_indices(bars)
    y = [b[4] for b in bars]
    return x, y

def clamp_last_n(bars: List[Bar], n: int) -> List[Bar]:
    return bars[-n:] if len(bars) > n else bars

def update_with_tick(current_bar: dict, ts_ms: int, price: float, frame_ms: int):
    """
    Обновляет словарь текущего бара O/H/L/C. Возвращает True, если начался новый бар.
    """
    start_ms = (ts_ms // frame_ms) * frame_ms
    if not current_bar or current_bar["start_ms"] != start_ms:
        return True, {
            "start_ms": start_ms,
            "open": price,
            "high": price,
            "low": price,
            "close": price
        }
    # апдейт
    cb = current_bar
    cb["close"] = price
    if price > cb["high"]: cb["high"] = price
    if price < cb["low"]:  cb["low"] = price
    return False, cb
