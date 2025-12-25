import random
from tkinter import PhotoImage
from .assets import generate_missing_texture

try:
    from PIL import Image, ImageTk
except ImportError:
    Image = None
    ImageTk = None


class Sprite:
    def __init__(self, pos, size=None, image=None, color=(255, 0, 0)):
        """
        pos: (x, y)
        size: (w, h)
        image: PhotoImage or PIL ImageTk.PhotoImage
        """
        self.pos = pos
        self.x, self.y = pos
        self.image = image
        self.color = color

        # drawn object id
        self.canvas_id = None

        # sprite states
        self.visible = True      # can draw
        self.alive = True        # can collide / move / draw

        # save original spawn
        self.spawn_point = pos

        # width / height
        if image is not None:
            try:
                self.width = image.width()
                self.height = image.height()
            except Exception:
                try:
                    self.width = image.width
                    self.height = image.height
                except Exception:
                    raise ValueError("Sprite image has no size info")

        elif size is not None:
            self.width, self.height = size
        else:
            raise ValueError("Sprite needs 'size' or 'image'")

        # optional velocity
        self.vel_x = 0
        self.vel_y = 0

        self._last_win = None


    # === CLASS METHODS ===
    @classmethod
    def image(cls, img, pos):
        """Create sprite from image OR fallback dict"""
        if isinstance(img, dict) and img.get("fallback"):
            w, h = img["size"]
            missing = generate_missing_texture((w, h))
            return cls(pos, image=missing, size=(w, h))
        # normal image
        return cls(pos, image=img)


    @classmethod
    def rect(cls, pos, w, h, color=(255, 0, 0)):
        """Create sprite using a simple rectangle"""
        return cls(pos, size=(w, h), color=color)


    # === MOVE / DRAW ===
    def draw(self, win, cam=None):
        """Draw sprite onto Tk canvas. Skips when not visible/alive."""
        if not self.alive or not self.visible:
            return

        self._last_win = win

        # delete previous drawing
        if self.canvas_id is not None:
            try:
                win.canvas.delete(self.canvas_id)
            except:
                pass

        # camera offset
        if cam:
            draw_x, draw_y = cam.apply(self)
        else:
            draw_x, draw_y = self.x, self.y

        # draw img or rect
        if self.image:
            self.canvas_id = win.canvas.create_image(
                draw_x, draw_y, anchor="nw", image=self.image
            )
        else:
            # draw_rect MUST return the canvas ID
            self.canvas_id = win.draw_rect(
                self.color, (draw_x, draw_y, self.width, self.height)
            )


    def move(self, dx, dy):
        if not self.alive:
            return
        self.x += dx
        self.y += dy
        self.pos = (self.x, self.y)


    def apply_velocity(self, dt=1):
        if not self.alive:
            return
        self.x += self.vel_x * dt
        self.y += self.vel_y * dt
        self.pos = (self.x, self.y)


    # === COLLISION ===
    def colliderect(self, other):
        if not self.alive or not other.alive:
            return False

        return (
            self.x < other.x + getattr(other, "width", 0)
            and self.x + getattr(self, "width", 0) > other.x
            and self.y < other.y + getattr(other, "height", 0)
            and self.y + getattr(self, "height", 0) > other.y
        )


    # === RESPAWN / REDRAW ===
    def redraw(self, win, new_pos=None, flash=True):
        if not self.alive:
            return

        self._last_win = win

        # save original spawn ONCE
        if not hasattr(self, "spawn_pos"):
            self.spawn_pos = (self.x, self.y)

        # delete old draw
        if self.canvas_id is not None:
            try:
                win.canvas.delete(self.canvas_id)
            except:
                pass
            self.canvas_id = None

        # teleport
        if new_pos is not None:
            self.x, self.y = new_pos
        else:
            self.x, self.y = self.spawn_pos

        self.pos = (self.x, self.y)

        # flash effect
        if flash and self.image is None:
            og_color = self.color
            self.color = (255, 255, 255)
            self.draw(win)
            win.canvas.update()
            self.color = og_color

        self.draw(win)


    # === IMAGE SWITCH ===
    def set_image(self, img):
        self.image = img

        if img is not None:
            try:
                self.width = img.width()
                self.height = img.height()
            except Exception:
                try:
                    self.width = img.width
                    self.height = img.height
                except:
                    pass


    # === FULL REMOVE ===
    def remove(self):
        """
        Removes from screen AND disables collisions/movement/drawing.
        Fully out of the game world.
        """
        self.visible = False
        self.alive = False

        # erase from canvas
        if self.canvas_id is not None:
            try:
                win = self._last_win
                win.canvas.delete(self.canvas_id)
            except:
                pass

        self.canvas_id = None
        self._last_win = None

class CollisionHandler:
    def __init__(self):
        """Initialize the collision handler with an empty list of sprites."""
        self.sprites = []

    def add(self, sprite):
        """Add a sprite to the collision handler."""
        self.sprites.append(sprite)

    def check_collisions(self):
        """Check for collisions between all sprites in the handler."""
        for i in range(len(self.sprites)):
            for j in range(i + 1, len(self.sprites)):
                sprite_a = self.sprites[i]
                sprite_b = self.sprites[j]

                if sprite_a.colliderect(sprite_b):
                    self.handle_collision(sprite_a, sprite_b)

    def handle_collision(self, sprite_a, sprite_b):
        """Handle the collision between two sprites."""
        
        # Prevent "noclip": Adjust positions or velocities to prevent overlap

        # Stop both sprites' movement upon collision
        if sprite_a.vel_x != 0 and sprite_b.vel_x != 0:
            sprite_a.vel_x = 0
            sprite_b.vel_x = 0
        
        if sprite_a.vel_y != 0 and sprite_b.vel_y != 0:
            sprite_a.vel_y = 0
            sprite_b.vel_y = 0

        # Prevent overlap by adjusting their positions after a collision
        if sprite_a.x < sprite_b.x:
            sprite_a.x = sprite_b.x - sprite_a.width
        else:
            sprite_b.x = sprite_a.x - sprite_b.width

        if sprite_a.y < sprite_b.y:
            sprite_a.y = sprite_b.y - sprite_a.height
        else:
            sprite_b.y = sprite_a.y - sprite_b.height

        # You can add more sophisticated handling (e.g., bounce, adjust based on velocity)
        # For now, this simple solution ensures no overlap and stops movement
