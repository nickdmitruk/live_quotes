from config import COLOR_PRICE_LINE, COLOR_PRICE_LABEL_BG, COLOR_PRICE_LABEL_TEXT

class PriceLine:
    def __init__(self, ax):
        self.ax = ax
        self.hline = None
        self.label = None

    def update(self, price: float, x_right: float):
        # Линия
        if self.hline is None or self.hline.axes is None:
            self.hline = self.ax.axhline(price, color=COLOR_PRICE_LINE, linewidth=1, linestyle="--")
        else:
            self.hline.set_ydata([price, price])

        # Лейбл
        if self.label is None or self.label.axes is None:
            self.label = self.ax.text(
                x_right, price, f"{price:.5f}",
                va="center", ha="left",
                color=COLOR_PRICE_LABEL_TEXT,
                bbox=dict(boxstyle="round,pad=0.25", fc=COLOR_PRICE_LABEL_BG, ec="none", alpha=1.0),
                fontsize=9
            )
        else:
            self.label.set_position((x_right, price))
            self.label.set_text(f"{price:.5f}")
