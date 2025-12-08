import pygame
import sys
import time

from Game_Creations import (
    pipe_creation,
    pipe_spawner,
    pipe_movement,
    check_collision,
    score,
    delete_all_pipes,
    box_creation,
    box_movement,
    box_spawner,
    delete_all_boxes,
    triangle_spawner,
    triangle_movement,
    triangle_creation,
    triangle_off_screen,
    delete_all_triangles,
    check_triangle_collision,
    spawn_item,
    move_items,
    draw_item,
    handle_item_collision,
    restore_pipes,
    spawn_bad_item,
    move_bad_items,
    draw_bad_items
)

def FlappyBirdCore():
    pygame.init()

    WIDTH, HEIGHT = 400, 600
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Flappy Bird Deluxe")

    BG = (135, 206, 235)

    # -------------------------
    # Bird Setup
    # -------------------------
    Bird = pygame.image.load("THEBIRDY.png").convert_alpha()
    Bird = pygame.transform.scale(Bird, (50, 40))
    BIRD_W, BIRD_H = 50, 40

    bird_rect = Bird.get_rect(center=(100, HEIGHT // 2))
    gravity = 0.7
    bird_vel = 0

    # -------------------------
    # Pipes
    # -------------------------
    base_speed = 3
    pipe_speed = base_speed
    pipes = []

    # Timestamp-based pipe spawn
    last_pipe_spawn = time.time()
    pipe_delay = 1200 / 1000  # convert ms to seconds

    # -------------------------
    # Items
    # -------------------------
    items = []
    item_delay = 3500
    SpawnItem = pygame.USEREVENT + 1
    pygame.time.set_timer(SpawnItem, item_delay)

    # -------------------------
    # State
    # -------------------------
    state = {
        "score": 0,
        "lives": 3,

        "immunity": False,
        "immunity_end": 0,

        "double_points": False,
        "double_end": 0,

        "pipe_shrink": False,
        "pipe_restore_time": 0,

        "bird_shrink": False,
        "shrink_end": 0,

        "pipe_slow": False,
        "slow_end": 0,

        "reward_popup": ("", 0),
        "red_lives_end": 0,

        "pipe_width": 60,
        "pipe_gap": 150,
        "base_pipe_width": 60,
        "base_pipe_gap": 150
    }

    font = pygame.font.SysFont(None, 36)
    clock = pygame.time.Clock()
    running = True

    # -------------------------
    # MAIN LOOP
    # -------------------------
    while True:
        now = time.time()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and running:
                    bird_vel = -8
                elif event.key == pygame.K_SPACE and not running:
                    bird_rect.center = (100, HEIGHT // 2)
                    bird_vel = 0
                    pipes.clear()
                    items.clear()
                    last_pipe_spawn = now

                    state.update({
                        "score": 0,
                        "lives": 3,
                        "immunity": False,
                        "double_points": False,
                        "pipe_shrink": False,
                        "bird_shrink": False,
                        "pipe_slow": False,
                        "pipe_width": 60,
                        "pipe_gap": 150
                    })

                    pipe_speed = base_speed

                    running = True

            if event.type == SpawnItem:
                items.append(spawn_item(WIDTH, HEIGHT))

        # -------------------------
        # DRAW
        # -------------------------
        screen.fill(BG)

        if running:
            bird_vel += gravity
            bird_rect.centery += bird_vel

            # -------------------------
            # Slow Pipes Logic
            # -------------------------
            current_pipe_delay = pipe_delay
            if state["pipe_slow"] and now < state["slow_end"]:
                pipe_speed = base_speed * 0.5
                state["pipe_gap"] = int(state["base_pipe_gap"] * 1.5)
                current_pipe_delay *= 2.5  # slow pipe spawn
            else:
                if state["pipe_slow"]:
                    state["pipe_slow"] = False
                    pipe_speed = base_speed
                    state["pipe_gap"] = state["base_pipe_gap"]

            # -------------------------
            # Timestamp-based Pipe Spawn
            # -------------------------
            if now - last_pipe_spawn > current_pipe_delay:
                pipes.extend(pipe_spawner(WIDTH, HEIGHT, state["pipe_width"], state["pipe_gap"]))
                last_pipe_spawn = now

            # -------------------------
            # Pipes + Items
            # -------------------------
            pipes = pipe_movement(pipes, pipe_speed)
            pipe_creation(screen, pipes)

            items = move_items(items)
            for rect, color, born in items:
                draw_item(screen, rect, color, born)
            items = handle_item_collision(items, bird_rect, state)

            # Restore shrunken pipes
            if state["pipe_shrink"] and now >= state["pipe_restore_time"]:
                restore_pipes(state)

            # Score
            state["score"] += 0.03 * (2 if state["double_points"] else 1)
            score(screen, font, state["score"], state["lives"])

            # Collision
            running = check_collision(bird_rect, pipes, HEIGHT, state)

            # Bird rendering
            if state["bird_shrink"] and now < state["shrink_end"]:
                shrink_img = pygame.transform.scale(Bird, (int(BIRD_W * 0.5), int(BIRD_H * 0.5)))
                shrink_rect = shrink_img.get_rect(center=bird_rect.center)
                screen.blit(shrink_img, shrink_rect)
            else:
                state["bird_shrink"] = False
                screen.blit(Bird, bird_rect)

            # Power-up Text
            power_texts = []
            if state["immunity"] and now < state["immunity_end"]:
                power_texts.append(f"IMMUNITY {int(state['immunity_end'] - now)}s")
            if state["double_points"] and now < state["double_end"]:
                power_texts.append(f"DOUBLE {int(state['double_end'] - now)}s")
            if state["pipe_shrink"] and now < state["pipe_restore_time"]:
                power_texts.append(f"PIPE SHRINK {int(state['pipe_restore_time'] - now)}s")
            if state["bird_shrink"] and now < state["shrink_end"]:
                power_texts.append(f"SHRINK {int(state['shrink_end'] - now)}s")
            if state["pipe_slow"] and now < state["slow_end"]:
                power_texts.append(f"SLOW PIPES {int(state['slow_end'] - now)}s")
            for i, t in enumerate(power_texts):
                txt = font.render(t, True, (0, 0, 0))
                screen.blit(txt, (10, 50 + i * 25))

            msg, endt = state["reward_popup"]
            if now < endt:
                popup = font.render(msg, True, (0, 0, 0))
                screen.blit(popup, (WIDTH // 2 - popup.get_width() // 2, 80))

        else:
            game_over = font.render("GAME OVER - Press SPACE", True, (255, 0, 0))
            screen.blit(game_over, (WIDTH // 2 - game_over.get_width() // 2, HEIGHT // 2))

        pygame.display.update()
        clock.tick(60)

if __name__ == "__main__":
    FlappyBirdCore()
