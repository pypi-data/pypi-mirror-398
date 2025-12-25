#gui.py
import random
import tkinter as tk
from crystalwindow import *
import time

# ----------------- Color Helpers -----------------
def hex_to_rgb(hex_str):
    """Convert hex color string to RGB tuple"""
    hex_str = hex_str.lstrip("#")
    return tuple(int(hex_str[i:i+2], 16) for i in (0, 2, 4))

def lerp_color(c1, c2, t):
    """Linearly interpolate between two colors"""
    return tuple(int(a + (b-a)*t) for a,b in zip(c1,c2))

# ----------------- GUI Elements -----------------
class Button:
    def __init__(self, pos, size, text,
                 color=(200,200,200),
                 hover_color=(255,255,255),
                 press_color=(180,180,180),
                 text_color=(0,0,0)):

        self.pos = pos
        self.size = size
        self.text = text

        self.color = color
        self.hover_color = hover_color
        self.press_color = press_color
        self.text_color = text_color

        # States
        self.hovered = False
        self._held = False
        self._clicked = False
        self._released = False

        self._was_down = False   # mouse prev frame
        self._cooldown = 0.05    # tiny debounce like Toggle
        self._last_click = 0

    # ======================================
    #   UPDATE (same style as slider/toggle)
    # ======================================
    def update(self, win):
        mx, my = win.mouse_pos
        x, y = self.pos
        w, h = self.size

        # Reset transient states
        self._clicked = False
        self._released = False

        # Hover
        self.hovered = (x <= mx <= x + w and y <= my <= y + h)

        mouse_down = win.mouse_pressed(1)

        # HELD
        if self.hovered and mouse_down:
            self._held = True
        else:
            self._held = False

        # CLICKED (fires once)
        now = time.time()
        if self.hovered and mouse_down and not self._was_down:
            if now - self._last_click >= self._cooldown:
                self._clicked = True
                self._last_click = now

        # RELEASED (fires once)
        if not mouse_down and self._was_down and self.hovered:
            self._released = True

        self._was_down = mouse_down

    # ======================================
    #   PUBLIC GETTERS
    # ======================================
    def clicked(self):
        return self._clicked

    def held(self):
        return self._held

    def released(self):
        return self._released

    def hovering(self):
        return self.hovered

    # ======================================
    #   DRAW
    # ======================================
    def draw(self, win):
        x, y = self.pos
        w, h = self.size

        # choose color by state
        if self._held:
            col = self.press_color
        elif self.hovered:
            col = self.hover_color
        else:
            col = self.color

        win.draw_rect(col, (x, y, w, h))
        win.draw_text(self.text, pos=(x + 5, y + 5), color=self.text_color)

class Label:
    def __init__(self, pos, text, color=(255,255,255), font="Arial", size=16):
        self.pos = pos
        self.text = text
        self.color = color
        self.font = font
        self.size = size

    def draw(self, win):
        win.draw_text_later(self.text, font=self.font, size=self.size, color=self.color, pos=self.pos)

# ----------------- Optional GUI Manager -----------------
class Fade:
    def __init__(self, win, color=(0,0,0), speed=10):
        self.win = win
        self.color = color
        self.speed = speed
        self.alpha = 0
        self.target = 0
        self.active = False
        self.done_callback = None
        self.overlay = Sprite.rect((0,0), win.width, win.height, color=self.color)
        self.overlay.alpha = 0

    def fade_in(self, on_done=None):
        """Fade from black to clear."""
        self.alpha = 255
        self.target = 0
        self.active = True
        self.done_callback = on_done

    def fade_out(self, on_done=None):
        """Fade from clear to black."""
        self.alpha = 0
        self.target = 255
        self.active = True
        self.done_callback = on_done

    def update(self):
        if not self.active:
            return

        if self.alpha < self.target:
            self.alpha = min(self.alpha + self.speed, self.target)
        elif self.alpha > self.target:
            self.alpha = max(self.alpha - self.speed, self.target)

        self.overlay.alpha = self.alpha

        if self.alpha == self.target:
            self.active = False
            if self.done_callback:
                self.done_callback()
                self.done_callback = None

    def draw(self):
        if self.alpha > 0:
            self.overlay.draw(self.win)

class GUIManager:
    def __init__(self):
        self.elements = []

    def add(self, element):
        self.elements.append(element)

    def draw(self, win):
        for e in self.elements:
            if hasattr(e, "draw"):
                e.draw(win)

    def update(self, win):
        for e in self.elements:
            if hasattr(e, "update"):
                e.update(win)
