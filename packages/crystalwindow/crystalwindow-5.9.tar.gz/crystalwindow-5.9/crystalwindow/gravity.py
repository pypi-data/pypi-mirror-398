class Gravity:
    def __init__(self, obj, force=0.6, terminal_velocity=18, bouncy=False, bounce_strength=0.7):
        """
        obj: Sprite (or object with x, y, width, height, vel_y)
        force: gravity per frame
        terminal_velocity: max falling speed
        bouncy: should object bounce on collision
        bounce_strength: fraction of vel_y to keep when bouncing
        """
        self.obj = obj

        # Ensure velocity exists
        if not hasattr(self.obj, "vel_y"):
            self.obj.vel_y = 0

        self.force = force
        self.terminal_velocity = terminal_velocity
        self.bouncy = bouncy
        self.bounce_strength = bounce_strength
        self.on_ground = False
        self.stretch_factor = 0  # optional squishy effect

        # Decide mode (rect or sprite)
        self.mode = "sprite" if hasattr(obj, "sprite") else "rect"

    # -----------------------
    # Rect getter
    # -----------------------
    def get_obj_rect(self):
        if self.mode == "sprite":
            s = self.obj.sprite
            return s.x, s.y, s.width, s.height
        else:
            return self.obj.x, self.obj.y, self.obj.width, self.obj.height

    # -----------------------
    # Rect setter
    # -----------------------
    def set_obj_rect(self, x, y):
        if self.mode == "sprite":
            self.obj.sprite.x = x
            self.obj.sprite.y = y
        else:
            self.obj.x = x
            self.obj.y = y

    # -----------------------
    # Update gravity
    # -----------------------
    def update(self, dt=1, platforms=[]):
        self.on_ground = False
        # Apply gravity (per frame, not dt scaled)
        self.obj.vel_y += self.force
        if self.obj.vel_y > self.terminal_velocity:
            self.obj.vel_y = self.terminal_velocity

        # Move
        x, y, w, h = self.get_obj_rect()
        y += self.obj.vel_y
        self.on_ground = False

        # Platform collisions
        for plat in platforms:
            plat_w = getattr(plat, "width", 32)
            plat_h = getattr(plat, "height", 32)

            if (x + w > plat.x and x < plat.x + plat_w and
                y + h >= plat.y and y < plat.y and
                self.obj.vel_y >= 0):

                # Land on top
                y = plat.y - h
                self.on_ground = True

                if self.bouncy:
                    self.obj.vel_y = -self.obj.vel_y * self.bounce_strength
                    self.stretch_factor = min(0.5, self.stretch_factor + 0.2)
                else:
                    self.obj.vel_y = 0
                    self.stretch_factor = 0

        # Slowly reset stretch
        if self.stretch_factor > 0:
            self.stretch_factor -= 0.05
            if self.stretch_factor < 0:
                self.stretch_factor = 0

        # Write back position
        self.set_obj_rect(x, y)
