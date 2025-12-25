import time
from .window import Window


# ============================================================
#   T O G G L E  (behaves EXACTLY like old version)
# ============================================================

class Toggle:
    def __init__(self, rect, value=False,
                 color=(200, 200, 200), hover_color=(255, 255, 255),
                 cooldown=0.1):

        self.rect = rect
        self.value = value
        self.color = color
        self.hover_color = hover_color

        self.hovered = False
        self.cooldown = cooldown
        self._last_toggle = 0

    def update(self, win: Window):
        mx, my = win.mouse_pos
        x, y, w, h = self.rect

        # hover check
        self.hovered = (x <= mx <= x + w and y <= my <= y + h)

        # cooldown logic (same as old ver)
        now = time.time()
        if self.hovered and win.mouse_pressed(1):
            if now - self._last_toggle >= self.cooldown:
                self.value = not self.value
                self._last_toggle = now

    def draw(self, win: Window):
        draw_color = self.hover_color if self.hovered else self.color
        win.draw_rect(draw_color, self.rect)

        # ON glow (same as old ver)
        if self.value:
            inner = (
                self.rect[0] + 4,
                self.rect[1] + 4,
                self.rect[2] - 8,
                self.rect[3] - 8,
            )
            win.draw_rect((0, 255, 0), inner)



# ============================================================
#   S L I D E R  (old logic fully restored)
# ============================================================

class Slider:
    def __init__(self, rect, min_val=0, max_val=100, value=50,
                 color=(150, 150, 150), handle_color=(255, 0, 0),
                 handle_radius=10):

        self.rect = rect
        self.min_val = min_val
        self.max_val = max_val
        self.value = value

        self.color = color
        self.handle_color = handle_color
        self.handle_radius = handle_radius

        self.dragging = False

    def update(self, win: Window):
        mx, my = win.mouse_pos
        x, y, w, h = self.rect

        # compute handle pos
        handle_x = x + ((self.value - self.min_val) /
                        (self.max_val - self.min_val)) * w
        handle_y = y + h // 2

        inside_slider = (x <= mx <= x + w and y <= my <= y + h)

        if win.mouse_pressed(1):
            # start drag if within slider area (old behavior)
            if not self.dragging and inside_slider:
                self.dragging = True
        else:
            self.dragging = False

        # dragging updates value
        if self.dragging:
            rel = max(0, min(mx - x, w))
            t = rel / w
            self.value = self.min_val + t * (self.max_val - self.min_val)

    def draw(self, win: Window):
        x, y, w, h = self.rect

        # slider bar
        win.draw_rect(self.color, (x, y + h // 2 - 2, w, 4))

        # handle pos
        handle_x = x + ((self.value - self.min_val) /
                        (self.max_val - self.min_val)) * w
        handle_y = y + h // 2

        win.draw_circle(self.handle_color,
                        (int(handle_x), int(handle_y)),
                        self.handle_radius)
