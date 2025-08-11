import matplotlib.pyplot as plt
from matplotlib.widgets import Button

class ToggleButton:
    def __init__(self, fig, label_left="Candles", label_right="Line", on_toggle=None):
        ax_btn = fig.add_axes([0.06, 0.06, 0.18, 0.06])  # x,y,w,h
        self.button = Button(ax_btn, f"Switch to {label_right}")
        self.mode = "candles"
        self.label_left = label_left
        self.label_right = label_right
        self.on_toggle = on_toggle
        self.button.on_clicked(self._clicked)

    def _clicked(self, _):
        self.mode = "line" if self.mode == "candles" else "candles"
        new_label = self.label_left if self.mode == "line" else self.label_right
        self.button.label.set_text(f"Switch to {new_label}")
        if self.on_toggle:
            self.on_toggle(self.mode)
