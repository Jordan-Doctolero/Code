import pygame
import sys
import random
import json
import os
import time

from Game_Creations import (
    pipe_creation, pipe_spawner, pipe_movement, check_collision, score,
    delete_all_pipes, box_creation, box_movement, box_spawner, delete_all_boxes,
    triangle_spawner, triangle_movement, triangle_creation, triangle_off_screen, delete_all_triangles, check_triangle_collision,
    spawn_item, move_items, draw_item, handle_item_collision, restore_pipes, 
    spawn_bad_item, move_bad_items,  draw_bad_items
)

from Profilesave import (
    load_profiles, 
    save_profiles
)

# Screen dimensions
Width, Height = 400, 600

# Colors
White = (255, 255, 255)
Blue = (135, 206, 235)
Green = (0, 200, 0)
Black = (0, 0, 0)
Yellow = (255, 255, 0)     # flash bomb/triangle color
Red = (255, 0, 0)
Orange = (255, 165, 0)
Purple = (160, 0, 160)      # invert controls
Red    = (255, 80, 80)      # speed up
DarkBlue = (80, 80, 255)    # slow motion

BAD_COLORS = {
    "invert": Purple,
    "flash": Yellow,
    "speedup": Red,
    "slow": DarkBlue
}

#Profile Management--CHATGPT
def select_or_create_profile():
    profiles = load_profiles()
    input_name = ""
    selecting = True

    while selecting:
        screen.fill((50, 50, 70))
        title = font.render("Enter your name:", True, White)
        screen.blit(title,(Width // 2 - title.get_width() // 2, Height // 3))
        name_surface = font.render(input_name + "|", True, Yellow)
        screen.blit(name_surface,(Width // 2 - name_surface.get_width() // 2, Height // 2))
        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN and input_name:
                    selecting = False
                elif event.key == pygame.K_BACKSPACE:
                    input_name = input_name[:-1]
                elif event.unicode.isalnum():
                    input_name += event.unicode

    if input_name not in profiles:
        profiles[input_name] = {"high_score": 0, "last_score": 0}
        save_profiles(profiles)

    return input_name, profiles[input_name]

#Main Game
def FlappyBirdCore():
    pygame.init()
    pygame.mixer.init()

    global screen, font
    screen = pygame.display.set_mode((Width, Height))
    font = pygame.font.SysFont(None, 40)
    pygame.display.set_caption("Flappy Bird Deluxe")

    game_state = "menu"
    play = pygame.Rect(100, 250, 200, 60)
    rules = pygame.Rect(100, 350, 200, 60)
    clock = pygame.time.Clock()

    death = pygame.mixer.Sound("Death.mp3")

    # POWER-UP STATE (GOOD + BAD) 
    # Good item timers live in `state` dict (like in Tests.py)
    state = {
        "scoring_number": 0.0,
        "lives": 3,

        "immunity": False,
        "immunity_end": 0.0,

        "double_points": False,
        "double_end": 0.0,

        "pipe_shrink": False,
        "pipe_restore_time": 0.0,

        "bird_shrink": False,
        "shrink_end": 0.0,

        "pipe_slow": False,
        "slow_end": 0.0,

        "reward_popup": ("", 0.0),
        "red_lives_end": 0.0,

        "pipe_width": 60,
        "pipe_gap": 150,
        "base_pipe_width": 60,
        "base_pipe_gap": 150
    }

    # Bad effects
    bad_items = []              # list of (rect, kind)
    inverted_controls = False
    invert_end_time = 0
    flash_active = False
    flash_end_time = 0
    speed_effect = None         # "speedup", "slow", or None
    speed_effect_end_time = 0

    # Timers for items
    SpawnItem = pygame.USEREVENT + 10
    SpawnBad = pygame.USEREVENT + 11
    item_delay = 3500
    pygame.time.set_timer(SpawnItem, item_delay)
    pygame.time.set_timer(SpawnBad, 4000)

    #  PROFILE / GAME VARIABLES (set after profile) 
    # These will be defined when entering the "profile" state and reused in "game"
    Bird1 = None
    Bird2 = None
    bird_rect1 = None
    bird_rect2 = None
    show_bird2 = False
    offset = -60
    BIRD_W, BIRD_H = 50, 40

    gravity = 0.7
    bird_movement1 = 0
    bird_movement2 = 0

    pipes = []
    boxes = []
    triangles = []

    pipe_width = state["pipe_width"]
    pipe_gap = state["pipe_gap"] 
    pipe_speed = 4
    box_width = 50
    box_speed = 2
    triangle_size = 40

    Spawnpipe = pygame.USEREVENT + 1
    Spawnbox = pygame.USEREVENT + 2
    TriangleSpawn = pygame.USEREVENT + 3

    pygame.time.set_timer(Spawnpipe, 0)
    pygame.time.set_timer(Spawnbox, 0)
    pygame.time.set_timer(TriangleSpawn, 0)

    running = False
    time_score_active = False
    tri_score_active = False
    triangle_wave_created = False
    triangles_to_spawn = 0
    triangles_spawned = 0
    previous_score_time = 0

    cycle_count = 0
    repeat_count = 0
    max_repeats = 0
    chaos_round = None
    bird2_active = None
    scoretracker = None

    random_number = 0
    random_for_tri = 0

    # Timestamp-based pipe spawn (for slow pipes power-up)
    last_pipe_spawn_time = time.time()
    base_pipe_delay = 1200 / 1000.0  # seconds

    items = []

    # Main loop
    while True:
        now = time.time()
        current_ticks = pygame.time.get_ticks()

        # UPDATE TIMERS FOR EFFECTS 
        if inverted_controls and current_ticks > invert_end_time:
            inverted_controls = False

        if flash_active and current_ticks > flash_end_time:
            flash_active = False

        if speed_effect is not None and current_ticks > speed_effect_end_time:
            speed_effect = None
            # restore to game-phase pipe speed (pipe_speed adjusted later per phase)
            # pipe_speed will be recomputed in phase logic

        # Good power-ups: restore pipe_slow when needed
        if state["pipe_slow"] and now >= state["slow_end"]:
            state["pipe_slow"] = False
            state["pipe_gap"] = state["base_pipe_gap"]

        # Restore shrunken pipes
        if state["pipe_shrink"] and now >= state["pipe_restore_time"]:
            restore_pipes(state)

        # Shrink bird timeout
        if state["bird_shrink"] and now >= state["shrink_end"]:
            state["bird_shrink"] = False

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if game_state == "menu":
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if play.collidepoint(event.pos):
                        game_state = "profile"
                    elif rules.collidepoint(event.pos):
                        game_state = "rules"

            elif game_state == "rules":
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        game_state = "menu"

            elif game_state == "game_over":
                if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                    game_state = "menu"

            elif game_state == "game":
                if event.type == pygame.KEYDOWN:
                    # Bird 1 jump with bad effect support
                    if event.key == pygame.K_SPACE and running:
                        if inverted_controls:
                            bird_movement1 = 8
                        else:
                            bird_movement1 = -8

                    # Bird 2 jump (when active) with same bad effect
                    if event.key == pygame.K_SPACE and running and show_bird2:
                        if inverted_controls:
                            bird_movement2 = 8
                        else:
                            bird_movement2 = -8

                    # Reset game on space when not running
                    if event.key == pygame.K_SPACE and not running:
                        bird_rect1.center = (100, Height // 2)
                        bird_rect2.center = (bird_rect1.centerx + offset, bird_rect1.centery)
                        bird_movement1 = 0
                        bird_movement2 = 0
                        BIRD_W, BIRD_H = 50, 40
                        previous_score_time = pygame.time.get_ticks()
                        pygame.time.set_timer(Spawnpipe, 1200)
                        pygame.time.set_timer(Spawnbox, 0)
                        pygame.time.set_timer(TriangleSpawn, 0)
                        time_score_active = False
                        tri_score_active = False
                        pipes.clear()
                        boxes.clear()
                        triangles.clear()
                        state["scoring_number"] = 0
                        cycle_count = 0
                        repeat_count = 0
                        running = True
                        show_bird2 = False
                        bird2_active = None
                        scoretracker = None
                        chaos_round = None

                        # reset power-up states
                        items.clear()
                        bad_items.clear()
                        state.update({
                            "scoring_number": 0.0,
                            "lives": 3,
                            "immunity": False,
                            "immunity_end": 0.0,
                            "double_points": False,
                            "double_end": 0.0,
                            "pipe_shrink": False,
                            "pipe_restore_time": 0.0,
                            "bird_shrink": False,
                            "shrink_end": 0.0,
                            "pipe_slow": False,
                            "slow_end": 0.0,
                            "pipe_width": state["base_pipe_width"],
                            "pipe_gap": state["base_pipe_gap"]
                        })
                        inverted_controls = False
                        invert_end_time = 0
                        flash_active = False
                        flash_end_time = 0
                        speed_effect = None
                        speed_effect_end_time = 0
                        last_pipe_spawn_time = now

                # Pipe spawn event
                if event.type == Spawnpipe:
                    pipes.extend(pipe_spawner(Width, Height, state["pipe_width"], state["pipe_gap"]))

                # Box spawn event
                if event.type == Spawnbox and time_score_active:
                    boxes.append(box_spawner(screen, 50))
                     
                # Triangle spawn event
                if event.type == TriangleSpawn and tri_score_active:
                    if triangles_spawned < triangles_to_spawn:
                        triangles.append(triangle_spawner(screen, triangle_size))
                        triangles_spawned += 1
                    if triangles_spawned >= triangles_to_spawn:
                        pygame.time.set_timer(TriangleSpawn, 0)
                
                # Good item spawn
                if event.type == SpawnItem and running:
                    items.append(spawn_item(Width, Height))

                # Bad item spawn
                if event.type == SpawnBad and running:
                    bad_rect, kind = spawn_bad_item(Width, Height, size=25)
                    bad_items.append((bad_rect, kind))

        if game_state == "menu":
            screen.fill(Blue)
            pygame.draw.rect(screen, Green, play)
            pygame.draw.rect(screen, Red, rules)
            screen.blit(font.render("PLAY", True, Black), (play.x + 60, play.y + 15))
            screen.blit(font.render("RULES", True, Black), (rules.x + 55, rules.y + 15))

        elif game_state == "rules":
            rules_font = pygame.font.SysFont(None, 22)
            screen.fill(White)
            rules_lines = [
                "Flappy Bird Game Rules and Tips:",
                "-Press SPACE to make Bird 1 fly.",
                "-Avoid any obstacles.",
                "-Score points.",
                "-If you hit a pipe or box, it's game over.",
                "-There will be powerups good and bad that will spawn.",
                "Press ESC to return to the menu.",
            ]

            y = 20
            for line in rules_lines:
                screen.blit(rules_font.render(line, True, Black), (6, y))
                y += 40

        elif game_state == "profile":
            # Profile
            player_name, profile = select_or_create_profile()
            #player_last_score = profile["last_score"]
            state["scoring_number"] = 0.0
            high_score = profile["high_score"]

            # Bird 1
            Bird1 = pygame.image.load("THEBIRDY.png").convert_alpha()
            Bird1 = pygame.transform.scale(Bird1, (50, 40))
            bird_rect1 = Bird1.get_rect(center=(100, Height // 2))

            # Bird 2
            Bird2 = pygame.image.load("21.png").convert_alpha()
            Bird2.set_colorkey((0, 0, 0))
            Bird2 = pygame.transform.scale(Bird2, (50, 40))
            offset = -60
            bird_rect2 = Bird2.get_rect(center=(bird_rect1.centerx + offset, bird_rect1.centery))
            show_bird2 = False

            # Game variables
            running = True
            gravity = 0.7
            bird_movement1 = 0
            bird_movement2 = 0
            cycle_count = 0
            repeat_count = 0
            previous_score_time = pygame.time.get_ticks()
            time_score_active = False
            tri_score_active = False
            bird2_active = None
            scoretracker = None
            death_played = False
            repeat_count = 0       # how many cycles have happened
            max_repeats = 2
            BIRD_W, BIRD_H = 50, 40

            #Pipe Dimensions and Speed
            state["pipe_width"] = state["base_pipe_width"]
            state["pipe_gap"] = state["base_pipe_gap"]
            pipe_width = state["pipe_width"]
            pipe_gap = state["pipe_gap"]
            pipe_speed = 4
            pipes = []
            
            #Box Dimensions and Speed
            box_width = 50
            box_speed = 2
            boxes = []

            #Triangle Dimensions and Speed
            triangles = []
            triangle_size = 40
            TriangleSpawn = pygame.USEREVENT + 3
            triangle_wave_created = False
            triangles_to_spawn = 0
            triangles_spawned = 0

            # Events
            Spawnpipe = pygame.USEREVENT + 1
            Spawnbox = pygame.USEREVENT + 2
            pygame.time.set_timer(Spawnpipe, 1200)
            pygame.time.set_timer(Spawnbox, 0)
            pygame.time.set_timer(TriangleSpawn, 0)
            chaos_round = None

            # Power items
            items.clear()
            bad_items.clear()
            state.update({
                "scoring_number": 0.0, 
                "lives": 3,
                "immunity": False,
                "immunity_end": 0.0,
                "double_points": False,
                "double_end": 0.0,
                "pipe_shrink": False,
                "pipe_restore_time": 0.0,
                "bird_shrink": False,
                "shrink_end": 0.0,
                "pipe_slow": False,
                "slow_end": 0.0,
                "pipe_width": state["base_pipe_width"],
                "pipe_gap": state["base_pipe_gap"]
            })
            inverted_controls = False
            invert_end_time = 0
            flash_active = False
            flash_end_time = 0
            speed_effect = None
            speed_effect_end_time = 0
            last_pipe_spawn_time = now

            # Random thresholds for phases
            random_number = random.randint(15,20)
            print("Box:", random_number)
            random_for_tri = random.randint(random_number + 15, random_number + 25)
            print("Triangle:", random_for_tri)

            game_state = "game"

        elif game_state == "game":
            screen.fill(Blue)

        if running:
            #print(cycle_count)
            # Adjust pipe_speed from bad effects
            phase_base_pipe_speed = 4
            if speed_effect == "speedup":
                pipe_speed = phase_base_pipe_speed * 2
            elif speed_effect == "slow":
                pipe_speed = max(1, phase_base_pipe_speed // 2)
            else:
                pipe_speed = phase_base_pipe_speed

            #Added: base box speed affected by bad speed powerups
            box_base_speed = 2
            if speed_effect == "speedup":
                box_speed = box_base_speed * 2
            elif speed_effect == "slow":
                box_speed = max(1, box_base_speed // 2)
            else:
                box_speed = box_base_speed

            # Adjust pipe speed and gap for pipe_slow good effect
            current_pipe_delay = base_pipe_delay
            if state["pipe_slow"] and now < state["slow_end"]:
                pipe_speed = max(1, pipe_speed // 2)
                state["pipe_gap"] = int(state["base_pipe_gap"] * 1.5)
                current_pipe_delay *= 2.5
            else:
                if state["pipe_slow"]:
                    state["pipe_slow"] = False
                    state ["pipe_gap"] = state["base_pipe_gap"]
            
            #Bird1
            bird_movement1 += gravity
            bird_rect1.centery += bird_movement1
            
            #Bird2 
            if show_bird2:
                bird_movement2 += gravity
                bird_rect2.centery += bird_movement2

            # Pipes
            pipes = pipe_movement(pipes, pipe_speed)
            pipe_creation(screen, pipes, Green)

            # Draw score and high score--Placed here so it is above the pipes
            score(screen, font, state["scoring_number"],state["lives"])
            display_high = max(high_score, state["scoring_number"])
            high_score_surf = font.render(f"High Score: {int(display_high)}", True, (0, 0, 0))
            screen.blit(high_score_surf, (10, 40))

            #Pipe wiggle
            for pipe in pipes:
                pipe["rect"].y += random.choice([-1, 0, 1])

            bad_items = move_bad_items(bad_items, pipe_speed)
            draw_bad_items(screen, bad_items, BAD_COLORS)

            new_bad = []
            for bad_rect, kind in bad_items:
                hit1 = bird_rect1.colliderect(bad_rect)
                hit2 = show_bird2 and bird_rect2.colliderect(bad_rect)
                if hit1 or hit2:
                    if kind == "invert":
                        inverted_controls = True
                        invert_end_time = current_ticks + 3000
                        print("Invert triggered")  # debug
                    elif kind == "flash":
                        flash_active = True
                        flash_end_time = current_ticks + 1000
                        print("Flash triggered")
                    elif kind == "speedup":
                        speed_effect = "speedup"
                        speed_effect_end_time = current_ticks + 4000
                    elif kind == "slow":
                        speed_effect = "slow"
                        speed_effect_end_time = current_ticks + 4000
                else:
                    new_bad.append((bad_rect, kind))

            bad_items = new_bad

            items = move_items(items)
            for rect, color, born in items:
                draw_item(screen, rect, color, born)
            items, cycle_count = handle_item_collision(items, bird_rect1, state, cycle_count)
 
            # Bird rendering (pipes/normal phase) 
            if state["bird_shrink"] and now < state["shrink_end"]:
                shrink_img1 = pygame.transform.scale(Bird1, (int(BIRD_W * 0.5), int(BIRD_H * 0.5)))
                shrink_rect1 = shrink_img1.get_rect(center=bird_rect1.center)
                screen.blit(shrink_img1, shrink_rect1)
                if show_bird2:
                    shrink_img2 = pygame.transform.scale(Bird2, (int(BIRD_W * 0.5), int(BIRD_H * 0.5)))
                    shrink_rect2 = shrink_img2.get_rect(center=bird_rect2.center)
                    screen.blit(shrink_img2, shrink_rect2)
            else:
                state["bird_shrink"] = False
                screen.blit(Bird1, bird_rect1)
                if show_bird2:
                    screen.blit(Bird2, bird_rect2) 

            # Collision with pipes
            if not check_collision(bird_rect1, pipes, Height, state):
                running = False
                game_state = "game_over"

            if show_bird2 and not check_collision(bird_rect2, pipes, Height, state):
                running = False
                game_state = "game_over"

            # Scoring on pipes (normal phase only)
            if not time_score_active and not tri_score_active:
                for pipe in pipes:
                    if pipe["type"] == "bottom":
                        if pipe["rect"].centerx < bird_rect1.centerx and not pipe.get("scored1", False):
                            state["scoring_number"] += 1
                            cycle_count += 1
                            pipe["scored1"] = True
                        if (show_bird2 and pipe["rect"].centerx < bird_rect2.centerx and not pipe.get("scored2", False)):
                            state["scoring_number"] += 1
                            cycle_count += 1
                            pipe["scored2"] = True
            
            # Spawn Bird 2 at random score before box event
            if scoretracker is None:
                randomness = random.randint(1, max(1, random_number - 1))
                print("Bird 2 Spawn:", randomness)
                scoretracker = True
            if cycle_count >= randomness and bird2_active is None:
                bird_rect2.center = (bird_rect1.centerx + offset, bird_rect1.centery)
                bird_movement2 = bird_movement1
                show_bird2 = True
                bird2_active = True

            # Box scoring event start
            if cycle_count >= random_number and not time_score_active and not tri_score_active:
                delete_all_pipes(screen, pipes)
                pygame.time.set_timer(Spawnpipe, 0)
                pygame.time.set_timer(Spawnbox, 800)
                time_score_active = True
                previous_score_time = pygame.time.get_ticks()
                show_bird2 = False

            # Box phase
            if time_score_active:
                # Changed: draw bird with shrink logic during box phase
                if state["bird_shrink"] and now < state["shrink_end"]:
                    shrink_img1 = pygame.transform.scale(Bird1, (int(BIRD_W * 0.5), int(BIRD_H * 0.5)))
                    shrink_rect1 = shrink_img1.get_rect(center=bird_rect1.center)
                    screen.blit(shrink_img1, shrink_rect1)
                else:
                    screen.blit(Bird1, bird_rect1)

                for i in range(len(boxes) - 1, -1, -1):
                    rect, vel = boxes[i]
                    vel = box_movement(rect, vel, box_speed, Height)
                    boxes[i][1] = vel
                    if rect.right < 0:
                        boxes.pop(i)
                    else:
                        pygame.draw.rect(screen, Black, rect)

                current_time = pygame.time.get_ticks()
                if current_time - previous_score_time >= 1000:
                    state["scoring_number"] += 1
                    cycle_count += 1
                    previous_score_time = current_time
            
            # boxes collision using lives + immunity
            now_time = time.time()
            if state["immunity"] and now_time >= state["immunity_end"]:
                state["immunity"] = False

            for rect, vel in boxes:
                hit1 = bird_rect1.colliderect(rect)
                hit2 = show_bird2 and bird_rect2.colliderect(rect)
                if hit1 or hit2:
                    if not state["immunity"]:
                        state["lives"] -= 1
                        print("Hit box, lives now:", state["lives"])  # debug
                        if state["lives"] < 0:
                            running = False
                            game_state = "game_over"
                            break
                        else:
                            # start brief immunity after a non-lethal hit
                            state["immunity"] = True
                            state["immunity_end"] = now_time + 1
                            # if already immune, do nothing (no extra life loss)

            # Triangle scoring event start (after box phase)
            if cycle_count >= random_for_tri and not tri_score_active and time_score_active:
                delete_all_boxes(screen, boxes)
                tri_score_active = True
                triangle_wave_created = False
                triangles_to_spawn = random.randint(15,20)
                print("Triangles to spawn:", triangles_to_spawn)
                triangles_spawned = 0
                pygame.time.set_timer(TriangleSpawn, 400)
                pygame.time.set_timer(Spawnbox, 0)
                previous_score_time = pygame.time.get_ticks()
                screen.fill(Blue)

            # Triangle phase
            if tri_score_active:
                for i in range(len(triangles) - 1, -1, -1):
                    points, x_vel = triangles[i]
                    x_vel = triangle_movement(points, x_vel, pipe_speed)
                    triangles[i][1] = x_vel
                    if triangle_off_screen(points):
                        triangles.pop(i)
                    else:
                        triangle_creation(screen, [triangles[i]], Orange)

                current_time = pygame.time.get_ticks()
                if current_time - previous_score_time >= 2000:
                    state["scoring_number"] += 1
                    cycle_count += 1
                    previous_score_time = current_time
            
            # Triangles collision using lives + immunity
            if not check_triangle_collision(bird_rect1, triangles, state):
                running = False
                game_state = "game_over"
            elif show_bird2 and not check_triangle_collision(bird_rect2, triangles, state):
                running = False
                game_state = "game_over"
                
                if triangles_spawned == triangles_to_spawn and not triangle_wave_created:
                    if len(triangles) == 0:
                        triangle_wave_created = True
                        pygame.time.set_timer(TriangleSpawn, 0)
                        delete_all_triangles(triangles)
                        tri_score_active = False
                        time_score_active = False
                        bird2_active = None
                        scoretracker = None
                        show_bird2 = False

                        repeat_count += 1
                        print("Cycle completed:", repeat_count)

                        random_number = random.randint(15, 20)
                        random_for_tri = random.randint(random_number + 15, random_number + 25)
                        print("New Box:", random_number)
                        print("New Tri:", random_for_tri)

                        # If we still need more repeats → restart pipe phase
                        if repeat_count < max_repeats:
                            print("Restarting cycle...")
                            cycle_count = 0
                            scoretracker = None
                            pygame.time.set_timer(Spawnpipe, 1200)
                            pipes.clear()
                        else:
                            print("All repeats done!")
                            chaos_round = True

                #Chaos Round
                if chaos_round and not time_score_active and not tri_score_active:
                    # Changed: use base chaos speeds, then apply powerups
                    chaos_pipe_base = 3
                    chaos_box_base = 2

                    if speed_effect == "speedup":
                        pipe_speed = chaos_pipe_base * 2
                        box_speed = chaos_box_base * 2
                    elif speed_effect == "slow":
                        pipe_speed = max(1, chaos_pipe_base // 2)
                        box_speed = max(1, chaos_box_base // 2)
                    else:
                        pipe_speed = chaos_pipe_base
                        box_speed = chaos_box_base

                    # good slow pipes powerup in chaos
                    if state["pipe_slow"] and now < state["slow_end"]:
                        pipe_speed = max(1, pipe_speed // 2)
                        state["pipe_gap"] = int(state["base_pipe_gap"] * 1.5)
                    else:
                        if state["pipe_slow"]:
                            state["pipe_slow"] = False
                            state["pipe_gap"] = state["base_pipe_gap"]

                    pygame.time.set_timer(Spawnpipe, 1000)
                    pygame.time.set_timer(Spawnbox, 1000)
                    pygame.time.set_timer(TriangleSpawn, 500) 

                    time_score_active = True
                    tri_score_active = True
                    triangle_wave_created = False
                    triangles_spawned = 0
                    triangles_to_spawn = random.randint(1, 2)

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
                txt = font.render(t, True, Black)
                screen.blit(txt, (10, 80 + i * 25))

            msg, endt = state["reward_popup"]
            if now < endt:
                popup = font.render(msg, True, Black)
                screen.blit(popup,(Width // 2 - popup.get_width() // 2, 60))

            if inverted_controls:
                overlay = pygame.Surface((Width, Height), pygame.SRCALPHA)
                overlay.fill((255, 0, 0, 60))
                screen.blit(overlay, (0, 0))
            if flash_active:
                flash_surf = pygame.Surface((Width, Height), pygame.SRCALPHA)
                flash_surf.fill((255, 255, 255, 160))
                screen.blit(flash_surf, (0, 0))
                                        
        elif game_state == "game_over":
            if not death_played:
                death.play()
                death_played = True

            screen.fill(Blue)
            game_over_surface = font.render("Game Over! Press SPACE", True, (0, 0, 0))
            screen.blit(game_over_surface, (30, Height // 2 - 20))

            profiles = load_profiles()
            profiles[player_name]["last_score"] = int(state["scoring_number"])
            if state["scoring_number"] > high_score:
                profiles[player_name]["high_score"] = int(state["scoring_number"])
            save_profiles(profiles)

        pygame.display.update()
        clock.tick(60)

if __name__ == "__main__":
    FlappyBirdCore()
