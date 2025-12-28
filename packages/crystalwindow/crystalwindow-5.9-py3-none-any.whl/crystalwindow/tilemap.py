from .sprites import Sprite

class TileMap:
    def __init__(self, tile_size=32):
        self.tile_size = tile_size
        self.tiles = []  # list of Sprite

    def add_tile(self, image, x, y):
        """Add a tile snapped to grid."""
        gx = x // self.tile_size * self.tile_size
        gy = y // self.tile_size * self.tile_size
        tile = Sprite((gx, gy), (self.tile_size, self.tile_size), image=image)
        self.tiles.append(tile)
        return tile

    def remove_tile_at(self, x, y):
        """Remove a tile that sits on this grid cell."""
        gx = x // self.tile_size * self.tile_size
        gy = y // self.tile_size * self.tile_size
        for t in self.tiles:
            if t.pos[0] == gx and t.pos[1] == gy:
                self.tiles.remove(t)
                return True
        return False

    def get_tile_at(self, x, y):
        """Return tile located at the grid coords."""
        gx = x // self.tile_size * self.tile_size
        gy = y // self.tile_size * self.tile_size
        for t in self.tiles:
            if t.pos[0] == gx and t.pos[1] == gy:
                return t
        return None

    def to_data(self):
        """Convert to serializable list for saving."""
        return [
            {
                "x": t.pos[0],
                "y": t.pos[1],
                "image_id": t.image_id if hasattr(t, "image_id") else None
            }
            for t in self.tiles
        ]

    def load_data(self, data, image_loader):
        """
        Load tiles from list.
        image_loader(id) → returns the image object used by Sprite.
        """
        self.tiles = []
        for d in data:
            img = image_loader(d["image_id"])
            tile = Sprite((d["x"], d["y"]),
                          (self.tile_size, self.tile_size),
                          image=img)
            if img is not None:
                tile.image_id = d["image_id"]
            self.tiles.append(tile)

    def draw(self, win):
        """Draw all tiles."""
        for t in self.tiles:
            win.draw_sprite(t)
class Grid:
    def __init__(self, win, cell_size=(16, 16)):
        self.win = win
        self.cell_w, self.cell_h = cell_size
        self.update_size()

    def update_size(self):
        self.w, self.h = self.win.size

        self.cols = self.w // self.cell_w
        self.rows = self.h // self.cell_h
        self.cells = [(cx, cy) for cy in range(self.rows) for cx in range(self.cols)]

    # MAKES GRID WORK LIKE gameg(x, y)
    def __call__(self, x, y):
        """Return cell index for given pixel pos."""
        return x // self.cell_w, y // self.cell_h

    def snap(self, x, y):
        gx = x // self.cell_w * self.cell_w
        gy = y // self.cell_h * self.cell_h
        return gx, gy

    def get_cell(self, x, y):
        return x // self.cell_w, y // self.cell_h

    def cell_to_px(self, cx, cy):
        return cx * self.cell_w, cy * self.cell_h

    def draw(self, color=(200, 200, 200)):
        self.update_size()

        # vertical
        for x in range(0, self.w, self.cell_w):
            self.win.draw_line((x, 0), (x, self.h), color)

        # horizontal
        for y in range(0, self.h, self.cell_h):
            self.win.draw_line((0, y), (self.w, y), color)
