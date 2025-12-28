"""
CrystalWindow FileHelper
------------------------
Handles saving/loading text, JSON, and pickle files.
Uses Tk file dialogs, auto-creates 'saves/' folder,
and supports image fallback + resizing.
"""

import os
import json
import pickle
import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk
from .assets import load_image


class FileHelper:
    """CrystalWindow integrated file helper."""

    def __init__(self, default_save_folder="saves"):
        self.default_save_folder = default_save_folder
        self.last_dir = "."
        os.makedirs(self.default_save_folder, exist_ok=True)

    # ======================================================================
    # INTERNAL TK ROOT
    # ======================================================================
    def _make_root(self):
        """Create hidden Tk root without any custom icon."""
        root = tk.Tk()
        root.withdraw()
        return root

    # ======================================================================
    # SAFE RESIZE HANDLER
    # ======================================================================
    def _resize_any(self, img, size):
        """Resize PIL image safely and return Tk PhotoImage."""
        if size is None:
            # If already a PhotoImage, keep as is
            if isinstance(img, Image.Image):
                return ImageTk.PhotoImage(img)
            return img

        if isinstance(img, Image.Image):
            pil = img.resize(size, Image.Resampling.LANCZOS)
            return ImageTk.PhotoImage(pil)

        print("[WARN] Unknown image type, cannot resize.")
        return img

    # ======================================================================
    # IMAGE OPENING WITH RETRY + FALLBACK + RESIZE
    # ======================================================================
    def open_img(
        self,
        start_in=None,
        retry=False,
        fallback_size=(64, 64),
        fallback_color=(255, 0, 255),
        resize=None,
        return_pil=False
    ):
        """
        Open an image using a dialog.

        Params:
            retry=True → reopen dialog until image selected
            fallback_size → fallback square size when cancelled
            fallback_color → fallback color
            resize=(w, h) → resize final image

        Returns dict:
            - Always returns `image` as a Tk-compatible image (ImageTk.PhotoImage or PhotoImage)
            - If `return_pil=True` and Pillow is available, also returns `pil` with the PIL Image
            { "path": str|None, "image": PhotoImage, "pil": PIL.Image.Image|None, "cancelled": bool }
        """

        while True:
            root = self._make_root()
            folder = start_in if start_in else self.last_dir

            path = filedialog.askopenfilename(
                title="Select image",
                initialdir=folder,
                filetypes=[
                    ("Image files", "*.png;*.jpg;*.jpeg;*.gif;*.bmp"),
                    ("All files", "*.*")
                ]
            )
            root.destroy()

            # ------------------------ CANCELLED ------------------------
            if not path:
                if retry:
                    print("⚠️ No image selected. Trying again...")
                    continue

                print("⚠️ No image selected. Using fallback.")
                # Create a PIL fallback if Pillow available, then make a Tk image
                if Image is not None:
                    w, h = fallback_size if fallback_size else (64, 64)
                    pil_fb = Image.new("RGB", (w, h), fallback_color)
                    if resize:
                        pil_fb = pil_fb.resize(resize, Image.Resampling.LANCZOS)
                    tk_fb = ImageTk.PhotoImage(pil_fb)
                    if return_pil:
                        return {"path": None, "image": tk_fb, "pil": pil_fb, "cancelled": True}
                    return {"path": None, "image": tk_fb, "pil": None, "cancelled": True}

                # Fallback to existing asset loader (returns PhotoImage)
                fb = load_image(None, size=fallback_size, color=fallback_color)
                if resize:
                    fb = self._resize_any(fb, resize)
                return {"path": None, "image": fb, "pil": None, "cancelled": True}

            # ------------------------ LOAD IMAGE -----------------------
            self.last_dir = os.path.dirname(path)

            try:
                # If Pillow is available, open with PIL and create a Tk PhotoImage for compatibility
                if Image is not None:
                    pil_img = Image.open(path).convert("RGBA")
                    if resize:
                        pil_img = pil_img.resize(resize, Image.Resampling.LANCZOS)
                    tk_img = ImageTk.PhotoImage(pil_img)
                    if return_pil:
                        return {"path": path, "image": tk_img, "pil": pil_img, "cancelled": False}
                    return {"path": path, "image": tk_img, "pil": None, "cancelled": False}

                # Otherwise fall back to the asset loader which returns a Tk image
                img = load_image(path)
                if resize:
                    img = self._resize_any(img, resize)
                return {"path": path, "image": img, "pil": None, "cancelled": False}

            except Exception as e:
                print(f"[ERROR] Failed to load image '{path}': {e}")

                if retry:
                    print("Trying again...")
                    continue

                # On error, provide a fallback (PIL if available)
                if Image is not None:
                    w, h = fallback_size if fallback_size else (64, 64)
                    pil_fb = Image.new("RGB", (w, h), fallback_color)
                    if resize:
                        pil_fb = pil_fb.resize(resize, Image.Resampling.LANCZOS)
                    tk_fb = ImageTk.PhotoImage(pil_fb)
                    if return_pil:
                        return {"path": None, "image": tk_fb, "pil": pil_fb, "cancelled": True}
                    return {"path": None, "image": tk_fb, "pil": None, "cancelled": True}

                fb = load_image(None, size=fallback_size, color=fallback_color)
                if resize:
                    fb = self._resize_any(fb, resize)
                return {"path": None, "image": fb, "pil": None, "cancelled": True}

    # ======================================================================
    # FILE DIALOGS
    # ======================================================================
    def ask_save_file(self, default_name="save.json",
                      filetypes=[("JSON files", "*.json"), ("All files", "*.*")]):
        root = self._make_root()

        path = filedialog.asksaveasfilename(
            title="Save As",
            initialdir=self.default_save_folder,
            initialfile=default_name,
            filetypes=filetypes,
            defaultextension=filetypes[0][1]
        )
        root.destroy()
        return path if path else None

    def ask_open_file(self, filetypes=[("JSON files", "*.json"), ("All files", "*.*")]):
        root = self._make_root()

        path = filedialog.askopenfilename(
            title="Open File",
            initialdir=self.default_save_folder,
            filetypes=filetypes
        )
        root.destroy()
        return path if path else None

    # ======================================================================
    # PATH HANDLING
    # ======================================================================
    def _resolve_path(self, filename):
        if not filename:
            return None
        if os.path.isabs(filename):
            return filename
        return os.path.join(self.default_save_folder, filename)

    # ======================================================================
    # TEXT FILES
    # ======================================================================
    def save_text(self, filename, content):
        path = self._resolve_path(filename)
        if not path:
            print("[CANCELLED] No save path provided.")
            return None
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"[INFO] Text saved to: {path}")
        return path

    def load_text(self, filename):
        path = self._resolve_path(filename)
        if path and os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        print(f"[WARN] Text file not found: {path}")
        return None

    # ======================================================================
    # JSON FILES
    # ======================================================================
    def save_json(self, filename, data):
        path = self._resolve_path(filename)
        if not path:
            print("[CANCELLED] No save path provided.")
            return None
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
        print(f"[INFO] JSON saved to: {path}")
        return path

    def load_json(self, filename):
        path = self._resolve_path(filename)
        if path and os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        print(f"[WARN] JSON file not found: {path}")
        return None

    # ======================================================================
    # PICKLE FILES
    # ======================================================================
    def save_pickle(self, filename, obj):
        path = self._resolve_path(filename)
        if not path:
            print("[CANCELLED] No save path provided.")
            return None
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as f:
            pickle.dump(obj, f)
        print(f"[INFO] Pickle saved to: {path}")
        return path

    def load_pickle(self, filename):
        path = self._resolve_path(filename)
        if path and os.path.exists(path):
            with open(path, "rb") as f:
                return pickle.load(f)
        print(f"[WARN] Pickle file not found: {path}")
        return None
