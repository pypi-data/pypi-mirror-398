from crystalwindow import *

win = Window(800, 600, "GameWindow")
PlayerCube = Sprite.rect((400, 300), 50, 50, color=(0,100,254))

def gamerun(win):
    PlayerCube.draw(win)

    win.draw_text("This is a crystalwindow test. (you can leave using ESC)", size=21, color=(255,255,255), pos=(25,25))

    if win.key_pressed("keyw"):
        PlayerCube.y -= 10
    if win.key_pressed("keys"):
        PlayerCube.y += 10
    if win.key_pressed("keya"):
        PlayerCube.x -= 10
    if win.key_pressed("keyd"):
        PlayerCube.x += 10

    if win.key_pressed("escape"):
        win.quit()    

win.run(gamerun)
win.quit()
