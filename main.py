import asyncio
import os
from dotenv import load_dotenv
from threading import Thread
import matplotlib.pyplot as plt  # <-- добавили

from ui.chart import ChartUI
from data.fxopen_ws import FXOpenWS
from utils.data_utils import update_with_tick

# ---------- Константы ----------
SYMBOL = "EURUSD"
TIMEFRAME = "M1"
HISTORY_BARS = 1000

# ---------- Загрузка .env ----------
load_dotenv()
ENV = {
    "FEED_URL": os.getenv("FEED_URL"),
    "WEB_API_ID": os.getenv("WEB_API_ID"),
    "WEB_API_KEY": os.getenv("WEB_API_KEY"),
    "WEB_API_SECRET": os.getenv("WEB_API_SECRET")
}


def run_ws(chart: ChartUI):
    ws = FXOpenWS(
        ENV["FEED_URL"],
        ENV["WEB_API_ID"],
        ENV["WEB_API_KEY"],
        ENV["WEB_API_SECRET"]
    )

    frame_ms = 60_000  # M1
    current_bar = None

    def on_history(bars):
        print(f"📥 История: {len(bars)} баров")
        chart.post_history(bars)

    def on_tick(ts_ms, price):
        nonlocal current_bar
        new_bar, cb = update_with_tick(current_bar, ts_ms, price, frame_ms)

        if new_bar and current_bar is not None:
            t = current_bar["start_ms"]
            chart.post_bar((t, current_bar["open"], current_bar["high"], current_bar["low"], current_bar["close"]))

        current_bar = cb
        chart.post_bar((cb["start_ms"], cb["open"], cb["high"], cb["low"], cb["close"]))
        chart.post_tick_update(ts_ms, price, frame_ms)

    def on_bar(bar_tuple):
        chart.post_bar(bar_tuple)

    ws.on_history = on_history
    ws.on_tick = on_tick
    ws.on_bar = on_bar

    asyncio.run(ws.run(SYMBOL, TIMEFRAME, HISTORY_BARS))


if __name__ == "__main__":
    chart = ChartUI()

    # Кнопка переключения типа графика
    ax_btn = chart.fig.add_axes([0.85, 0.95, 0.1, 0.04])
    from matplotlib.widgets import Button
    btn = Button(ax_btn, "Switch to Line")

    def toggle_chart_type(_event):
        if chart.mode == "candles":
            chart.mode = "line"
            btn.label.set_text("Switch to Candles")
        else:
            chart.mode = "candles"
            btn.label.set_text("Switch to Line")

    btn.on_clicked(toggle_chart_type)

    # Запуск WS в отдельном потоке
    t = Thread(target=run_ws, args=(chart,), daemon=True)
    t.start()

    # Показываем окно (ChartUI не имеет .show())
    plt.show(block=True)
