import sys
sys.path.insert(0, r"c:/Users/USUARIO/Desktop/crystalwindow")

from crystalwindow import *


# --- Window setup ---
win = Window(800, 600, "CrystalWindowLib Mega Sandbox")

# --- GUI ---
gui = GUIManager()
toggle1 = Toggle((50, 50, 100, 40), value=False)
slider1 = Slider((50, 120, 200, 30), min_val=0, max_val=100, value=50)

btn1 = Button(rect=(50, 200, 150, 50), text="Click Me!", color=random_color(),
              hover_color=random_color(), callback=lambda: print("Button clicked!"))
lbl1 = Label((250, 50), "Hello GUI!", color=random_color(), size=24)

gui.add(toggle1)
gui.add(slider1)
gui.add(btn1)
gui.add(lbl1)

# --- Debug Overlay ---
debug = DebugOverlay()

# --- Camera Shake ---
shake = CameraShake(intensity=20)

# --- Main loop ---
def update(win):
    gui.update(win)
    gui.draw(win)

    # --- draw text examples ---
    win.draw_text("Normal Text", pos=(400, 50), size=18, color=random_color())
    win.draw_text("Bold Text", pos=(400, 80), size=20, color=random_color(), bold=True)
    win.draw_text("Italic Text", pos=(400, 110), size=20, color=random_color(), italic=True)
    win.draw_text("Bold + Italic", pos=(400, 140), size=22, color=random_color(), bold=True, italic=True)
    
    # --- draw toggle/slider values ---
    win.draw_text(f"Toggle: {toggle1.value}", pos=(50, 90), size=18)
    win.draw_text(f"Slider: {int(slider1.value)}", pos=(50, 160), size=18)
    
    # --- draw gradient ---
    gradient_rect(win, (50, 300, 200, 100), (255,0,0), (0,0,255))
    
    # --- screen shake example (move a rectangle with shake) ---
    shake.update()
    x_off, y_off = shake.offset
    win.draw_rect((0,255,0), (500+x_off, 300+y_off, 100, 50))
    
    # --- draw random name + color ---
    win.draw_text(f"Random Name: {random_name()}", pos=(50, 420), size=20, color=random_color())
    

win.run(update)
win.quit()
