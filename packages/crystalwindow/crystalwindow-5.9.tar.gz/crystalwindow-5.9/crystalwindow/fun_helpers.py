import random
import time

# ============================================================
# RANDOM HELPERS
# ============================================================

def random_color():
    return (
        random.randint(0, 255),
        random.randint(0, 255),
        random.randint(0, 255)
    )

def random_palette(n=5):
    return [random_color() for _ in range(n)]

def random_pastel():
    return (
        random.randint(150, 255),
        random.randint(150, 255),
        random.randint(150, 255)
    )

def random_bool(chance=0.5):
    return random.random() < chance

def random_number(min_val, max_val):
    return random.randint(min_val, max_val)

def random_pos(w, h):
    return (
        random.randint(0, w),
        random.randint(0, h)
    )

def random_choice_weighted(items, weights):
    return random.choices(items, weights=weights, k=1)[0]


# ============================================================
# NAME / TEXT HELPERS
# ============================================================

def random_name(syllables=3):
    pool = ["ka","zi","lo","ra","mi","to","na","ve","xo","qu"]
    return "".join(random.choice(pool) for _ in range(syllables))


# ============================================================
# DIFFERENCE TELLER
# ============================================================
class difference:
    @staticmethod
    def tell(obj1, obj2):
        diffs = {}

        for attr in vars(obj1):
            if hasattr(obj2, attr):
                v1 = getattr(obj1, attr)
                v2 = getattr(obj2, attr)

                if v1 != v2:
                    diffs[attr] = difference._distance(v1, v2)

        return diffs

    @staticmethod
    def _distance(a, b):
        if isinstance(a, (int, float)) and isinstance(b, (int, float)):
            return abs(b - a)

        if isinstance(a, tuple) and isinstance(b, tuple):
            return sum(abs(b[i] - a[i]) for i in range(min(len(a), len(b))))

        return 1

    @staticmethod
    def _get_name(obj):
        # priority: explicit name attr
        if hasattr(obj, "name"):
            return obj.name

        # fallback: class name
        return obj.__class__.__name__

    @staticmethod
    def score(obj1, obj2):
        name1 = difference._get_name(obj1)
        name2 = difference._get_name(obj2)

        diffs = difference.tell(obj1, obj2)

        if not diffs:
            print(f"The Difference of '{name1}' and '{name2}' are: 0%")
            return 0

        max_score = len(diffs) * 100
        raw_score = sum(min(v, 100) for v in diffs.values())
        percent = int((raw_score / max_score) * 100)

        print(f"The Difference of '{name1}' and '{name2}' are: {percent}%")
        return percent


# ============================================================
# MATH / TWEEN HELPERS
# ============================================================

def lerp(a, b, t):
    return a + (b - a) * t

def clamp(val, minv=0, maxv=255):
    return max(minv, min(maxv, val))

def clamp01(t):
    return max(0.0, min(1.0, t))

def smoothstep(a, b, t):
    t = clamp01(t)
    t = t * t * (3 - 2 * t)
    return a + (b - a) * t

def approach(current, target, speed):
    if current < target:
        return min(current + speed, target)
    return max(current - speed, target)

def sign(x):
    return -1 if x < 0 else (1 if x > 0 else 0)


# ============================================================
# COLOR MODIFIERS
# ============================================================

def lighten(color, amount=30):
    r, g, b = color
    return (
        clamp(r + amount),
        clamp(g + amount),
        clamp(b + amount)
    )

def darken(color, amount=30):
    r, g, b = color
    return (
        clamp(r - amount),
        clamp(g - amount),
        clamp(b - amount)
    )


# ============================================================
# TIME HELPERS
# ============================================================

def timer_passed(start_time, duration):
    return (time.perf_counter() - start_time) >= duration


# ============================================================
# DEBUG OVERLAY
# ============================================================

class DebugOverlay:
    def __init__(self):
        self.active = True
        self.lines = []

    def toggle(self):
        self.active = not self.active

    def log(self, text):
        self.lines.append(str(text))
        if len(self.lines) > 6:
            self.lines.pop(0)

    def clear(self):
        self.lines.clear()

    def draw(self, win, fps=0):
        if not self.active:
            return

        y = 10
        win.draw_text(f"FPS: {int(fps)}", pos=(10, y))
        y += 20

        if hasattr(win, "mouse_pos"):
            mx, my = win.mouse_pos
            win.draw_text(f"Mouse: {mx},{my}", pos=(10, y))
            y += 20

        for line in self.lines:
            win.draw_text(line, pos=(10, y))
            y += 18
