# 💎 CrystalWindow - Master Import Hub
from .ver_warner import check_for_update
check_for_update("crystalwindow")

# === Core Systems ===
from .window import Window
from .sprites import Sprite, CollisionHandler
from .tilemap import TileMap
from .objects import Player, Block, Enemy
from .gravity import Gravity
from .FileHelper import FileHelper
from .math import Mathematics

# === Assets & Animation ===
from .assets import (
    load_image,
    load_folder_images,
    load_music,
    play_music,
    flip_image,
    flip_horizontal,
    flip_vertical,
    LoopAnim,
    loop_image,
    load_file,
    Sound,
)
from .animation import Animation

# === Collision ===
from .collision import check_collision, resolve_collision

# === GUI & Extensions ===
from .gui import Button, Label, GUIManager, hex_to_rgb, Fade
from .gui_ext import Toggle, Slider

# === Time System ===
from .clock import Clock, CountdownTimer

# === Drawing Helpers ===
from .draw_helpers import gradient_rect, CameraShake
from .draw_rects import DrawHelper
from .draw_text_helper import DrawTextManager
from .draw_tool import CrystalDraw

# === Misc Helpers ===
from .fun_helpers import random_name, DebugOverlay, random_color, random_palette, lerp, random_number, random_pos, random_bool, random_choice_weighted, difference
from .camera import Camera
from .color_handler import Colors, Color
from .websearch import SearchResult, WebBrowse

# === 3D Engine ===
from .crystal3d import CW3DShape, CW3D

# === Chatting/VPN Engine =====
from .chatvpn import ChatVPN, ChatVPNServer

# ==== Message Bus ====
from .messagebus import send_message, view_message, clear_messages

# ==== Fonts =======
from .Fonts import Font

# === App/Window ====
from .apphelper import GameAppHelper

# === System ===
from .System import System, Watchdog

# === Score System ===
from .scores import Score

__all__ = [
    # --- Core ---
    "Window", "Sprite", "TileMap", "Player", "Block", "Enemy", "Gravity", "FileHelper", "Mathematics",

    # --- Assets & Animation ---
    "load_image",
    "load_folder_images",
    "load_music",
    "play_music",
    "flip_image",
    "flip_horizontal",
    "flip_vertical",
    "Animation",
    "LoopAnim",
    "loop_image",
    "load_file",
    "Sound",

    # --- Collision ---
    "check_collision", "resolve_collision", "CollisionHandler",

    # --- GUI ---
    "Button", "Label", "GUIManager", "random_color", "hex_to_rgb", "Fade",

    # --- GUI Extensions ---
    "Toggle", "Slider",

    # --- Time System ---
    "Clock", "CountdownTimer",

    # --- Drawing ---
    "gradient_rect", "CameraShake", "DrawHelper", "DrawTextManager", "CrystalDraw", 

    # --- Misc ---
    "random_name", "DebugOverlay", "Camera", "Colors", "Color",
    "random_palette", "lerp", "SearchResult", "WebBrowse", "random_number", "random_pos", "random_bool", "random_choice_weighted", "difference",

    # --- 3D ---
    "CW3DShape", "CW3D",

    # --- ChatVPN ---
    "ChatVPN", "ChatVPNServer",

    # --- Message Bus ---
    "send_message", "view_message", "clear_messages",

    # === Fonts ===
    "Font",

    # --- App/Window ---
    "GameAppHelper",

    # --- System ---
    "System", "Watchdog",

    # --- Scores ---
    "Score",
]