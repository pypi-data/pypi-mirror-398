import math, re
from .sprites import Sprite
from .assets import load_folder_images, load_image
from .animation import Animation


# ============================================================
#   PLAYER / ENEMY WITH HP SECURITY + COOLDOWN + RESPAWN
# ============================================================

class Player(Sprite):
    def __init__(self, name="Player", pos=(0, 0), size=(32, 32), speed=4, hp=100):
        self.name = name
        self.hp = hp
        self.max_hp = hp     # allows 0–100 or even 0–500
        self.speed = speed

        # frames
        self.animations = {}
        self.current_anim = None
        self.flip_x = False

        # death / respawn flags
        self.dead = False

        super().__init__(pos, size=size, image=None)

    # ----------------------------------------------------
    # BASIC DAMAGE HANDLING
    # ----------------------------------------------------
    def take_damage(self, dmg):
        if self.dead:
            return

        self.hp -= dmg
        if self.hp <= 0:
            self.hp = 0
            self.dead = True

    # ----------------------------------------------------
    # RESPAWN (normal redraw logic kept)
    # ----------------------------------------------------
    def respawn(self, win):
        """Manual respawn call if coder wants it."""
        self.hp = self.max_hp
        self.dead = False
        self.redraw(win)

    # ----------------------------------------------------
    # LOAD ANIMATION
    # ----------------------------------------------------
    def load_anim(self, key, folder, loop=True):
        imgs = self._load_sorted(folder)
        anim = Animation(imgs)
        anim.loop = loop
        self.animations[key] = anim

        if self.current_anim is None:
            self.current_anim = anim

    # ----------------------------------------------------
    # UPDATE (movement + anim)
    # ----------------------------------------------------
    def update(self, dt, win):
        if self.dead:
            # still draw corpse frame
            self.draw(win)
            return

        moving = False
        spd = self.speed * dt * 60

        # movement
        if win.key_pressed("left"):
            self.x -= spd
            self.flip_x = True
            moving = True

        if win.key_pressed("right"):
            self.x += spd
            self.flip_x = False
            moving = True

        if win.key_pressed("up"):
            self.y -= spd
            moving = True

        if win.key_pressed("down"):
            self.y += spd
            moving = True

        self.pos = (self.x, self.y)

        # anim switching
        if moving and "run" in self.animations:
            self.current_anim = self.animations["run"]
        elif not moving and "idle" in self.animations:
            self.current_anim = self.animations["idle"]

        # apply anim frame
        if self.current_anim:
            self.current_anim.update(dt)
            frame = self.current_anim.get_frame()
            self.set_image(frame)

        # final draw
        self.draw(win)

    # ----------------------------------------------------
    # FOLDER LOADING (unchanged)
    # ----------------------------------------------------
    def _load_sorted(self, folder):
        imgs_dict = load_folder_images(folder)
        return self._sort_images(imgs_dict)

    @staticmethod
    def _sort_images(imgs_dict):
        def extract_num(f):
            m = re.search(r"(\d+)", f)
            return int(m.group(1)) if m else 0

        items = [(name, img) for name, img in imgs_dict.items() if not isinstance(img, dict)]
        sorted_imgs = [img for name, img in sorted(items, key=lambda x: extract_num(x[0]))]
        return sorted_imgs


# ============================================================
# BLOCK (same)
# ============================================================
class Block(Sprite):
    def __init__(self, x, y, w, h, color=None, texture=None):
        self.x = x
        self.y = y
        self.w, self.h = w, h
        self.color = color

        if texture:
            img = load_image(texture)
            super().__init__((x, y), size=(w, h), image=img)
        else:
            super().__init__((x, y), size=(w, h), color=color or (150,150,150))

    def draw(self, win):
        win.draw_rect(self.color, (self.x, self.y, self.w, self.h))

    def collide_with(self, other):
        return self.colliderect(other)


# ============================================================
# ENEMY WITH DAMAGE COOLDOWN
# ============================================================
class Enemy(Sprite):
    def __init__(self, pos, w, h, dmg=10, speed=2, color=(200,50,50), texture=None, cooldown_max=5):
        self.dmg = dmg
        self.speed = speed

        # cooldown system
        self.cooldown = 0
        self.cooldown_max = cooldown_max

        if texture:
            super().__init__(pos, size=(w, h), image=load_image(texture))
        else:
            super().__init__(pos, size=(w, h), color=color)

    # enemy tick
    def update(self, dt):
        if self.cooldown > 0:
            self.cooldown -= dt * 60

    def collide_with(self, other):
        return self.colliderect(other)

    # enemy tries to damage
    def hit_player(self, player):
        if self.cooldown <= 0:
            player.take_damage(self.dmg)
            self.cooldown = self.cooldown_max

    # the X and Y is an check like if you want the enemy to chase the player horizontally or vertaically or both like chase_player(player, x=True, y=False) so it chases the player only thru horizontal
    def chase_player(self, obj, mode = "xy"):
        if mode == "x" or mode == "xy":
            if obj.x < self.x:
                self.x -= self.speed
            elif obj.x > self.x:
                self.x += self.speed

        if mode == "y" or mode == "xy":
            if obj.y < self.y:
                self.y -= self.speed
            elif obj.y > self.y:
                self.y += self.speed

        self.pos = (self.x, self.y)