from crystalwindow import *

# --- setup window ---
win = Window(800, 600, "CrystalWindow Sandbox")

# --- setup debug overlay ---
debug = DebugOverlay()
draw = DrawHelper()
draw.rect(win, 100, 100, 50, 60, (255,0,0)).circle(win, 300, 200, 40, (0,255,0))


# --- player setup ---
player = Player((100, 400), speed=220)


# --- gravity system ---
gravity = Gravity(player, force=1.5)

# --- GUI setup ---

lbl = Label((20, 70), "CrystalWindow Sandbox Ready 🧠")

gui = GUIManager()
gui.add(lbl)

# --- rect testing helper ---
draw = DrawHelper()
draw.add_rect((300, 500, 200, 50), (50, 200, 255))

# --- text system ---
text_draw = DrawTextManager()
text_draw.write("Hello Crystal Sandbox!", (250, 50), (255, 255, 255))

# --- main loop ---
running = True
while running:
    player.update()
    gravity.apply()
    win.fill((20, 20, 30))

    draw.render()
    player.draw(win)
    gui.draw(win)
    text_draw.render()

    win.flip()

win.run()
win.quit()
