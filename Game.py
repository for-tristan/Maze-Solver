import pygame
import random
from collections import deque
import config
import monster_ai

# ---------------- INIT ----------------
pygame.mixer.pre_init(44100, -16, 2, 512)
pygame.init()

 
 
# ---------------- CONFIG ----------------
# Maze & Player
ROWS = config.ROWS
COLS = config.COLS
TILE_SIZE = config.TILE_SIZE
VISION_RADIUS = config.PLAYER_VISION
MOVE_DELAY = 6400 // config.PLAYER_SPEED

# Monster
MONSTER_SPEED = 6400 // config.MONSTER_SPEED
MONSTER_VISION = config.MONSTER_VISION

# Screen
info = pygame.display.Info()
SCREEN_WIDTH, SCREEN_HEIGHT = info.current_w, info.current_h
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.NOFRAME)
pygame.display.set_caption("Maze Game")

# Timing
FPS = 60

# ---------------- COLORS ----------------
BACKGROUND = (110, 120, 140)
WALLS = (15, 20, 55)
PLAYER = (0, 100, 255)
GHOST1 = (40, 110, 210)
GHOST2 = (85, 115, 170)
START = (20, 40, 130)
EXIT = (150, 35, 130)
WIN = (255, 255, 0)
BUTTON_ON = (10, 50, 10)
BUTTON_OFF = (40, 50, 40)
EXIT_BUTTON_COLOR = (50, 10, 10)
DARKNESS_COLOR = (0, 5, 25)

# ---------------- FONTS & CLOCK ----------------
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 50)
small_font = pygame.font.SysFont(None, 30)

# ---------------- UI BUTTONS ----------------
mute_button_rect = pygame.Rect(SCREEN_WIDTH - 60, 10, 50, 50)  # Top-right
exit_button_rect = pygame.Rect(10, 10, 50, 50)                 # Top-left

# ---------------- MAZE ----------------
maze = [[1 for _ in range(COLS)] for _ in range(ROWS)]
DIRS = [(0, -1), (1, 0), (0, 1), (-1, 0)]  # N, E, S, W

def generate_maze():
    """Generates a random maze using DFS with bias against straight paths."""
    visited = [[False] * COLS for _ in range(ROWS)]
    stack = [(0, 0)]
    visited[0][0] = True
    maze[0][0] = 0

    last_dir = None
    straight_len = 0

    while stack:
        x, y = stack[-1]
        neighbors = []

        for dx, dy in DIRS:
            nx, ny = x + dx * 2, y + dy * 2
            if 0 <= nx < COLS and 0 <= ny < ROWS and not visited[ny][nx]:
                neighbors.append((nx, ny, dx, dy))

        if neighbors:
            # Weight against continuing straight
            weighted = []
            for nx, ny, dx, dy in neighbors:
                weight = 1 if (dx, dy) == last_dir and straight_len > 1 else 4
                weighted.append((nx, ny, dx, dy, weight))

            # Flatten weighted list
            choices = [item for item in weighted for _ in range(item[4])]
            nx, ny, dx, dy, _ = random.choice(choices)

            maze[y + dy][x + dx] = 0
            maze[ny][nx] = 0
            visited[ny][nx] = True
            stack.append((nx, ny))

            if (dx, dy) == last_dir:
                straight_len += 1
            else:
                last_dir = (dx, dy)
                straight_len = 1
        else:
            stack.pop()
            straight_len = 0
            last_dir = None

def add_loops(loop_chance=0.07):
    """Randomly opens some walls to create loops."""
    for y in range(2, ROWS - 2):
        for x in range(2, COLS - 2):
            if maze[y][x] == 1 and random.random() < loop_chance:
                open_neighbors = sum(maze[y+dy][x+dx] == 0 for dx, dy in DIRS)
                if open_neighbors >= 2:
                    maze[y][x] = 0

generate_maze()
add_loops()

# ---------------- START & EXIT ----------------
start_pos = (0, 0)

def find_exit():
    """Finds the farthest point from the start to use as the exit."""
    visited = [[False]*COLS for _ in range(ROWS)]
    q = deque([(0, 0, 0)])
    visited[0][0] = True
    farthest = (0, 0, 0)

    while q:
        x, y, d = q.popleft()
        farthest = (x, y, d)
        for dx, dy in DIRS:
            nx, ny = x + dx, y + dy
            if 0 <= nx < COLS and 0 <= ny < ROWS and maze[ny][nx] == 0 and not visited[ny][nx]:
                visited[ny][nx] = True
                q.append((nx, ny, d + 1))

    return farthest[:2]

exit_pos = find_exit()

# ---------------- ENTITIES ----------------
player = [0, 0]
ghost1 = [0, 0]
ghost2 = [0, 0]
monster = [exit_pos[0], exit_pos[1]]  # Monster starts at exit
monstertrail = deque(maxlen=3)

last_move = 0
oldmove = 0
won = False

# ---------------- CAMERA & VISION ----------------
camera_x, camera_y = 0, 0
CAMERA_SPEED = 0.12  # smooth camera speed

vision_x, vision_y = player[0] * TILE_SIZE, player[1] * TILE_SIZE
VISION_SMOOTH = CAMERA_SPEED

fog_camera_x, fog_camera_y = 0, 0
FOG_LAG_SPEED = 0.06  # slower than camera

# ---------------- DRAW FUNCTIONS ----------------
def draw_maze(camera_x, camera_y):
    for y in range(ROWS):
        for x in range(COLS):
            rect = pygame.Rect(x*TILE_SIZE - camera_x,
                               y*TILE_SIZE - camera_y,
                               TILE_SIZE, TILE_SIZE)
            if rect.colliderect(screen.get_rect()):
                if (x, y) == start_pos:
                    color = START
                elif (x, y) == exit_pos:
                    color = EXIT
                else:
                    color = WALLS if maze[y][x] else BACKGROUND
                pygame.draw.rect(screen, color, rect)

def draw_entities(camera_x, camera_y):
    """Draws player, ghosts, and monster (with trail)."""
    # Monster trail
    for i, (tx, ty) in enumerate(monstertrail):
        alpha = int(255 * (i + 1) / len(monstertrail))
        s = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
        s.fill((200, 40, 40, alpha))
        screen.blit(s, (tx * TILE_SIZE - camera_x, ty * TILE_SIZE - camera_y))

    # Monster
    pygame.draw.rect(screen, (200, 40, 40),
                     (monster[0]*TILE_SIZE - camera_x,
                      monster[1]*TILE_SIZE - camera_y,
                      TILE_SIZE, TILE_SIZE))

    # Player and ghosts
    for pos, color in [(ghost2, GHOST2), (ghost1, GHOST1), (player, PLAYER)]:
        pygame.draw.rect(screen, color,
                         (pos[0]*TILE_SIZE - camera_x,
                          pos[1]*TILE_SIZE - camera_y,
                          TILE_SIZE, TILE_SIZE))

def draw_mute_button():
    color = BUTTON_OFF if is_muted else BUTTON_ON
    pygame.draw.rect(screen, color, mute_button_rect)
    text = small_font.render("M", True, (190, 190, 190))
    screen.blit(text, (mute_button_rect.x + 17, mute_button_rect.y + 17))

def draw_exit_button():
    pygame.draw.rect(screen, EXIT_BUTTON_COLOR, exit_button_rect)
    text = small_font.render("X", True, (255, 255, 255))
    screen.blit(text, (exit_button_rect.x + 15, exit_button_rect.y + 15))

def draw_fog_of_war(camera_x, camera_y, show_player=True, show_monster=True):
    """Draws darkness overlay with vision radius for player & monster."""
    global fog_camera_x, fog_camera_y

    fog_camera_x += (camera_x - fog_camera_x) * FOG_LAG_SPEED
    fog_camera_y += (camera_y - fog_camera_y) * FOG_LAG_SPEED

    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    overlay.fill((*DARKNESS_COLOR, 255))  # fully dark

    px, py = vision_x - camera_x + TILE_SIZE//2, vision_y - camera_y + TILE_SIZE//2
    radius_player = VISION_RADIUS * TILE_SIZE

    mx, my = monster[0]*TILE_SIZE - camera_x + TILE_SIZE//2, monster[1]*TILE_SIZE - camera_y + TILE_SIZE//2
    radius_monster = MONSTER_VISION * TILE_SIZE

    fade_extra = 3 * TILE_SIZE

    for y in range(ROWS):
        for x in range(COLS):
            tile_cx = x * TILE_SIZE + TILE_SIZE // 2 - camera_x
            tile_cy = y * TILE_SIZE + TILE_SIZE // 2 - camera_y

            alpha = 255

            if show_player:
                dist_player = ((tile_cx - px) ** 2 + (tile_cy - py) ** 2) ** 0.5
                if dist_player <= radius_player:
                    alpha_player = 0
                elif dist_player <= radius_player + fade_extra:
                    alpha_player = 255 * (dist_player - radius_player) / fade_extra
                else:
                    alpha_player = 255
                alpha = min(alpha, alpha_player)

            if show_monster and radius_monster > 0:
                dist_monster = ((tile_cx - mx) ** 2 + (tile_cy - my) ** 2) ** 0.5
                if dist_monster <= radius_monster:
                    alpha_monster = 0
                elif dist_monster <= radius_monster + fade_extra:
                    alpha_monster = 255 * (dist_monster - radius_monster) / fade_extra
                else:
                    alpha_monster = 255
                alpha = min(alpha, alpha_monster)

            if alpha < 255:
                rect = pygame.Rect(x*TILE_SIZE - camera_x,
                                   y*TILE_SIZE - camera_y,
                                   TILE_SIZE, TILE_SIZE)
                overlay.fill((*DARKNESS_COLOR, int(alpha)), rect)

    screen.blit(overlay, (0, 0))

# ---------------- GAME LOOP ----------------
running = True
while running:
    now = pygame.time.get_ticks()

    # ----- EVENTS -----
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if mute_button_rect.collidepoint(event.pos):
                if not is_muted:
                    previous_volume = pygame.mixer.music.get_volume()
                    pygame.mixer.music.set_volume(0)
                    is_muted = True
                else:
                    pygame.mixer.music.set_volume(previous_volume)
                    is_muted = False
            elif exit_button_rect.collidepoint(event.pos):
                running = False

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_m:
                if not is_muted:
                    previous_volume = pygame.mixer.music.get_volume()
                    pygame.mixer.music.set_volume(0)
                    is_muted = True
                else:
                    pygame.mixer.music.set_volume(previous_volume)
                    is_muted = False
            elif event.key == pygame.K_ESCAPE:
                running = False

    keys = pygame.key.get_pressed()

    # ----- PLAYER MOVE -----
    if now - last_move > MOVE_DELAY and not won:
        dx = dy = 0
        if keys[pygame.K_w] or keys[pygame.K_UP]: dy = -1
        elif keys[pygame.K_s] or keys[pygame.K_DOWN]: dy = 1
        elif keys[pygame.K_a] or keys[pygame.K_LEFT]: dx = -1
        elif keys[pygame.K_d] or keys[pygame.K_RIGHT]: dx = 1

        nx, ny = player[0] + dx, player[1] + dy
        if 0 <= nx < COLS and 0 <= ny < ROWS and maze[ny][nx] == 0:
            ghost2[:] = ghost1
            ghost1[:] = player
            player[:] = [nx, ny]
            last_move = now

    # ----- MONSTER MOVE -----
    if now - oldmove > MONSTER_SPEED:
        mdx, mdy = monster_ai.move(monster, player, maze)
        monster[0] += mdx
        monster[1] += mdy
        oldmove = now
        monstertrail.append((monster[0], monster[1]))

    # ----- GAME CONDITIONS -----
    if tuple(player) == exit_pos:
        won = True
        monster = 0
    if monster == player:
        running = False  # Player caught

    # ----- CAMERA -----
    target_x = player[0]*TILE_SIZE - SCREEN_WIDTH//2
    target_y = player[1]*TILE_SIZE - SCREEN_HEIGHT//2
    camera_x += (target_x - camera_x) * CAMERA_SPEED
    camera_y += (target_y - camera_y) * CAMERA_SPEED
    camera_x = max(0, min(camera_x, COLS*TILE_SIZE - SCREEN_WIDTH))
    camera_y = max(0, min(camera_y, ROWS*TILE_SIZE - SCREEN_HEIGHT))

    # ----- VISION FOLLOW -----
    target_vx = player[0] * TILE_SIZE
    target_vy = player[1] * TILE_SIZE
    vision_x += (target_vx - vision_x) * VISION_SMOOTH
    vision_y += (target_vy - vision_y) * VISION_SMOOTH

    # ----- DRAW -----
    screen.fill(BACKGROUND)
    draw_maze(camera_x, camera_y)
    draw_entities(camera_x, camera_y)
    draw_fog_of_war(camera_x, camera_y)
    draw_mute_button()
    draw_exit_button()

    if won:
        text = font.render("YOU WIN!", True, WIN)
        screen.blit(text, (SCREEN_WIDTH//2 - text.get_width()//2,
                           SCREEN_HEIGHT//2 - text.get_height()//2))

    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()