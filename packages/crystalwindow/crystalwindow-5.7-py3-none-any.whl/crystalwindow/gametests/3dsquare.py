from crystalwindow import Window, CW3DShape, Clock

win = Window(800, 600, "CrystalWindow 3D Wavy Background")
clock = Clock()
cw3d = CW3DShape(win)
cw3d.add_cube(size=1.3, color="cyan")

# brightness wave vars
bright = 20
dir = 2  # 1 = going up, -1 = going down

def update(dt):
    global bright, dir

    # === spin cube ===
    cw3d.spin(0.03, 0.04)

    # === smooth brightness wave ===
    bright += dir * 1  # speed of wave
    if bright >= 50:  # top cap
        dir = -1
    elif bright <= 20:  # bottom cap
        dir = 1

    bg_color = (bright, bright, 50)
    win.fill(bg_color)

    # === draw cube ===
    cw3d.draw()

    # === lil debug text ===
    win.draw_text(f"BG Bright: {bright}", (10, 10), color=(255,255,255))
    clock.tick(60)

win.run(update)
win.quit()
