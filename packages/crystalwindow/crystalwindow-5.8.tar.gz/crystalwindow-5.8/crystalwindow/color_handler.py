# --------------------------------------
# CrystalWindow Color System v2.0
# --------------------------------------

class Colors:
    # BASIC COLORS
    Black       = (0, 0, 0)
    White       = (255, 255, 255)
    Red         = (255, 0, 0)
    Green       = (0, 255, 0)
    Blue        = (0, 0, 255)
    Yellow      = (255, 255, 0)
    Cyan        = (0, 255, 255)
    Magenta     = (255, 0, 255)
    Gray        = (120, 120, 120)
    DarkGray    = (40, 40, 40)

    # CRYSTALWINDOW CUSTOM
    CrystalBlue = (87, 199, 255)
    Accent      = (87, 199, 255)
    Success     = (76, 255, 111)
    Error       = (255, 68, 68)
    Transparent = (0, 0, 0, 0)  # full alpha


class Color:
    COLOR_NAMES = {name.lower(): value for name, value in Colors.__dict__.items()
                   if not name.startswith("__")}

    def __init__(self, r=None, g=None, b=None, a=255, hex_value=None):
        if isinstance(r, (tuple, list)):
            if len(r) == 3:
                self.r, self.g, self.b = r
                self.a = a
            elif len(r) == 4:
                self.r, self.g, self.b, self.a = r
            return

        if isinstance(r, str):
            name = r.lower()
            if name not in self.COLOR_NAMES:
                raise ValueError(f"unknown color name: {r}")
            data = self.COLOR_NAMES[name]
            if len(data) == 4:
                self.r, self.g, self.b, self.a = data
            else:
                self.r, self.g, self.b = data
                self.a = a
            return

        if hex_value is not None:
            self.r, self.g, self.b, self.a = self.hex_to_rgba(hex_value)
            return

        self.r = r or 0
        self.g = g or 0
        self.b = b or 0
        self.a = a

    @staticmethod
    def hex_to_rgba(hex_value: str):
        hex_value = hex_value.replace("#", "")
        if len(hex_value) == 6:
            r = int(hex_value[0:2], 16)
            g = int(hex_value[2:4], 16)
            b = int(hex_value[4:6], 16)
            a = 255
        elif len(hex_value) == 8:
            r = int(hex_value[0:2], 16)
            g = int(hex_value[2:4], 16)
            b = int(hex_value[4:6], 16)
            a = int(hex_value[6:8], 16)
        else:
            raise ValueError("bad hex")
        return r, g, b, a

    def to_tuple(self):
        return (self.r, self.g, self.b, self.a)

    def to_hex(self):
        return "#{:02X}{:02X}{:02X}{:02X}".format(self.r, self.g, self.b, self.a)

    def set_alpha(self, a):
        self.a = max(0, min(255, a))
        return self

    def brighten(self, amt=30):
        self.r = min(255, self.r + amt)
        self.g = min(255, self.g + amt)
        self.b = min(255, self.b + amt)
        return self

    def darken(self, amt=30):
        self.r = max(0, self.r - amt)
        self.g = max(0, self.g - amt)
        self.b = max(0, self.b - amt)
        return self

    @staticmethod
    def lerp(c1, c2, t: float):
        r = c1.r + (c2.r - c1.r) * t
        g = c1.g + (c2.g - c1.g) * t
        b = c1.b + (c2.b - c1.b) * t
        a = c1.a + (c2.a - c1.a) * t
        return Color(int(r), int(g), int(b), int(a))
