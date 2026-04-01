import pygame
import subprocess

# ---------------- INIT ----------------
pygame.init()
info = pygame.display.Info()
SCREEN_WIDTH, SCREEN_HEIGHT = info.current_w, info.current_h
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN)
pygame.display.set_caption("Maze Game Menu")
clock = pygame.time.Clock()
FPS = 60

# Larger fonts
title_font = pygame.font.SysFont(None, 120)
font = pygame.font.SysFont(None, 80)
small_font = pygame.font.SysFont(None, 50)

# ---------------- DEFAULT SETTINGS ----------------
DEFAULT_SETTINGS = {
    "Rows": 100,
    "Cols": 100,
    "Tile Size": 64,
    "Player Vision": 5, #if you want darkness adjust the Player Vision and Monster Vision to 5
    "Monster Vision": 0,#if you want the monster to not appear unless in player sight adjust Monster Vision to 0
    "Player Speed": 80,
    "Monster Speed": 40,
}

TOOLTIPS = {
    "Rows": "Number of rows in the maze",
    "Cols": "Number of columns in the maze",
    "Tile Size": "Pixel size of each tile",
    "Player Vision": "Radius around the player that is visible",
    "Monster Vision": "Radius around the monster that is visible",
    "Player Speed": "How fast the player moves (higher = faster)",
    "Monster Speed": "How fast the monster moves (higher = faster)",
}

MAIN_OPTIONS = ["Enter Game", "Settings", "Quit Game"]

# ---------------- DRAW FUNCTIONS ----------------
def draw_main_menu(selected):
    screen.fill((30, 30, 40))
    title_surface = title_font.render("Maze Game", True, (255, 255, 0))
    screen.blit(title_surface, (SCREEN_WIDTH//2 - title_surface.get_width()//2, 100))

    spacing = 100
    for i, option in enumerate(MAIN_OPTIONS):
        color = (255, 255, 0) if i == selected else (200, 200, 200)
        text_surface = font.render(option, True, color)
        screen.blit(text_surface, (SCREEN_WIDTH//2 - text_surface.get_width()//2, 300 + i*spacing))
    pygame.display.flip()


def main_menu():
    selected = 0
    running = True
    while running:
        draw_main_menu(selected)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    selected = (selected - 1) % len(MAIN_OPTIONS)
                elif event.key == pygame.K_DOWN:
                    selected = (selected + 1) % len(MAIN_OPTIONS)
                elif event.key == pygame.K_RETURN:
                    if MAIN_OPTIONS[selected] == "Enter Game":
                        running = False
                        return "play"
                    elif MAIN_OPTIONS[selected] == "Settings":
                        settings_menu()
                    elif MAIN_OPTIONS[selected] == "Quit Game":
                        pygame.quit()
                        exit()
        clock.tick(FPS)

# ---------------- SETTINGS MENU ----------------
def draw_settings_menu(selected, settings):
    screen.fill((30, 30, 40))
    title_surface = title_font.render("Settings", True, (255, 255, 0))
    screen.blit(title_surface, (SCREEN_WIDTH//2 , 50))

    keys = list(settings.keys()) + ["Return"]
    selected_key = keys[selected]
    tooltip = TOOLTIPS.get(selected_key, "Go back to main menu") if selected_key != "Return" else "Return to main menu"
    tooltip_surface = small_font.render(tooltip, True, (180, 180, 180))
    screen.blit(tooltip_surface, (SCREEN_WIDTH//2 , SCREEN_HEIGHT//2))  # Left tooltip

    # Right side: list of all settings
    x_right = SCREEN_WIDTH//16
    y_start = SCREEN_HEIGHT//16
    y_spacing = 120

    for i, key in enumerate(keys):
        color = (255, 255, 0) if i == selected else (200, 200, 200)
        if key == "Return":
            text_surface = font.render("Return", True, color)
        else:
            text_surface = font.render(f"{key}: {settings[key]}", True, color)
        screen.blit(text_surface, (x_right, y_start + i*y_spacing))

    pygame.display.flip()


def settings_menu():
    settings = DEFAULT_SETTINGS.copy()
    selected = 0
    keys = list(settings.keys()) + ["Return"]
    running = True

    while running:
        draw_settings_menu(selected, settings)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    if keys[selected] == "Return":
                        running = False
                elif event.key == pygame.K_UP:
                    selected = (selected - 1) % len(keys)
                elif event.key == pygame.K_DOWN:
                    selected = (selected + 1) % len(keys)
                elif event.key == pygame.K_LEFT:
                    if keys[selected] != "Return":
                        key = keys[selected]
                        settings[key] = max(1, settings[key]-1)
                        
                elif event.key == pygame.K_RIGHT:
                    if keys[selected] != "Return":
                        key = keys[selected]
                        settings[key] += 1

    # Save settings to config.py
    with open("config.py", "w") as f:
        for key, value in settings.items():
            name = key.upper().replace(" ", "_")
            f.write(f"{name} = {value}\n")


# ---------------- RUN ----------------
if __name__ == "__main__":
    action = main_menu()
    if action == "play":
        subprocess.call(["python", "game.py"])  # replace with your game file

