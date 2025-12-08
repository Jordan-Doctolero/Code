import pygame
import sys
import random
import json
import os
from JordansGC import (
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
    check_triangle_collision
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
Yellow = (255, 255, 0)
Red = (255, 0, 0)
Orange = (255, 165, 0)

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

def FlappyBirdCore():
    pygame.init()
    pygame.mixer.init()

    global screen, font
    screen = pygame.display.set_mode((Width, Height))
    font = pygame.font.SysFont(None, 40)
    pygame.display.set_caption("New Flappy Bird")

    game_state = "menu"
    play = pygame.Rect(100, 250, 200, 60)
    rules = pygame.Rect(100, 350, 200, 60)
    clock = pygame.time.Clock()

    death = pygame.mixer.Sound("Death.mp3")

    # Main loop
    while True:
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
                    # Bird 1 jump
                    if event.key == pygame.K_SPACE and running:
                        bird_movement1 = -8

                    # Bird 2 jump (when active)
                    if event.key == pygame.K_SPACE and running and show_bird2:
                        bird_movement2 = -8

                    # Reset game on space when not running
                    if event.key == pygame.K_SPACE and not running:
                        bird_rect1.center = (100, Height // 2)
                        bird_rect2.center = (bird_rect1.centerx + offset, bird_rect1.centery)
                        bird_movement1 = 0
                        bird_movement2 = 0
                        previous_score_time = pygame.time.get_ticks()
                        pygame.time.set_timer(Spawnpipe, 1200)
                        pygame.time.set_timer(Spawnbox, 0)
                        pygame.time.set_timer(TriangleSpawn, 0)
                        time_score_active = False
                        tri_score_active = False
                        pipes.clear()
                        boxes.clear()
                        triangles.clear()
                        scoring_number = 0
                        cycle_count = 0
                        repeat_count = 0
                        running = True
                        show_bird2 = False
                        bird2_active = None
                        scoretracker = None
                        Repeat = False
                        chaos_round = None

                # Pipe spawn event
                if event.type == Spawnpipe:
                    pipes.extend(pipe_spawner(Width, Height, pipe_width, pipe_gap))

                # Box spawn event
                if event.type == Spawnbox and time_score_active:
                    new_box = box_spawner(screen, box_width)
                    boxes.append(new_box)

                # Triangle spawn event
                if event.type == TriangleSpawn and tri_score_active:
                    if triangles_spawned < triangles_to_spawn:
                        triangles.append(triangle_spawner(screen, triangle_size))
                        triangles_spawned += 1
                    if triangles_spawned >= triangles_to_spawn:
                        pygame.time.set_timer(TriangleSpawn, 0)

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
            player_last_score = profile["last_score"]
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
            scoring_number = 0
            cycle_count = 0
            repeat_count = 0
            previous_score_time = pygame.time.get_ticks()
            time_score_active = False
            tri_score_active = False
            bird2_active = None
            scoretracker = None
            death_played = False
            Repeat = False
            repeat_count = 0       # how many cycles have happened
            max_repeats = 0
            
            #Pipe Dimensions and Speed
            pipe_width = 60
            pipe_gap = 150
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
            chaos_round = None

            # Random thresholds for phases
            random_number = random.randint(4,6)
            print("Box:", random_number)
            random_for_tri = random.randint(random_number + 1, random_number + 2)
            print("Triangle:", random_for_tri)

            game_state = "game"

        elif game_state == "game":
            screen.fill(Blue)

            if running:
                # Bird 1 movement
                bird_movement1 += gravity
                bird_rect1.centery += bird_movement1
                screen.blit(Bird1, bird_rect1)

                # Bird 2 movement
                if show_bird2:
                    bird_movement2 += gravity
                    bird_rect2.centery += bird_movement2
                    screen.blit(Bird2, bird_rect2)

                # Pipes
                pipes = pipe_movement(pipes, pipe_speed)
                pipe_creation(screen, pipes, Green)

                # Collision with pipes
                if not check_collision(bird_rect1, pipes, Height):
                    running = False
                    game_state = "game_over"

                if show_bird2 and not check_collision(bird_rect2, pipes, Height):
                    running = False
                    game_state = "game_over"

                # Collision with boxes
                for rect, vel in boxes:
                    if bird_rect1.colliderect(rect):
                        running = False
                        game_state = "game_over"
                        break
                    if show_bird2 and bird_rect2.colliderect(rect):
                        running = False
                        game_state = "game_over"
                        break

                # Collision with triangles
                if not check_triangle_collision(bird_rect1, triangles):
                    running = False
                    game_state = "game_over"

                # Scoring on pipes (normal phase only)
                if not time_score_active and not tri_score_active:
                    for pipe in pipes:
                        if pipe["type"] == "bottom":
                            if pipe["rect"].centerx < bird_rect1.centerx and not pipe.get("scored1", False):
                                scoring_number += 1
                                cycle_count += 1
                                pipe["scored1"] = True
                            if (show_bird2 and pipe["rect"].centerx < bird_rect2.centerx and not pipe.get("scored2", False)):
                                scoring_number += 1
                                cycle_count += 1
                                pipe["scored2"] = True

                # Draw score and high score
                score(screen, font, scoring_number)
                display_high = max(high_score, scoring_number)
                high_score_surf = font.render(f"High Score: {int(display_high)}", True, (0, 0, 0))
                screen.blit(high_score_surf, (10, 40))

                # Spawn Bird 2 at random score before box event
                if scoretracker is None:
                    randomness = random.randint(1, random_number - 1)
                    print("Bird 2 Spawn:", randomness)
                    scoretracker = True
                if cycle_count == randomness and bird2_active is None:
                    bird_rect2.center = (bird_rect1.centerx + offset, bird_rect1.centery)
                    bird_movement2 = bird_movement1
                    show_bird2 = True
                    bird2_active = True

                # Box scoring event start
                if cycle_count == random_number and not time_score_active and not tri_score_active:
                    delete_all_pipes(screen, pipes)
                    pygame.time.set_timer(Spawnpipe, 0)
                    pygame.time.set_timer(Spawnbox, 800)
                    time_score_active = True
                    previous_score_time = pygame.time.get_ticks()
                    show_bird2 = False

                # Box phase
                if time_score_active:
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
                        scoring_number += 1
                        cycle_count += 1
                        previous_score_time = current_time

                # Triangle scoring event start (after box phase)
                if cycle_count == random_for_tri and not tri_score_active and time_score_active:
                    delete_all_boxes(screen, boxes)
                    tri_score_active = True
                    triangle_wave_created = False
                    triangles_to_spawn = random.randint(1,3)
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
                        scoring_number += 1
                        cycle_count += 1
                        previous_score_time = current_time
                    
                    
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

                            random_number = random.randint(4, 6)
                            random_for_tri = random.randint(random_number + 1, random_number + 2)
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
                        # Chaos round logic can be implemented here
                        box_speed = 2
                        pipe_speed = 3
                        pygame.time.set_timer(Spawnpipe, 1000)
                        pygame.time.set_timer(Spawnbox, 1000)
                        pygame.time.set_timer(TriangleSpawn, 500)

                        time_score_active = True
                        tri_score_active = True
                        triangle_wave_created = False
                        triangles_spawned = 0
                        triangles_to_spawn = random.randint(1, 2)
                                        
        elif game_state == "game_over":
            if not death_played:
                death.play()
                death_played = True

            screen.fill(Blue)
            game_over_surface = font.render("Game Over! Press SPACE", True, (0, 0, 0))
            screen.blit(game_over_surface, (30, Height // 2 - 20))

            profiles = load_profiles()
            profiles[player_name]["last_score"] = int(scoring_number)
            if scoring_number > high_score:
                profiles[player_name]["high_score"] = int(scoring_number)
            save_profiles(profiles)

        pygame.display.update()
        clock.tick(60)

if __name__ == "__main__":
    FlappyBirdCore()
