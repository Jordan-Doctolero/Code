import pygame
import sys
import random
from LukesGC import (
    pipe_creation,
    pipe_spawner,
    pipe_movement,
    check_collision,
    score, 
    spawn_bad_item,
    move_bad_items,
    draw_bad_items,
)

def FlappyBirdCore():
    # Init Pygame and mixer
    pygame.init()
    pygame.mixer.init()

    # Screen settings
    Width, Height = 400, 600
    screen = pygame.display.set_mode((Width, Height))
    pygame.display.set_caption("Flappy Bird")

    # Colors
    White  = (255, 255, 255)
    Blue   = (135, 206, 235)
    Green  = (0, 200, 0)
    Purple = (160, 0, 160)      # invert controls
    Yellow = (255, 255, 0)      # flash bomb
    Red    = (255, 80, 80)      # speed up
    DarkBlue = (80, 80, 255)    # slow motion

    BAD_COLORS = {
        "invert": Purple,
        "flash": Yellow,
        "speedup": Red,
        "slow": DarkBlue
    }

    # Misc
    Bird = pygame.image.load("THEBIRDY.png").convert_alpha()
    Bird = pygame.transform.scale(Bird, (50, 40))
    bird_rect = Bird.get_rect(center=(100, Height // 2))

    # Game variables
    running = True
    gravity = 0.7
    bird_movement = 0
    Scoring_Number = 0

    # Pipe settings
    base_pipe_speed = 3
    pipe_speed = base_pipe_speed
    pipe_width = 60
    pipe_gap = 150
    pipes = []

    # BAD EFFECTS
    bad_items = []  # list of (rect, kind)

    # invert controls
    inverted_controls = False
    invert_end_time = 0

    # flash bomb
    flash_active = False
    flash_end_time = 0

    # speed up / slow motion
    speed_effect = None         # "speedup", "slow", or None
    speed_effect_end_time = 0

    # Events
    Spawnpipe = pygame.USEREVENT + 1
    SpawnBad = pygame.USEREVENT + 2

    pygame.time.set_timer(Spawnpipe, 1200)
    pygame.time.set_timer(SpawnBad, 4000)  # spawn a bad item every 4 seconds

    font = pygame.font.SysFont(None, 40)
    clock = pygame.time.Clock()

    while True:
        current_time = pygame.time.get_ticks()

        # ======== UPDATE TIMERS FOR EFFECTS ========
        if inverted_controls and current_time > invert_end_time:
            inverted_controls = False

        if flash_active and current_time > flash_end_time:
            flash_active = False

        if speed_effect is not None and current_time > speed_effect_end_time:
            # restore normal pipe speed
            speed_effect = None
            pipe_speed = base_pipe_speed

        # ======== HANDLE EVENTS ========
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and running:
                    # BAD EFFECT: invert jump when under bad effect
                    if inverted_controls:
                        bird_movement = 8    # SPACE makes you dive
                    else:
                        bird_movement = -8   # normal jump

                if event.key == pygame.K_SPACE and not running:
                    # Reset game
                    bird_rect.center = (100, Height // 2)
                    bird_movement = 0
                    pipes.clear()
                    bad_items.clear()
                    Scoring_Number = 0
                    running = True

                    # reset effects
                    inverted_controls = False
                    invert_end_time = 0
                    flash_active = False
                    flash_end_time = 0
                    speed_effect = None
                    speed_effect_end_time = 0
                    pipe_speed = base_pipe_speed

            if event.type == Spawnpipe and running:
                pipes.extend(pipe_spawner(Width, Height, pipe_width, pipe_gap))

            # BAD EFFECT: spawn bad items using helper
            if event.type == SpawnBad and running:
                bad_rect, kind = spawn_bad_item(Width, Height, size=25)
                bad_items.append((bad_rect, kind))

        # ======== DRAW BACKGROUND ========
        screen.fill(Blue)

        if running:
            # ======== BIRD MOVEMENT ========
            bird_movement += gravity
            bird_rect.centery += bird_movement
            screen.blit(Bird, bird_rect)

            # ======== PIPES ========
            # horizontal movement with current pipe_speed (can be modified by bad effects)
            pipes = pipe_movement(pipes, pipe_speed)

            # small vertical wiggle
            for pipe in pipes:
                pipe.y += random.choice([-1, 0, 1])

            # draw pipes via helper
            pipe_creation(screen, pipes, Green)

            # ======== BAD ITEMS: MOVE & DRAW (helpers) ========
            bad_items = move_bad_items(bad_items, pipe_speed)
            draw_bad_items(screen, bad_items, BAD_COLORS)

            # ======== COLLISION WITH PIPES / BOUNDS ========
            running = check_collision(bird_rect, pipes, Height)

            # ======== COLLISION WITH BAD ITEMS ========
            if running:
                updated_bad_items = []
                for bad_rect, kind in bad_items:
                    if bird_rect.colliderect(bad_rect):
                        # Activate effect based on kind
                        if kind == "invert":
                            inverted_controls = True
                            invert_end_time = current_time + 3000  # 3 seconds
                        elif kind == "flash":
                            flash_active = True
                            flash_end_time = current_time + 1000   # 0.7 seconds
                        elif kind == "speedup":
                            speed_effect = "speedup"
                            pipe_speed = base_pipe_speed * 2      # faster pipes
                            speed_effect_end_time = current_time + 4000  # 4 seconds
                        elif kind == "slow":
                            speed_effect = "slow"
                            pipe_speed = max(1, base_pipe_speed // 2)   # slower pipes
                            speed_effect_end_time = current_time + 4000  # 4 seconds
                        # optional: change score here if you want bad items to also hurt score
                    else:
                        updated_bad_items.append((bad_rect, kind))
                bad_items = updated_bad_items

            # ======== SCORING ========
            for pipe in pipes:
                if pipe.centerx == bird_rect.centerx:
                    Scoring_Number += 0.5
            score(screen, font, Scoring_Number)

            # ======== VISUAL OVERLAYS FOR EFFECTS ========
            # Red tint when controls are inverted
            if inverted_controls:
                overlay = pygame.Surface((Width, Height), pygame.SRCALPHA)
                overlay.fill((255, 0, 0, 60))
                screen.blit(overlay, (0, 0))

            # White flash for flash bomb (draw last so it dominates)
            if flash_active:
                flash_surface = pygame.Surface((Width, Height), pygame.SRCALPHA)
                flash_surface.fill((255, 255, 255, 160))
                screen.blit(flash_surface, (0, 0))

        else:
            # Game over screen
            game_over_surface = font.render("Game Over! Press SPACE", True, (0, 0, 0))
            screen.blit(game_over_surface, (30, Height // 2 - 20))

        pygame.display.update()
        clock.tick(60)

if __name__ == "__main__":
    FlappyBirdCore()
