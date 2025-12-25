# === Window Management (tkinter version) ===
import random
import tkinter as tk
import base64, io, os, sys, contextlib, time, math

from pyscreeze import center

# === Boot ===
main_file = os.path.basename(sys.argv[0])
print(f"Welcome Future Dev!, running.. '{main_file}'")

# Base64 fallback logo (optional)
DEFAULT_LOGO_BASE64 = "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"

def decode_logo():
    """Decode the base64 logo and return a Tk PhotoImage."""
    try:
        logo_data = base64.b64decode(DEFAULT_LOGO_BASE64)
        with io.BytesIO(logo_data) as buf:
            return tk.PhotoImage(data=buf.read())
    except Exception:
        return None

class _CameraShake:
    def __init__(self):
        self.active = False
        self.intensity = 5
        self.end_time = 0
        self.offset = (0, 0)

    def start(self, intensity, duration):
        import time, random
        self.active = True
        self.intensity = intensity
        self.end_time = time.time() + duration

    def update(self):
        import time, random
        if not self.active:
            self.offset = (0, 0)
            return

        if time.time() > self.end_time:
            self.active = False
            self.offset = (0, 0)
            return

        self.offset = (
            random.randint(-self.intensity, self.intensity),
            random.randint(-self.intensity, self.intensity)
        )


class Window:
    # === Keymap to simplify key usage ===
    KEY_MAP = {
        # Arrows & Movement
        "left": "Left",
        "right": "Right",
        "up": "Up",
        "down": "Down",

        # Common control keys
        "space": "space",
        "enter": "Return",
        "backspace": "BackSpace",
        "tab": "Tab",
        "escape": "Escape",
        "Rshift": "Shift_R",
        "Lshift": "Shift_L",
        "Rctrl": "Control_R",
        "Lctrl": "Control_L",
        "alt": "Alt_L",

        # Letters
        "keya": "a", "keyb": "b", "keyc": "c", "keyd": "d",
        "keye": "e", "keyf": "f", "keyg": "g", "keyh": "h",
        "keyi": "i", "keyj": "j", "keyk": "k", "keyl": "l",
        "keym": "m", "keyn": "n", "keyo": "o", "keyp": "p",
        "keyq": "q", "keyr": "r", "keys": "s", "keyt": "t",
        "keyu": "u", "keyv": "v", "keyw": "w", "keyx": "x",
        "keyy": "y", "keyz": "z",

        # Numbers
        "0": "0", "1": "1", "2": "2", "3": "3", "4": "4",
        "5": "5", "6": "6", "7": "7", "8": "8", "9": "9",

        # Function keys
        "f1": "F1", "f2": "F2", "f3": "F3", "f4": "F4",
        "f5": "F5", "f6": "F6", "f7": "F7", "f8": "F8",
        "f9": "F9", "f10": "F10", "f11": "F11", "f12": "F12",

        # Editing and navigation
        "insert": "Insert",
        "delete": "Delete",
        "home": "Home",
        "end": "End",
        "pageup": "Prior",       # "Page Up" in Tkinter is "Prior"
        "pagedown": "Next",      # "Page Down" is "Next"

        # Lock keys
        "capslock": "Caps_Lock",
        "numlock": "Num_Lock",
        "scrolllock": "Scroll_Lock",

        # Symbols
        "+": "plus",
        "-": "minus",
        "/": "slash",
        "backslash": "backslash",
        "*": "asterisk",
        "=": "equal"
    }

    def __init__(self, width=640, height=480, title="Game Window", icon=None):
        self.width = width
        self.height = height
        self.title = title

        self.root = tk.Tk()
        self.root.title(title)
        self.root.protocol("WM_DELETE_WINDOW", self.quit)

        # === ICON HANDLING ===
        # === ICON HANDLING (SAFE + DEFERRED) ===
        self._icon_ref = None  # prevent GC

        if icon:
            try:
                if isinstance(icon, str) and os.path.exists(icon):
                    self._icon_ref = tk.PhotoImage(file=icon, master=self.root)
                elif isinstance(icon, tk.PhotoImage):
                    self._icon_ref = icon
                if self._icon_ref:
                    self.root.iconphoto(True, self._icon_ref)

            except Exception as e:
                print("⚠️ Icon load failed, using default", e)

        # fallback logo
        if not self._icon_ref:
            logo = decode_logo()
            if logo:
                self._icon_ref = logo
                self.root.iconphoto(True, logo)

        # === Canvas setup ===
        self.canvas = tk.Canvas(self.root, width=width, height=height, bg="#141432", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        # === State vars ===
        self.running = True
        self.keys = {}
        self.mouse_pos = (0, 0)
        self._mouse_pressed = (False, False, False)
        self.cam_x = 0
        self.cam_y = 0
        self.shake_timer = 0
        self.shake_strength = 0

        self.camerashake = _CameraShake()
        self._bg_color = (20, 20, 50)
        self.draw_calls = []
        self._key_last = {}  # new dict to store last press time per key
        self._key_cooldown = 0.0001  # seconds, tweak for faster/slower input

        # === Event bindings ===
        self.root.bind("<KeyPress>", self._on_keydown)
        self.root.bind("<KeyRelease>", self._on_keyup)
        self.root.bind("<Motion>", self._on_mousemove)
        self.root.bind("<ButtonPress>", self._on_mousedown)
        self.root.bind("<ButtonRelease>", self._on_mouseup)

    def _apply_camera_shake(self):
        if self.shake_timer > 0:
            self.shake_timer -= 1
            self.cam_x = random.randint(-self.shake_strength, self.shake_strength)
            self.cam_y = random.randint(-self.shake_strength, self.shake_strength)
        else:
            self.cam_x = 0
            self.cam_y = 0

    # === Input ===
    def _on_keydown(self, event):
        self.keys[event.keysym] = True

    def _on_keyup(self, event):
        self.keys[event.keysym] = False

    def _on_mousemove(self, event):
        self.mouse_pos = (event.x, event.y)

    def _on_mousedown(self, event):
        if event.num in [1, 2, 3]:
            pressed = list(self._mouse_pressed)
            pressed[event.num - 1] = True
            self._mouse_pressed = tuple(pressed)

    def _on_mouseup(self, event):
        if event.num in [1, 2, 3]:
            pressed = list(self._mouse_pressed)
            pressed[event.num - 1] = False
            self._mouse_pressed = tuple(pressed)


    # === Helpers ===
    def key_pressed(self, key):
        if isinstance(key, str):
            key = self.KEY_MAP.get(key, key)
    
        now = time.time()
        pressed = self.keys.get(key, False)
    
        last = self._key_last.get(key, 0)
        if pressed and (now - last) >= self._key_cooldown:
            self._key_last[key] = now
            return True
        
        return False

    def key_held(self, key):
        if isinstance(key, str):
            key = self.KEY_MAP.get(key, key)
        return self.keys.get(key, False)

    def mouse_pressed(self, button=1):
        return self._mouse_pressed[button - 1]
    def add_tab(self, title, widget):
        self.tabs.addTab(widget, title)

    # ====================================
    # Im gonna joke on the viewers here for a sec lmao
    # ====================================
    def f_crash(self, msg="oh no bruh... program ded 💀"):
        """start fake crash mode lol"""
        import tkinter as tk

        if hasattr(self, "_fcrash_window"):
            return  # already running

        self._fcrash_window = tk.Toplevel(self.root)
        self._fcrash_window.title("Fatal Error")
        self._fcrash_window.geometry("400x200")
        self._fcrash_window.configure(bg="#101010")
        self._fcrash_window.attributes("-topmost", True)

        tk.Label(
            self._fcrash_window,
            text=msg,
            fg="red",
            bg="#101010",
            font=("Consolas", 14, "bold")
        ).pack(pady=20)

        tk.Label(
            self._fcrash_window,
            text="System meltdown imminent...",
            fg="white",
            bg="#101010",
            font=("Consolas", 11)
        ).pack()

        # disable user clicking main window
        self.root.attributes("-disabled", True)

    def end_fcrash(self):
        """end fake crash prank"""
        if hasattr(self, "_fcrash_window"):
            self._fcrash_window.destroy()
            del self._fcrash_window

        # re-enable main window
        self.root.attributes("-disabled", False)

    # An actuall fucking Real crash that bricks your system sorry bud
    def crash(self, msg="REAL CRASH: u messed up bruh"):
        """actual crash (safe)."""
        raise RuntimeError(msg)

    # === Drawing ===
    def fill(self, color):
        """Fill background with a color"""
        if isinstance(color, str):
            if color.startswith("#"):
                fill_color = color
            else:
                fill_color = f"#{color}"
        elif isinstance(color, tuple):
            fill_color = f"#{color[0]:02x}{color[1]:02x}{color[2]:02x}"
        else:
            fill_color = "#000000"

        self._bg_color = fill_color
        self.canvas.delete("all")
        self.canvas.configure(bg=fill_color)

    # ------------------------------------------------------
    # INTERNAL: color / texture resolver
    # ------------------------------------------------------
    def _resolve_color_or_texture(self, color):
        """
        Returns (mode, value)
        mode = "rgb", "hex", "fallback", "texture"
        """
        # Texture?
        try:
            from PIL.ImageTk import PhotoImage as PILPhoto
            import tkinter
            if isinstance(color, (tkinter.PhotoImage, PILPhoto)):
                return ("texture", color)
        except:
            pass

        # Fallback dict
        if isinstance(color, dict) and color.get("fallback"):
            r, g, b = color["color"]
            return ("rgb", f"#{r:02x}{g:02x}{b:02x}")

        # Hex
        if isinstance(color, str) and color.startswith("#"):
            return ("hex", color)

        # Color instance
        try:
            if hasattr(color, "to_tuple"):
                r, g, b, *_ = color.to_tuple()
                return ("rgb", f"#{r:02x}{g:02x}{b:02x}")
        except:
            pass

        # RGB tuple
        if isinstance(color, (tuple, list)) and len(color) >= 3:
            r, g, b = color[0], color[1], color[2]
            return ("rgb", f"#{r:02x}{g:02x}{b:02x}")

        return ("rgb", "#ffffff")


    # ------------------------------------------------------
    # DRAW RECTANGLE
    # ------------------------------------------------------
    def draw_rect(self, color, rect):
        mode, value = self._resolve_color_or_texture(color)
        x, y, w, h = rect

        if mode == "texture":
            from PIL import Image, ImageTk
            try:
                pil = ImageTk.getimage(value).resize((w, h))
            except:
                return
            tk_tex = ImageTk.PhotoImage(pil)
            if not hasattr(self, "_tex_cache"): self._tex_cache = []
            self._tex_cache.append(tk_tex)
            self.canvas.create_image(x, y, image=tk_tex, anchor="nw")
        else:
            self.canvas.create_rectangle(
                x, y, x+w, y+h,
                fill=value, outline=""
            )


    # ------------------------------------------------------
    # DRAW LINE
    # ------------------------------------------------------
    def draw_line(self, p1, p2, color, width=2):
        mode, value = self._resolve_color_or_texture(color)

        if mode != "texture":
            self.canvas.create_line(
                p1[0], p1[1], p2[0], p2[1],
                fill=value, width=width
            )
            return

        # Texture line
        from PIL import Image, ImageDraw, ImageTk
        x1, y1 = p1
        x2, y2 = p2

        minx, maxx = int(min(x1, x2)), int(max(x1, x2))
        miny, maxy = int(min(y1, y2)), int(max(y1, y2))

        w = max(2, maxx - minx)
        h = max(2, maxy - miny)

        mask = Image.new("L", (w, h), 0)
        m = ImageDraw.Draw(mask)
        m.line([(x1-minx, y1-miny), (x2-minx, y2-miny)], fill=255, width=width)

        tex = ImageTk.getimage(value).resize((w, h))
        tex.putalpha(mask)

        tk_img = ImageTk.PhotoImage(tex)
        if not hasattr(self, "_line_tex"): self._line_tex = []
        self._line_tex.append(tk_img)

        self.canvas.create_image(minx, miny, image=tk_img, anchor="nw")

    # ------------------------------------------------------
    # DRAW CIRCLE  ——— FIXED SIGNATURE
    # ------------------------------------------------------
    def draw_circle(self, color, center, radius, width=0):
        mode, value = self._resolve_color_or_texture(color)

        # safe unpacking
        cx, cy = center[:2]

        if mode != "texture":
            self.canvas.create_oval(
                cx - radius, cy - radius,
                cx + radius, cy + radius,
                fill=value if width == 0 else "",
                outline=value if width > 0 else "",
                width=width
            )
            return

        # textured circle
        from PIL import Image, ImageDraw, ImageTk
        d = int(radius * 2)

        mask = Image.new("L", (d, d), 0)
        m = ImageDraw.Draw(mask)
        m.ellipse((0, 0, d, d), fill=255)

        tex = ImageTk.getimage(value).resize((d, d))
        tex.putalpha(mask)

        tk_img = ImageTk.PhotoImage(tex)
        if not hasattr(self, "_circ_tex"):
            self._circ_tex = []
        self._circ_tex.append(tk_img)

        self.canvas.create_image(cx - radius, cy - radius, image=tk_img, anchor="nw")

    # ------------------------------------------------------
    # DRAW POLYGON (FILL)
    # ------------------------------------------------------
    def draw_polygon(self, color, points):
        mode, value = self._resolve_color_or_texture(color)

        if mode != "texture":
            self.canvas.create_polygon(points, fill=value, outline="")
            return

        from PIL import Image, ImageDraw, ImageTk
        xs, ys = zip(*points)
        minx, maxx = min(xs), max(xs)
        miny, maxy = min(ys), max(ys)

        w = int(maxx - minx)
        h = int(maxy - miny)
        if w < 2 or h < 2: return

        mask = Image.new("L", (w, h), 0)
        m = ImageDraw.Draw(mask)
        m.polygon([(x-minx, y-miny) for x, y in points], fill=255)

        tex = ImageTk.getimage(value).resize((w, h))
        tex.putalpha(mask)

        tk_img = ImageTk.PhotoImage(tex)
        if not hasattr(self, "_poly_tex"): self._poly_tex = []
        self._poly_tex.append(tk_img)

        self.canvas.create_image(minx, miny, image=tk_img, anchor="nw")


    # ------------------------------------------------------
    # DRAW POLYGON OUTLINE
    # ------------------------------------------------------
    def draw_polygon_outline(self, color, points, width=2):
        mode, value = self._resolve_color_or_texture(color)

        if mode != "texture":
            self.canvas.create_polygon(points, outline=value, width=width, fill="")
            return

        from PIL import Image, ImageDraw, ImageTk
        xs, ys = zip(*points)
        minx, maxx = min(xs), max(xs)
        miny, maxy = min(ys), max(ys)

        w = int(maxx - minx)
        h = int(maxy - miny)

        mask = Image.new("L", (w, h), 0)
        m = ImageDraw.Draw(mask)
        m.line([(x-minx, y-miny) for x, y in points] +
               [(points[0][0]-minx, points[0][1]-miny)],
               fill=255, width=width)

        tex = ImageTk.getimage(value).resize((w, h))
        tex.putalpha(mask)

        tk_img = ImageTk.PhotoImage(tex)
        if not hasattr(self, "_poly_oline_tex"): self._poly_oline_tex = []
        self._poly_oline_tex.append(tk_img)

        self.canvas.create_image(minx, miny, image=tk_img, anchor="nw")


    # ------------------------------------------------------
    # DRAW STAR
    # ------------------------------------------------------
    def draw_star(self, color, center, outer_radius, inner_radius=None,
                  points=5, stroke=None, stroke_width=2):

        if inner_radius is None:
            inner_radius = outer_radius * 0.5

        cx, cy = center
        step = math.pi / points
        ang = -math.pi / 2
        verts = []

        for i in range(points * 2):
            r = outer_radius if i % 2 == 0 else inner_radius
            verts.append((cx + math.cos(ang) * r,
                          cy + math.sin(ang) * r))
            ang += step

        self.draw_polygon(color, verts)
        if stroke:
            self.draw_polygon_outline(stroke, verts, stroke_width)

    # ------------------------------------------------------
    # DRAW TEXT — SAFE, FIXED, TKINTER-PROOF
    # ------------------------------------------------------
    def draw_text(self, text, font="Arial", size=16, color=(255, 255, 255), pos=(0, 0), **kwargs):
        # extract style kwargs safely (DO NOT send them to tkinter)
        bold = kwargs.pop("bold", False)
        italic = kwargs.pop("italic", False)

        # scale
        scaled_size = size

        # resolve color or texture
        mode, value = self._resolve_color_or_texture(color)

        # build font style string
        style = ""
        if bold:
            style += "bold "
        if italic:
            style += "italic"
        style = style.strip()

        # tkinter font tuple
        if style:
            font_tuple = (font, scaled_size, style)
        else:
            font_tuple = (font, scaled_size)

        # ---------------- NORMAL COLOR TEXT ----------------
        if mode != "texture":
            fill = f"#{color[0]:02x}{color[1]:02x}{color[2]:02x}"

            # HARD DELETE unsupported kwargs (just in case)
            kwargs.pop("bold", None)
            kwargs.pop("italic", None)

            # allowed kwargs ONLY
            ALLOWED = {"anchor", "justify", "tags"}
            safe_kwargs = {k: v for k, v in kwargs.items() if k in ALLOWED}

            self.canvas.create_text(
                pos[0], pos[1],
                text=text,
                fill=fill,
                font=font_tuple,
                anchor="nw",
                **safe_kwargs
            )
            return

        # ---------------- TEXTURED TEXT ----------------
        from PIL import Image, ImageDraw, ImageFont, ImageTk

        # try load font with style
        try:
            fnt = ImageFont.truetype(font + ".ttf", scaled_size)
        except:
            fnt = ImageFont.load_default()

        # measure text
        temp = Image.new("L", (1, 1), 0)
        d = ImageDraw.Draw(temp)

        try:
            bbox = d.textbbox((0, 0), text, font=fnt)
            tw = bbox[2] - bbox[0]
            th = bbox[3] - bbox[1]
        except:
            tw, th = d.textsize(text, font=fnt)

        pad = int(size * 0.25)
        tw += pad
        th += pad

        # alpha mask for texture
        mask = Image.new("L", (tw, th), 0)
        m = ImageDraw.Draw(mask)
        m.text((pad//2, pad//2), text, font=fnt, fill=255)

        # texture
        tex = ImageTk.getimage(value).resize((tw, th))
        tex.putalpha(mask)

        tk_img = ImageTk.PhotoImage(tex)
        if not hasattr(self, "_text_tex"):
            self._text_tex = []
        self._text_tex.append(tk_img)

        self.canvas.create_image(
            pos[0], pos[1],
            image=tk_img,
            anchor="nw"
        )

    # ------------------------------------------------------
    # DRAW TEXT LATER (Queued) — CLEAN KWARGS BEFORE SAVE
    # ------------------------------------------------------
    def draw_text_later(self, *args, **kwargs):
        # remove style keys NOW so they never come back
        kwargs.pop("bold", None)
        kwargs.pop("italic", None)

        # allowed kwargs ONLY (same list as draw_text)
        ALLOWED = {"anchor", "justify", "tags"}
        clean_kwargs = {k: v for k, v in kwargs.items() if k in ALLOWED}

        self.draw_calls.append(("text", args, clean_kwargs))


    # === Update + Loop ===
    def run(self, update_func=None, bg=(20, 20, 50)):
        self._bg_color = f"#{bg[0]:02x}{bg[1]:02x}{bg[2]:02x}"
        def loop():
            if not self.running:
                return
            self.fill(self._bg_color)
            if update_func:
                update_func(self)
            for call in self.draw_calls:
                ctype = call[0]
                if ctype == "rect":
                    _, color, x, y, w, h = call
                    col = f"#{color[0]:02x}{color[1]:02x}{color[2]:02x}"
                    self.canvas.create_rectangle(x, y, x + w, y + h, fill=col, outline="")
                elif ctype == "circle":
                    _, color, x, y, r = call
                    col = f"#{color[0]:02x}{color[1]:02x}{color[2]:02x}"
                    self.canvas.create_oval(x - r, y - r, x + r, y + r, fill=col, outline="")
                elif ctype == "text":
                    self.draw_text(*call[1], **call[2])
            self.draw_calls.clear()
            self.root.after(16, loop)  # ~60fps
        loop()
        self.root.mainloop()

    def quit(self):
        print(f"Bye Bye!, Future Dev!. quitting '{main_file}'......")
        self.running = False
        self.root.destroy()
        sys.exit()
