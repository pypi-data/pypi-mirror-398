# CRYSTALWINDOW!!!

A tiny but mighty Tkinter framework that gives u a full window system, GUI magic, physics, and file power — all packed into one clean lil module. Made by Crystal.

No setup pain. No folder chaos.
Just import it. Boom. Instant game window. 🎮

# Quick Start
pip install crystalwindow

Then make a new .py file:

    from crystalwindow import Window  # imports everything from crystalwindow (in this case its Window)

    win = Window(800, 600, "Crystal Demo")  # setup: Window(width, height, name, icon=MyIcon.ico)
    win.run()  # runs the window loop
    win.quit()   # closes it (for RAM n CPU)

Run it. And boom, instant working window.
Yes, THAT easy.

# Easy CrystalWindow Window + GUI + Text File:
    from crystalwindow import *

    win = Window(800, 600, "CrystalWindowLib Mega Sandbox")

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

    # --- Main Loop ---
    def update(win):
        gui.update(win)
        gui.draw(win)

        # --- draw text examples ---
        win.draw_text_later("Normal Text", pos=(400, 50), size=18, color=random_color())
        win.draw_text_later("Bold Text", pos=(400, 80), size=20, color=random_color(), bold=True)
        win.draw_text_later("Italic Text", pos=(400, 110), size=20, color=random_color(), italic=True)
        win.draw_text_later("Bold + Italic", pos=(400, 140), size=22, color=random_color(), bold=True, italic=True)

        # --- draw toggle/slider values ---
        win.draw_text_later(f"Toggle: {toggle1.value}", pos=(50, 90), size=18)
        win.draw_text_later(f"Slider: {int(slider1.value)}", pos=(50, 160), size=18)

        # --- draw gradient ---
        gradient_rect(win, (50, 300, 200, 100), (255,0,0), (0,0,255))

        # --- screen shake example ---
        shake.update()
        x_off, y_off = shake.offset
        win.draw_rect((0,255,0), (500+x_off, 300+y_off, 100, 50))

        # --- draw random name + color ---
        win.draw_text_later(f"Random Name: {random_name()}", pos=(50, 420), size=20, color=random_color())

        # --- debug overlay ---
        debug.draw(win, fps=int(win.clock.get_fps()))

    win.run(update)
    win.quit()

And now thats how you use it!

# Whats Inside

Built-in window manager  
Built-in GUI (buttons, sliders, toggles, labels)  
Built-in gravity + physics engine  
TileMap system (place & save blocks!)  
Image loader (with default base64 logo)  
Safe startup (works inside PyInstaller)  
Mathematics Handler  
Works offline  
Minimal syntax  
Full debug overlay  

# Window System
    from crystalwindow import *

    win = Window(800, 600, "My Game", icon="MyIcon.png")

    def loop(win):
        win.fill((10, 10, 30))
        # draw or update stuff here

    win.run(loop)
    win.quit()

# Features
* handles events  
* tracks keys + mouse  
* supports fullscreen  
* safe to close anytime  

# Player Example
    player = Player(100, 100)

    def loop(win):
        player.update(win.keys)
        player.draw(win.screen)

    move(dx, dy) -> moves player  
    take_damage(x) -> takes damage  
    heal(x) -> heals  
    draw(surface) -> renders sprite  

# TileMap
    tilemap = TileMap(32)
    tilemap.add_tile(5, 5, "grass")
    tilemap.save("level.json")

    add_tile(x, y, type)  
    remove_tile(x, y)  
    draw(surface)  
    save(file) / load(file)  

# GUI System
    btn = Button(20, 20, 120, 40, "Click Me!", lambda: print("yo"))
    gui = GUIManager()
    gui.add(btn)

Use built-in stuff like:
    Button(x, y, w, h, text, onclick)  
    Label(x, y, text)  
    Toggle(x, y, w, h, text, default=False)  
    Slider(x, y, w, min, max, default)  

# Gravity
    g = Gravity(0.5)
    g.update(player)

# FileHelper
    save_json("data.json", {"coins": 99})
    data = load_json("data.json")

Also supports:
    save_pickle / load_pickle  
    FileDialog("save")  # tkinter popup  

# DrawHelper
    DrawHelper.text(win.screen, "Hello!", (10,10), (255,255,255), 24)
    DrawHelper.rect(win.screen, (100,0,200), (50,50,100,60))

# Debug Tools
    debug = DebugOverlay()
    debug.toggle()  # show/hide FPS
    debug.draw(win.screen, {"hp": 100, "fps": win.clock.get_fps()})

# Mathematics
    math = Mathematics()
    math.add(num1, num2)
    math.subtract(num1, num2)
    math.multiply(num1, num2)
    math.divide(num1, num2)

# Example Game
    from crystalwindow import *

    win = Window(800, 600, "My Cool Game")
    player = Player(100, 100)
    gravity = Gravity()

    def update(win):
        win.fill((25, 25, 40))
        player.update(win.keys)
        gravity.update(player)
        player.draw(win.screen)

    win.run(update)
    win.quit()

# Default Logo
There is a lil encoded PNG inside the file called DEFAULT_LOGO_BASE64.  
Its used when no icon is given. Set ur own like:

    Window(800, 600, "My Window", icon="MyIcon.png")

# Example Integration
    from crystalwindow import Window

    win = Window(800, 600, "My Window", icon="MyIcon.png")

    while win.running:
        win.check_events()
        win.fill((10, 10, 20))
        win.run()
        win.quit()

# Credits
Made by: CrystalBallyHereXD  
Framework: CrystalWindow  
Powered by: Tkinter and Python  
License: Free to use, modify, and vibe with it!
