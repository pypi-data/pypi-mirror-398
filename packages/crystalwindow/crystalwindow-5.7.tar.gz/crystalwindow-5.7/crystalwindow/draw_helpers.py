from .window import Window

def gradient_rect(win, rect, color_start, color_end, vertical=True):
    x,y,w,h = rect
    for i in range(h if vertical else w):
        t = i/(h if vertical else w)
        r = int(color_start[0]*(1-t) + color_end[0]*t)
        g = int(color_start[1]*(1-t) + color_end[1]*t)
        b = int(color_start[2]*(1-t) + color_end[2]*t)
        if vertical:
            win.draw_rect((r,g,b), (x,y+i,w,1))
        else:
            win.draw_rect((r,g,b), (x+i,y,1,h))

class CameraShake:
    def __init__(self, intensity=5, duration=1):
        self.intensity = intensity
        self.time_left = duration
        self.offset = (0, 0)

    def update(self, dt):
        import random

        if self.time_left > 0:
            self.time_left -= dt
            self.offset = (
                random.randint(-self.intensity, self.intensity),
                random.randint(-self.intensity, self.intensity)
            )
            return True
        else:
            self.offset = (0, 0)
            return False 
