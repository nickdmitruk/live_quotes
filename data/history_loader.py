from typing import List, Tuple
from .fxopen_ws import FXOpenWS, Bar

async def load_initial_bars(ws: FXOpenWS, symbol: str, periodicity: str, count: int) -> List[Bar]:
    # просто тонкая обёртка — уже реализовано в ws.get_history()
    # оставляем файл для будущих расширений (кэш, диск и т.п.)
    return await ws.get_history(symbol, periodicity, count)
