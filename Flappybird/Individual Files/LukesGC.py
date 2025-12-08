import pygame
import random

# Universal pipe color
Green = (0, 200, 0)

# -------------------------
# Pipes
# -------------------------

# Spawns a pair of pipes with a gap between them
def pipe_spawner(swidth, sheight, pwidth, pgap):
    pheight = random.randint(100, sheight - 250)
    bottom = pygame.Rect(
        swidth,
        pheight + pgap,
        pwidth,
        sheight - (pheight + pgap)
    )
    top = pygame.Rect(
        swidth,
        0,
        pwidth,
        pheight
    )
    return [bottom, top]

# Draws all pipes
def pipe_creation(screen, pipes, color=None):
    # color kept for compatibility; we always use Green
    for p in pipes:
        pygame.draw.rect(screen, Green, p)

# Moves pipes left and removes off-screen ones
def pipe_movement(pipes, speed):
    for p in pipes:
        p.centerx -= speed
    return [p for p in pipes if p.right > 0]

# -------------------------
# Collision
# -------------------------

# Returns False if game over, True otherwise
def check_collision(bird, pipes, sheight):
    # Hit a pipe?
    for p in pipes:
        if bird.colliderect(p):
            return False

    # Hit top or bottom of the screen?
    if bird.top <= 0 or bird.bottom >= sheight:
        return False

    return True

# -------------------------
# Score
# -------------------------

def score(screen, font, score_value):
    score_text = font.render(f"Score: {int(score_value)}", True, (0, 0, 0))
    screen.blit(score_text, (10, 10))

# -------------------------
# Bad items (negative power-ups)
# -------------------------

# All possible bad item types (must match what your main file expects)
BAD_KINDS = ("invert", "flash", "speedup", "slow")

# Create a new bad item on the right edge, at a random height
# Returns (rect, kind)
def spawn_bad_item(swidth, sheight, size=25):
    y_pos = random.randint(100, sheight - 100)
    rect = pygame.Rect(swidth, y_pos, size, size)
    kind = random.choice(BAD_KINDS)
    return rect, kind

# Move all bad items left and keep only on-screen ones
# bad_items is a list of (rect, kind)
def move_bad_items(bad_items, speed):
    updated = []
    for rect, kind in bad_items:
        rect.x -= speed
        if rect.right > 0:
            updated.append((rect, kind))
    return updated

# Draw bad items as colored squares.
# color_map should be a dict: { "invert": color, "flash": color, ... }
def draw_bad_items(screen, bad_items, color_map):
    for rect, kind in bad_items:
        color = color_map.get(kind, (0, 0, 0))
        pygame.draw.rect(screen, color, rect)
