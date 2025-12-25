import sys
sys.path.insert(0, r"c:/Users/USUARIO/Desktop/crystalwindow")

from crystalwindow import *

win = Window(800, 600, "Debug Panel Test")

# THIS WILL FAIL TO LOAD → fallback → checkerboard
game = load_image("SAKJDNSAOJDOSAJND;ONJSIOAJVO")

player = Sprite.image(game, (100, 100))

def gameruns(win):
    player.draw(win)

win.run()
win.quit()
