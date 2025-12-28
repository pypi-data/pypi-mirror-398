#draw_text_helper.py
from .window import Window

class DrawTextManager:
    def __init__(self):
        self.texts = []

    def add_text(self, text, pos=(0,0), size=16, color=(255,255,255), bold=False, italic=False, duration=None):
        """
        text: str
        pos: (x,y)
        size: int
        color: RGB tuple
        bold: bool
        italic: bool
        duration: float seconds or None for permanent
        """
        self.texts.append({
            "text": text,
            "pos": pos,
            "size": size,
            "color": color,
            "bold": bold,
            "italic": italic,
            "duration": duration,
            "timer": 0
        })

    def update(self, dt):
        # update timers and remove expired text
        for t in self.texts[:]:
            if t["duration"] is not None:
                t["timer"] += dt
                if t["timer"] >= t["duration"]:
                    self.texts.remove(t)

    def draw(self, win: Window):
        for t in self.texts:
            win.draw_text(
                t["text"],
                pos=t["pos"],
                size=t["size"],
                color=t["color"],
                bold=t["bold"],
                italic=t["italic"]
            )
