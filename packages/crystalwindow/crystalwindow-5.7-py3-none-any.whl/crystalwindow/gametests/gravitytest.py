import sys
sys.path.insert(0, r"c:/Users/USUARIO/Desktop/crystalwindow")

from crystalwindow import *
import time

# --- window ---
win = Window(800, 600, "Debug Panel Test")

# --- player ---
player = Player(name="Player", pos=(0, 0), size=(32, 32), speed=4,hp=100)
enemy = Enemy((100, 100), 50, 50, 10, 0, color=(255, 0, 0))

# --- platform ---
class Platform:
    def __init__(self, x, y, w, h, color=(100,200,100)):
        self.x = x
        self.y = y
        self.width = w
        self.height = h
        self.color = color
    def draw(self, win):
        win.draw_rect(self.color, (self.x, self.y, self.width, self.height))

platform = Platform(0, 500, 800, 50)

# --- gravity ---
player.gravity = Gravity(player, force=1, bouncy=True, bounce_strength=0.7)

# ==========================================
#        DEBUG PANEL SYSTEM
# ==========================================
gui = GUIManager()

panel_open = False
fly_mode = False

# panel background (Sprite.rect)
debug_panel = Sprite.rect((20, 20), 220, 140, color=(0,0,0))
debug_panel.alpha = 160  # make it transparent

# BUTTON CALLBACKS
def toggle_fly():
    global fly_mode
    fly_mode = not fly_mode
    fly_button.text = f"Fly: {'ON' if fly_mode else 'OFF'}"

# create buttons
fly_button = Button((35, 60), (180, 40),
                    text="Fly: OFF",
                    color=(150,150,150),
                    hover_color=(200,200,200),
)

gui.add(fly_button)

cooldown = 0

# ==========================================
#            MAIN UPDATE
# ==========================================
def update(win):
    global panel_open, fly_mode, cooldown

    win.fill((20,20,50))

    # PANEL TOGGLE KEY
    if win.key_pressed("f1") and time.time() > cooldown:
        panel_open = not panel_open
        cooldown = time.time() + 0.25

    if win.key_pressed("f") and not panel_open and time.time() > cooldown:
        fly_mode = not fly_mode
        cooldown = time.time() + 0.2

    # -------------------------------
    #         GAME LOGIC
    # -------------------------------
    if fly_mode:
        # disable gravity
        player.gravity.vel_y = 0

        # free fly movement
        if win.key_pressed("keyw"): player.y -= 6
        if win.key_pressed("keys"): player.y += 6
        if win.key_pressed("keya"): player.x -= 6
        if win.key_pressed("keyd"): player.x += 6
    else:
        # normal gravity
        player.gravity.update(1/60, [platform])

        # jumping + movement
        if win.key_pressed("keyw"): player.vel_y = -6
        if win.key_pressed("keya"): player.x -= 10
        if win.key_pressed("keyd"): player.x += 10

    # draw world
    player.draw(win)
    platform.draw(win)
    enemy.draw(win)

    enemy.update(60)

    if enemy.collide_with(player):
        player.hp -= enemy.dmg
    if player.hp == 0:
        player.redraw(win, new_pos=(0,0))   
        player.hp = 100

    win.draw_text(f"CurrentHP: {player.hp}", font="Arial", size=16, color=(255, 255, 255))
    # -------------------------------
    #      SHOW DEBUG PANEL
    # -------------------------------
    if panel_open:
        debug_panel.draw(win)   # panel bg
        gui.draw(win)           # buttons
        gui.update(win)         # button callbacks


win.run(update)
win.quit()
