import os
import random, json, pickle
from tkinter import PhotoImage

try:
    from PIL import Image, ImageTk
except ImportError:
    Image = None
    ImageTk = None

ASSETS = {}  # cache for all loaded images


# --------------------------------------------------------
# MAIN IMAGE LOADER
# --------------------------------------------------------
def load_image(path=None, flip_h=False, flip_v=False, size=None, color=None):
    """
    Unified image loader w/ caching, flips, and fallback.
    Handles:
      - path images
      - solid color gens
      - missing textures
      - Pillow and pure-tk fallback
    """

    # ----------------------------------------------------
    # NO PATH → GENERATE STATIC IMAGE
    # ----------------------------------------------------
    if path is None:
        if Image is None:
            # basic tk only
            w, h = size if size else (64, 64)
            img = PhotoImage(width=w, height=h)
            return img

        w, h = size if size else (64, 64)

        # solid or missing texture
        pil_img = (
            Image.new("RGB", (w, h), color) if color
            else generate_missing_texture((w, h))
        )

        # flips BEFORE resize
        if flip_h:
            pil_img = pil_img.transpose(Image.FLIP_LEFT_RIGHT)
        if flip_v:
            pil_img = pil_img.transpose(Image.FLIP_TOP_BOTTOM)

        if size:
            pil_img = pil_img.resize(size, Image.Resampling.LANCZOS)

        return ImageTk.PhotoImage(pil_img)

    # ----------------------------------------------------
    # USE FULL KEY AS CACHE
    # ----------------------------------------------------
    key = f"{path}|h={flip_h}|v={flip_v}|size={size}|color={color}"
    if key in ASSETS:
        return ASSETS[key]

    # ----------------------------------------------------
    # INVALID PATH → MISSING TEXTURE
    # ----------------------------------------------------
    if not os.path.exists(path):
        print(f"⚠ Missing image: {path}")
        fb = load_image(None, size=size, color=color)
        ASSETS[key] = fb
        return fb

    # ----------------------------------------------------
    # PIL NOT INSTALLED → PURE TK LOADING
    # ----------------------------------------------------
    if Image is None:
        try:
            img = PhotoImage(file=path)
            # cannot flip or resize without PIL, soz
            ASSETS[key] = img
            return img
        except:
            fb = load_image(None, size=size, color=color)
            ASSETS[key] = fb
            return fb

    # ----------------------------------------------------
    # LOAD USING PIL (BEST MODE)
    # ----------------------------------------------------
    try:
        pil_img = Image.open(path).convert("RGBA")

        # flips
        if flip_h:
            pil_img = pil_img.transpose(Image.FLIP_LEFT_RIGHT)
        if flip_v:
            pil_img = pil_img.transpose(Image.FLIP_TOP_BOTTOM)

        # resize AFTER flip
        if size:
            pil_img = pil_img.resize(size, Image.Resampling.LANCZOS)

        tk = ImageTk.PhotoImage(pil_img)
        ASSETS[key] = tk
        return tk

    except Exception as e:
        print(f"⚠ Error loading {path}: {e}")
        fb = load_image(None, size=size, color=color)
        ASSETS[key] = fb
        return fb


# ========================================================
# MISSING TEXTURE GENERATOR
# ========================================================
def generate_missing_texture(size):
    w, h = size
    img = Image.new("RGB", (w, h))
    px = img.load()

    pink = (255, 0, 255)
    black = (0, 0, 0)

    for y in range(h):
        for x in range(w):
            if (x // 8 + y // 8) % 2 == 0:
                px[x, y] = pink
            else:
                px[x, y] = black

    return img


# ========================================================
# PYGAME-STYLE FLIP HELPERS (FOR ALREADY-TK IMAGES)
# ========================================================
def flip_image(img, flip_h=False, flip_v=False):
    if Image is None or ImageTk is None:
        print("⚠ Pillow not installed; cannot flip images.")
        return img

    pil_img = ImageTk.getimage(img)

    if flip_h:
        pil_img = pil_img.transpose(Image.FLIP_LEFT_RIGHT)
    if flip_v:
        pil_img = pil_img.transpose(Image.FLIP_TOP_BOTTOM)

    return ImageTk.PhotoImage(pil_img)


def flip_horizontal(img):
    return flip_image(img, flip_h=True)


def flip_vertical(img):
    return flip_image(img, flip_v=True)
# --------------------------------------------------------
# LOOPING ANIMATIONS / IMAGES
# --------------------------------------------------------
class LoopAnim:
    def __init__(self, frames, speed=0.2):
        self.frames = frames
        self.i = 0
        self.speed = speed

    def next(self):
        """Return next frame automatically looping."""
        if not self.frames:
            return None

        self.i += self.speed
        if self.i >= len(self.frames):
            self.i = 0

        return self.frames[int(self.i)]


def loop_image(*imgs, speed=0.2):
    """
    Usage:
        anim = loop_image(img1, img2, img3)
        anim = loop_image(load_image("p1.png"), load_image("p2.png"))
    """
    frames = [x for x in imgs if x is not None]

    # If nothing was passed → fallback
    if not frames:
        print("⚠️ loop_image() got no frames.")
        fb = load_image("fallback.png") if os.path.exists("fallback.png") else None
        if fb is None:
            return LoopAnim([None], speed=speed)
        return LoopAnim([fb], speed=speed)

    return LoopAnim(frames, speed=speed)


# --------------------------------------------------------
# FOLDER LOADING
# --------------------------------------------------------
def load_folder_images(folder, nested=True):
    if not os.path.exists(folder):
        print(f"⚠️ Folder not found: {folder}")
        return {}

    result = {}
    for item in os.listdir(folder):
        full = os.path.join(folder, item)

        if os.path.isdir(full) and nested:
            result[item] = load_folder_images(full)

        elif item.lower().endswith((".png", ".gif")):
            result[item] = load_image(full)

    return result

#=========================================================
# LOAD FILES 
#=========================================================
def load_file(path):
    """
    Smart auto-loader for multiple formats.
    Reads:
      - .txt, .md, .cfg → text
      - .json           → parsed json
      - .py             → raw text
      - .bin, .dat      → raw bytes
      - .pickle, .pkl   → python objects
      - .png/.gif       → forwarded to load_image()
      - .pdf            → reads metadata only (no full extract)
    """

    if not os.path.exists(path):
        print(f"⚠️ Missing file: {path}")
        return None

    ext = path.lower().split(".")[-1]

    # ---------------- TEXT FILES ----------------
    if ext in ("txt", "md", "cfg", "ini", "py"):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return {
                    "type": "text",
                    "content": f.read()
                }
        except Exception as e:
            print(f"⚠️ Error reading text file: {e}")
            return None

    # ---------------- JSON ----------------
    if ext == "json":
        try:
            with open(path, "r", encoding="utf-8") as f:
                return {
                    "type": "json",
                    "content": json.load(f)
                }
        except Exception as e:
            print(f"⚠️ JSON error: {e}")
            return None

    # ---------------- PICKLE ----------------
    if ext in ("pickle", "pkl"):
        try:
            with open(path, "rb") as f:
                return {
                    "type": "pickle",
                    "content": pickle.load(f)
                }
        except Exception as e:
            print(f"⚠️ Pickle error: {e}")
            return None

    # ---------------- BINARY ----------------
    if ext in ("bin", "dat"):
        try:
            with open(path, "rb") as f:
                return {
                    "type": "binary",
                    "content": f.read()
                }
        except Exception as e:
            print(f"⚠️ Binary read error: {e}")
            return None

    # ---------------- PDF ----------------
    if ext == "pdf":
        try:
            with open(path, "rb") as f:
                head = f.read(1024)  # first 1KB for metadata
            return {
                "type": "pdf",
                "meta_preview": head,
                "note": "only metadata preview, not full pdf extract"
            }
        except Exception as e:
            print(f"⚠️ PDF read error: {e}")
            return None

    # ---------------- IMAGE ----------------
    if ext in ("png", "gif", "jpg", "jpeg"):
        try:
            return {
                "type": "image",
                "content": load_image(path)
            }
        except Exception as e:
            print(f"⚠️ Image load error: {e}")
            return None

    # ---------------- UNKNOWN TYPE ----------------
    try:
        with open(path, "rb") as f:
            raw = f.read()
        return {
            "type": "unknown",
            "content": raw
        }
    except:
        print("⚠️ Unknown file load failed")
        return None

# --------------------------------------------------------
# MUSIC PLACEHOLDER (REPLACED BY NEW SOUND ENGINE)
# --------------------------------------------------------
from matplotlib.pylab import size
import sounddevice as sd
import soundfile as sf
import threading


class Sound:
    def __init__(self, path, vol=1.0):
        self.path = path
        self.data, self.sr = sf.read(path, dtype="float32")
        self.volume = vol
        self._looping = False
        self._thread = None

    def _play_audio(self, loop=False):
        self._looping = loop
        while True:
            sd.play(self.data * self.volume, self.sr)
            sd.wait()
            if not self._looping:
                break

    def play(self):
        threading.Thread(target=self._play_audio, daemon=True).start()

    def play_once(self):
        self.stop()
        threading.Thread(target=self._play_audio, daemon=True).start()

    def loop(self):
        self.stop()
        self._thread = threading.Thread(
            target=self._play_audio, args=(True,), daemon=True
        )
        self._thread.start()

    def stop(self):
        self._looping = False
        sd.stop()

    def set_volume(self, v):
        self.volume = max(0, min(1, float(v)))


def load_sfx(path, vol=1.0):
    return Sound(path, vol)


# backwards compat but not real music engine
def load_music(path):
    print(f"[assets] use load_sfx() instead: {path}")


def play_music(loop=-1):
    print("[assets] play_music() disabled, use SoundObject.loop()")
