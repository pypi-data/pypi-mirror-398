from crystalwindow import *

class DrawHelper:
    def rect(self, win, x, y, w, h, color):
        win.draw_rect(color, (x, y, w, h))
        return self

    def square(self, win, x, y, size, color):
        win.draw_rect(color, (x, y, size, size))
        return self

    def circle(self, win, x, y, radius, color):
        win.draw_circle(color, (x, y), radius)
        return self

    def triangle(self, win, points, color):
        flat_points = [coord for pt in points for coord in pt]
        win.canvas.create_polygon(flat_points, fill=win._to_hex(color))
        return self

    def text(self, win, text, font="Arial", size=16, x=0, y=0, color=(255,255,255), bold=False, cursive=False):
        win.draw_text(text, font=font, size=size, pos=(x, y), color=color, bold=bold, italic=cursive)
        return self

    def gradient_rect(self, win, x, y, w, h, start_color, end_color, vertical=True):
        for i in range(h if vertical else w):
            ratio = i / (h if vertical else w)
            r = int(start_color[0]*(1-ratio) + end_color[0]*ratio)
            g = int(start_color[1]*(1-ratio) + end_color[1]*ratio)
            b = int(start_color[2]*(1-ratio) + end_color[2]*ratio)
            color = f"#{r:02x}{g:02x}{b:02x}"
            if vertical:
                win.canvas.create_line(x, y+i, x+w, y+i, fill=color)
            else:
                win.canvas.create_line(x+i, y, x+i, y+h, fill=color)
        return self
