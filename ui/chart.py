import matplotlib
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from queue import Queue, Empty
from typing import List, Tuple

from config import (
    COLOR_BG, COLOR_GRID, GRID_ALPHA,
    COLOR_CANDLE_UP, COLOR_CANDLE_DOWN, COLOR_LINE
)
from ui.price_line import PriceLine

Bar = Tuple[int, float, float, float, float]

class ChartUI:
    def __init__(self, backend: str = "TkAgg"):
        matplotlib.use(backend)
        self.fig, self.ax = plt.subplots(figsize=(13, 7))
        self._style_axes()

        self.mode = "candles"
        self.bars: List[Bar] = []

        # Очередь для событий из фоновых потоков
        self.q: Queue = Queue()

        self.price_line = PriceLine(self.ax)

        # Анимация UI-потока
        self.ani = FuncAnimation(
            self.fig, self._animate, interval=500, blit=False, cache_frame_data=False
        )
        self.fig._ani_ref = self.ani

    # ---------- публичный API (потокобезопасный) ----------
    def post_history(self, bars: List[Bar]):
        self.q.put(("HISTORY", bars))

    def post_bar(self, bar: Bar):
        self.q.put(("BAR", bar))

    def post_tick_update(self, ts_ms: int, price: float, frame_ms: int):
        self.q.put(("TICK", (ts_ms, price, frame_ms)))

    # ---------- внутреннее ----------
    def _style_axes(self):
        # Цвет фона
        self.fig.patch.set_facecolor(COLOR_BG)
        self.ax.set_facecolor(COLOR_BG)

        # Сетка
        self.ax.grid(True, linestyle="--", alpha=GRID_ALPHA, color=COLOR_GRID)

        # Цвет и расположение осей
        self.ax.spines['bottom'].set_color('white')
        self.ax.spines['right'].set_color('white')
        self.ax.spines['top'].set_color('white')
        self.ax.spines['left'].set_visible(False)

        # Тики и подписи
        self.ax.tick_params(axis='x', colors='white')
        self.ax.tick_params(axis='y', colors='white')

        # Цена справа, время снизу
        self.ax.yaxis.tick_right()
        self.ax.yaxis.set_label_position("right")
        self.ax.xaxis.set_ticks_position("bottom")

    def _draw_line(self):
        if not self.bars:
            return
        xs = list(range(len(self.bars)))
        ys = [b[4] for b in self.bars]
        self.ax.plot(xs, ys, linewidth=1.3, color=COLOR_LINE)

    def _draw_candles(self):
        if not self.bars:
            return
        xs = list(range(len(self.bars)))
        width = 0.6
        for i, (t, o, h, l, c) in enumerate(self.bars):
            color = COLOR_CANDLE_UP if c >= o else COLOR_CANDLE_DOWN
            self.ax.plot([xs[i], xs[i]], [l, h], color=color, linewidth=1.0)
            y1, y2 = sorted((o, c))
            self.ax.add_patch(
                plt.Rectangle(
                    (xs[i] - width / 2, y1),
                    width,
                    max(y2 - y1, 1e-9),
                    edgecolor=color,
                    facecolor=color,
                    linewidth=1.0
                )
            )

    def _animate(self, _):
        changed = False
        while True:
            try:
                tag, payload = self.q.get_nowait()
            except Empty:
                break

            if tag == "HISTORY":
                self.bars = list(payload)
                changed = True
            elif tag == "BAR":
                t, o, h, l, c = payload
                if self.bars and self.bars[-1][0] == t:
                    self.bars[-1] = (t, o, h, l, c)
                else:
                    self.bars.append((t, o, h, l, c))
                changed = True
            elif tag == "TICK":
                ts_ms, price, frame_ms = payload
                if self.bars:
                    start_ms = (ts_ms // frame_ms) * frame_ms
                    if start_ms == self.bars[-1][0]:
                        t, o, h, l, _ = self.bars[-1]
                        if price > h:
                            h = price
                        if price < l:
                            l = price
                        self.bars[-1] = (t, o, h, l, price)
                        changed = True

        if not changed or not self.bars:
            return ()

        self.ax.clear()
        self._style_axes()

        if self.mode == "line":
            self._draw_line()
        else:
            self._draw_candles()

        # Линия текущей цены
        last_price = self.bars[-1][4]
        x_right = len(self.bars) + 0.5
        if self.price_line is None or self.price_line.ax is not self.ax:
            self.price_line = PriceLine(self.ax)
        self.price_line.update(last_price, x_right)

        # Лимиты и масштаб
        self.ax.set_xlim(-1, len(self.bars) + 2)
        self.ax.relim()
        self.ax.autoscale_view()

        return ()


#Потом надо сделать приближение и наслоение