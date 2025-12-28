from .gui import hex_to_rgb

class CrystalDraw:
    def __init__(self, win, brush_color="#00aaff", brush_size=8, canvas_rect=None):
        """
        win: CrystalWindow instance
        brush_color: color string or tuple
        brush_size: int
        canvas_rect: (x, y, w, h) optional drawing area
        """
        self.win = win
        self.brush_color = hex_to_rgb(brush_color)
        self.brush_size = brush_size
        self.drawing = False
        self.last_pos = None
        self.canvas_rect = canvas_rect or (0, 0, win.width, win.height)

    def set_color(self, color):
        if isinstance(color, str):
            self.brush_color = hex_to_rgb(color)
        else:
            self.brush_color = color

    def set_brush_size(self, size):
        self.brush_size = max(1, int(size))

    def clear(self):
        self.win.fill((255,255,255))

    def update(self):
        """Draw if mouse pressed."""
        x, y, w, h = self.canvas_rect
        mx, my = self.win.mouse_pos
        in_bounds = x <= mx <= x+w and y <= my <= y+h

        if self.win.mouse_pressed(1) and in_bounds:
            if self.last_pos:
                self.win.canvas.create_line(
                    self.last_pos[0], self.last_pos[1], mx, my,
                    fill=self._to_hex(self.brush_color),
                    width=self.brush_size,
                    capstyle="round", smooth=True
                )
            self.last_pos = (mx, my)
        else:
            self.last_pos = None

    def _to_hex(self, color):
        return f"#{color[0]:02x}{color[1]:02x}{color[2]:02x}"
