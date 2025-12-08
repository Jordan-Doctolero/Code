#Importing libaries that will be needed
import pygame
import random

#Universal color of a pipe
Green = (0,200,0)
Black = (0,0,0)

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

#This functions check for collision between bird or the border of the screen
def check_collision(bird, pipes, sheight):
    for pipe in pipes:
        if bird.colliderect(pipe["rect"]):
            return False
    if bird.top <= 0 or bird.bottom >= sheight:
        return False
    return True

#This function, renders the score and prints it to the screen
def score(screen, font, score):
    score_text = font.render(f"Score: {int(score)}", True, (0, 0, 0))
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

