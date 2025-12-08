#Importing libaries that will be needed
import pygame
import random
import time
import math

#Universal color of a pipe(Jordan)
Green = (0,200,0)
Black = (0,0,0)

#Kadins Colors
RED = (255, 0, 0)
LIGHT_GREEN = (0, 255, 0)
ORANGE = (255, 165, 0)
BLUE = (0, 0, 255)
PURPLE = (170, 0, 255)
PINK = (255, 105, 180)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

#Kadins Powerups
# -----------------------------------
# COIN POWER-UP COLORS
# -----------------------------------
coin_colors = {
    "red": RED,
    "green": LIGHT_GREEN,
    "orange": ORANGE,
    "blue": BLUE,
    "purple": PURPLE,
    "pink": PINK
}

# -----------------------------------
# SCORE SQUARES
# -----------------------------------
score_squares = {
    "+5": 5,
    "+10": 10,
    "+25": 25
}

'''
Jordan's Functions
'''
#The function that spawns the pipes getting their heights, widths, and gaps
def pipe_spawner(swidth, sheight, pwidth, pgap):
    pheight = random.randint(100, sheight - 250)

    bottom_rect = pygame.Rect(swidth, pheight + pgap, pwidth, sheight - (pheight + pgap))
    top_rect = pygame.Rect(swidth, 0, pwidth, pheight)

    bottom = {
        "rect": bottom_rect,
        "scored1": False,
        "scored2": False,
        "type": "bottom"
    }

    top = {
        "rect": top_rect,
        "type": "top"
    }

    return [bottom, top]


#This function creates the actual pipes to the screen
def pipe_creation(screen, pipes, color):
    for p in pipes:
        pygame.draw.rect(screen, Green, p["rect"])

#This function moves the pipes along the screen.
def pipe_movement(pipes, speed):
    new_pipes = []
    for pipe in pipes:
        pipe["rect"].centerx -= speed
        if pipe["rect"].right > 0:
            new_pipes.append(pipe)
    return new_pipes

'''
Combining Kadin's and Jordan's Collisions
'''
#This functions check for collision between bird or the border of the screen
def check_collision(bird, pipes, sheight,state):
    now = time.time()
    # End immunity after timer runs out
    if state["immunity"] and now >= state["immunity_end"]:
        state["immunity"] = False

    # Pipe collisions
    for p in pipes:
        if bird.colliderect(p["rect"]):
            if not state["immunity"]:
                state["lives"] -= 1
                if state["lives"] <= 0:
                    return False
                else:
                    # brief immunity after hit
                    state["immunity"] = True
                    state["immunity_end"] = now + 1
                    return True
    #Ground collision
    if bird.bottom >= sheight:
        state["lives"] = 0
        return False
    
    # Ceiling collision
    if bird.top <= 0:
        if not state["immunity"]:
            state["lives"] -= 1
            if state["lives"] <= 0:
                return False
            else:
                state["immunity"] = True
                state["immunity_end"] = now + 1
                return True

    return True

#This function, renders the score and prints it to the screen
def score(screen, font, score,lives):
    score_text = font.render(f"Score: {int(score)}   Lives: {lives}", True, (0, 0, 0))
    screen.blit(score_text, (10, 10))

def delete_all_pipes(screen,pipes):
    pipes.clear()

def box_spawner(screen,bwidth):
    sw, sh = screen.get_size()

    bheight = random.randint(100,150)
    y_pos = random.randint(0, sh - bheight)

    box = pygame.Rect(sw, y_pos, bwidth, bheight)

    # Random vertical direction: -1 (up) or +1 (down)
    y_velocity = random.choice([-3, 3])

    return [box, y_velocity]

def box_movement(box, y_velocity, speed, screen_height):
    # Move left
    box.x -= speed

    # Move vertically
    box.y += y_velocity

    # Bounce on top / bottom
    if box.top <= 0 or box.bottom >= screen_height:
        y_velocity *= -1

    return y_velocity

def box_creation(screen,boxes,color):
    for b in boxes:
        pygame.draw.rect(screen, Black, b)

def delete_all_boxes(screen,boxes):
    boxes.clear()

# Triangles
def triangle_spawner(screen, tsize):
    """
    Spawns a triangle at the right edge of the screen with random vertical position.
    Returns [triangle_points, x_velocity].
    """
    sw, sh = screen.get_size()

    # Random vertical position (ensure triangle fits on screen)
    y_pos = random.randint(0, sh - tsize)

    # Triangle pointing left, starting just off the right side
    # Three points: top, bottom, left
    top_point = (sw + tsize, y_pos)
    bottom_point = (sw + tsize, y_pos + tsize)
    left_point = (sw, y_pos + tsize // 2)

    points = [top_point, bottom_point, left_point]
 
    # Horizontal speed (moving left)
    x_velocity = -15

    return [points, x_velocity]

def triangle_movement(points, x_velocity, speed):
    """
    Moves triangle horizontally to the left.
    Returns updated x_velocity (kept for symmetry with box_movement).
    """
    # Move horizontally
    for i in range(len(points)):
        x, y = points[i]
        points[i] = (x - speed, y)

    return x_velocity

def triangle_creation(screen, triangles, color):
    """
    Draws all triangles in the list.
    triangles is a list of [points, x_velocity].
    """
    for tri in triangles:
        points, i = tri
        pygame.draw.polygon(screen, color, points)


def triangle_off_screen(points):
    """
    Returns True if the entire triangle is off the left side of the screen.
    """
    xs = [p[0] for p in points]
    return max(xs) < 0

def check_triangle_collision(bird, triangles):
    for tri in triangles:
        points, i = tri

        # Build a bounding rect from triangle points
        xs = [p[0] for p in points]
        ys = [p[1] for p in points]
        tri_rect = pygame.Rect(min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys))

        if bird.colliderect(tri_rect):
            return False
        
    return True

def delete_all_triangles(triangles):
    """
    Clears all triangles from the list.
    """
    triangles.clear()

'''
Kadin's Functions
'''
# -----------------------------------
# ITEM SPAWNING (COINS + SCORE SQUARES)
# -----------------------------------
def spawn_item(screen_width, screen_height):
    y = random.randint(60, screen_height - 60)

    # Weighted spawn:
    # 80% = coin power-ups
    # 20% = score squares
    if random.random() < 0.8:
        color = random.choice(list(coin_colors.keys()))
        rect = pygame.Rect(screen_width, y, 20, 20)
        return rect, color, time.time()
    else:
        kind = random.choice(list(score_squares.keys()))
        rect = pygame.Rect(screen_width, y, 30, 30)
        return rect, kind, time.time()


def move_items(items):
    updated = []
    for rect, color, born in items:
        rect.centerx -= 3
        if rect.right > 0:
            updated.append((rect, color, born))
    return updated


# -----------------------------------
# ITEM DRAWING
# -----------------------------------
def draw_item(screen, rect, color, born):
    # If this is a SCORE SQUARE
    if color in score_squares:
        pygame.draw.rect(screen, WHITE, rect)  # background
        pygame.draw.rect(screen, BLACK, rect, 2)  # border

        font = pygame.font.SysFont(None, 24)
        text = font.render(color, True, BLACK)
        screen.blit(
            text,
            (rect.centerx - text.get_width() // 2,
             rect.centery - text.get_height() // 2)
        )
        return

    # Otherwise draw a COIN with glow
    elapsed = time.time() - born
    pulse = 6 * abs(math.sin(elapsed * 3)) + 10

    glow = pygame.Surface((rect.width + 30, rect.height + 30), pygame.SRCALPHA)
    pygame.draw.circle(
        glow,
        (*coin_colors[color], 80),
        (rect.width // 2 + 15, rect.height // 2 + 15),
        int(pulse + 10)
    )
    screen.blit(glow, (rect.centerx - rect.width // 2 - 15,
                       rect.centery - rect.height // 2 - 15))

    pygame.draw.circle(screen, coin_colors[color], rect.center, 10)


# -----------------------------------
# ITEM COLLISIONS & EFFECTS
# -----------------------------------
def handle_item_collision(items, bird, state):
    updated = []
    now = time.time()

    for rect, color, born in items:

        if bird.colliderect(rect):

            # -------- SCORE SQUARES (+5, +10, +25) --------
            if color in score_squares:
                bonus = score_squares[color]
                state["score"] += bonus
                state["reward_popup"] = (f"+{bonus} POINTS!", now + 2)
                continue  # remove this item completely

            # -------- POWER-UP COINS --------
            if color == "red":
                state["lives"] += 2
                state["reward_popup"] = ("+2 LIVES!", now + 2)

            elif color == "green":
                state["pipe_shrink"] = True
                state["pipe_restore_time"] = now + 8
                state["pipe_width"] = state["base_pipe_width"] // 2
                state["pipe_gap"] = int(state["base_pipe_gap"] * 1.5)
                state["reward_popup"] = ("SMALL PIPES!", now + 2)

            elif color == "orange":
                state["immunity"] = True
                state["immunity_end"] = now + 8
                state["reward_popup"] = ("IMMUNITY!", now + 2)

            elif color == "blue":
                state["double_points"] = True
                state["double_end"] = now + 8
                state["reward_popup"] = ("DOUBLE POINTS!", now + 2)

            elif color == "purple":
                state["bird_shrink"] = True
                state["shrink_end"] = now + 8
                state["reward_popup"] = ("SMALL BIRD!", now + 2)

            elif color == "pink":
                state["pipe_slow"] = True
                state["slow_end"] = now + 8
                state["reward_popup"] = ("SLOW PIPES!", now + 2)

            # Normal coin gives base 5 points
            state["score"] += 5

        else:
            updated.append((rect, color, born))

    return updated


# -----------------------------------
# RESTORE PIPE MODIFICATIONS
# -----------------------------------
def restore_pipes(state):
    state["pipe_width"] = state["base_pipe_width"]
    state["pipe_gap"] = state["base_pipe_gap"]
    state["pipe_shrink"] = False

'''
Luke's Functions
'''
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
