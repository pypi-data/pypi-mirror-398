import os
from PIL import ImageFont

class Font:
    def __init__(self, size=16, font_name="Arial", font_path=None):
        self.size = size
        self.font_name = font_name
        self.font_path = font_path
        self.font = self.load_font()

    def load_font(self):
        try:
            if self.font_path and os.path.isfile(self.font_path):
                return ImageFont.truetype(self.font_path, self.size)

            return ImageFont.truetype(self.font_name, self.size)

        except Exception as e:
            print(f"[Font] Fallback used: {e}")
            return ImageFont.load_default()

    def set_size(self, new_size):
        self.size = new_size
        self.font = self.load_font()

    def set_font(self, new_font_name=None, new_font_path=None):
        if new_font_name:
            self.font_name = new_font_name
        self.font_path = new_font_path
        self.font = self.load_font()
