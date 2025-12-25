def check_collision(sprite, tiles):
    for t in tiles:
        if sprite.rect.colliderect(t.rect):
            return True
    return False

def resolve_collision(sprite, tiles, dy):
    sprite.rect.y += dy
    collided = [t for t in tiles if sprite.rect.colliderect(t.rect)]
    for t in collided:
        if dy > 0:
            sprite.rect.bottom = t.rect.top
        elif dy < 0:
            sprite.rect.top = t.rect.bottom
    sprite.y = sprite.rect.y
