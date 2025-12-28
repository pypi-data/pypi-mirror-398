class Animation:
    def __init__(self, frames, speed=0.1):
        self.frames = frames
        self.speed = speed
        self.current = 0
        self.timer = 0

    def update(self, dt):
        self.timer += dt
        if self.timer >= self.speed:
            self.timer = 0
            self.current = (self.current + 1) % len(self.frames)

    def get_frame(self):
        return self.frames[self.current]
