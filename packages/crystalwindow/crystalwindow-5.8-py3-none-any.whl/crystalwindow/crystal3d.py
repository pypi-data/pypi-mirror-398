import math

def _lerp(a, b, t):
    return a + (b - a) * t

class CW3DShape:
    def __init__(self, kind, color, size=1.0, thickness=2, fill=None, texture=None,
                 points=5, inner_ratio=0.5):
        """
        kind: 'cube', 'triangle', 'circle', 'rectangle', 'pentagon', 'star', 'ngon'
        color: outline color (r,g,b)
        size: scale factor
        thickness: line thickness
        fill: optional fill color
        texture: optional texture placeholder
        points: number of points (for stars/ngons)
        inner_ratio: for stars, inner radius ratio (0.0-1.0)
        """
        self.kind = kind
        self.color = color
        self.size = size
        self.thickness = thickness
        self.fill = fill
        self.texture = texture

        self.rot_x = 0
        self.rot_y = 0
        self.smooth = False
        self.smooth_strength = 0.15
        self._sx = 0
        self._sy = 0

        self.points = points
        self.inner_ratio = inner_ratio

    def spin(self, rx, ry):
        self.rot_x += rx
        self.rot_y += ry

    def set_smooth(self, enable=True, strength=0.15):
        self.smooth = enable
        self.smooth_strength = strength

    def _smoothed(self):
        if not self.smooth:
            return self.rot_x, self.rot_y
        self._sx = _lerp(self._sx, self.rot_x, self.smooth_strength)
        self._sy = _lerp(self._sy, self.rot_y, self.smooth_strength)
        return self._sx, self._sy

    # ----------------------------------------------------------
    # DRAW ROUTE
    # ----------------------------------------------------------
    def draw(self, win):
        w, h = win.width, win.height
        rx, ry = self._smoothed()

        if self.kind == "cube":
            self._draw_cube(win, w, h, rx, ry)
        elif self.kind == "triangle":
            self._draw_triangle(win, w, h, rx, ry)
        elif self.kind == "circle":
            self._draw_circle(win, w, h, rx, ry)
        elif self.kind == "rectangle":
            self._draw_rectangle(win, w, h, rx, ry)
        elif self.kind == "pentagon":
            self._draw_polygon(win, w, h, 5, rx, ry)
        elif self.kind == "star":
            self._draw_star(win, w, h, rx, ry)
        elif self.kind == "ngon":
            self._draw_polygon(win, w, h, self.points, rx, ry)

    # ----------------------------------------------------------
    # GENERIC POLYGON
    # ----------------------------------------------------------
    def _draw_polygon(self, win, w, h, sides, rx, ry):
        cx, cy = w//2, h//2
        r = self.size * 80
        verts = []
        for i in range(sides):
            angle = -math.pi/2 + i * 2 * math.pi / sides
            verts.append((cx + math.cos(angle) * r, cy + math.sin(angle) * r))
        if self.fill:
            win.draw_polygon(verts, self.fill)
        win.draw_polygon_outline(verts, self.color, self.thickness)

    # ----------------------------------------------------------
    # STAR
    # ----------------------------------------------------------
    def _draw_star(self, win, w, h, rx, ry):
        cx, cy = w//2, h//2
        outer_r = self.size * 80
        inner_r = outer_r * self.inner_ratio
        verts = []
        step = math.pi / self.points
        ang = -math.pi / 2
        for i in range(self.points * 2):
            r = outer_r if i % 2 == 0 else inner_r
            verts.append((cx + math.cos(ang) * r, cy + math.sin(ang) * r))
            ang += step
        if self.fill:
            win.draw_polygon(verts, self.fill)
        win.draw_polygon_outline(verts, self.color, self.thickness)

# ==========================================================
# CW3D ENGINE (MANAGER)
# ==========================================================
class CW3D:
    def __init__(self, win):
        self.win = win
        self.shapes = []

    def add_cube(self, size=1.0, color=(255,255,255), thickness=2, fill=None):
        self.shapes.append(CW3DShape("cube", color, size, thickness, fill, None))

    def add_triangle(self, size=1.0, color=(255,255,255), thickness=2, fill=None):
        self.shapes.append(CW3DShape("triangle", color, size, thickness, fill, None))

    def add_circle(self, size=1.0, color=(255,255,255), thickness=2):
        self.shapes.append(CW3DShape("circle", color, size, thickness, None, None))

    def add_rectangle(self, size=1.0, color=(255,255,255), thickness=2, fill=None):
        self.shapes.append(CW3DShape("rectangle", color, size, thickness, fill, None))

    def add_pentagon(self, size=1.0, color=(255,255,255), thickness=2, fill=None):
        self.shapes.append(CW3DShape("pentagon", color, size, thickness, fill, None))

    def add_star(self, size=1.0, color=(255,255,255), thickness=2, fill=None, points=5, inner_ratio=0.5):
        self.shapes.append(CW3DShape("star", color, size, thickness, fill, None, points, inner_ratio))

    def add_ngon(self, size=1.0, points=6, color=(255,255,255), thickness=2, fill=None):
        self.shapes.append(CW3DShape("ngon", color, size, thickness, fill, None, points))

    def spin(self, rx, ry):
        for s in self.shapes:
            s.spin(rx, ry)

    def draw(self):
        for s in self.shapes:
            s.draw(self.win)
