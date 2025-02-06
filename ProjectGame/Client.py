import socket
import math
import random
import pygame
import os
import time
import re

WIDTH, HEIGHT = 800, 600
FPS = 60
GRAVITY = 0.5
FLAP_POWER = -9
PIPE_SPEED = 4
PIPE_GAP = 200
BIRD_ANIMATION_TIME = 150
PIPE_SCALE = 0.4
CAMERA_SPEED = 5

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()
font = pygame.font.Font(None, 36)
big_font = pygame.font.Font(None, 72)

bird_imgs = [pygame.transform.scale(pygame.image.load(f'bird{i}.png'), (40, 30)) for i in range(1, 4)]
background_img = pygame.image.load('background.jpg')
background_img = pygame.transform.scale(background_img, (WIDTH, HEIGHT))


class Bird:
    def __init__(self):
        self.x = 100
        self.y = HEIGHT // 2
        self.velocity = 0
        self.images = bird_imgs
        self.current_image = 0
        self.animation_time = BIRD_ANIMATION_TIME
        self.last_update = pygame.time.get_ticks()
        self.rect = self.images[0].get_rect(center=(self.x, self.y))

    def update(self):
        now = pygame.time.get_ticks()
        if now - self.last_update > self.animation_time:
            self.last_update = now
            self.current_image = (self.current_image + 1) % len(self.images)

        self.velocity += GRAVITY
        self.y += self.velocity
        self.rect.center = (self.x, self.y)

    def flap(self):
        self.velocity = FLAP_POWER

    def draw(self, surface):
        surface.blit(self.images[self.current_image], self.rect)


class Pipe:
    def __init__(self, x, height, rotated=False):
        self.x = x
        self.height = height
        self.passed = False
        self.rotated = rotated
        self.update_rect()

    def update_rect(self):
        if self.rotated:
            self.rect = pygame.Rect(self.x - 50, 0, 100, self.height)
        else:
            self.rect = pygame.Rect(self.x - 50, HEIGHT - self.height, 100, self.height)

    def update(self):
        self.x -= PIPE_SPEED
        self.update_rect()

    def draw(self, surface):
        color = (128, 128, 128)
        pygame.draw.rect(surface, color, self.rect)

        # Окна на башне
        window_color = (200, 200, 200)
        window_width = 15
        window_height = 20
        window_gap = 10

        if self.rotated:
            for i in range(10, self.height - 10, window_height + window_gap):
                for j in range(10, 90, window_width + window_gap):
                    pygame.draw.rect(
                        surface,
                        window_color,
                        (self.rect.x + j, self.rect.y + i, window_width, window_height),
                    )
        else:
            for i in range(10, self.height - 10, window_height + window_gap):
                for j in range(10, 90, window_width + window_gap):
                    pygame.draw.rect(
                        surface,
                        window_color,
                        (self.rect.x + j, self.rect.y + i, window_width, window_height),
                    )

    def off_screen(self):
        return self.x < -100


def game_over_animation(score, highscore):
    if score > highscore:
        text = big_font.render("NEW RECORD!", True, (0, 255, 0))

        score_text = font.render(f"Score: {score}", True, (0, 255, 0))
    else:
        text = big_font.render("GAME OVER", True, (255, 0, 0))

        score_text = font.render(f"Score: {score} | Best: {highscore}", True, (255, 0, 0))

    y = -100

    velocity = 0

    gravity = 0.7

    damping = 0.8

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return

        velocity += gravity
        y += velocity

        if y > HEIGHT // 2 - 50:
            y = HEIGHT // 2 - 50
            velocity = -velocity * damping
            if abs(velocity) < 1:
                break

        screen.blit(background_img, (0, 0))
        screen.blit(text, (WIDTH // 2 - text.get_width() // 2, int(y)))
        screen.blit(score_text, (WIDTH // 2 - score_text.get_width() // 2, int(y) + 70))
        pygame.display.update()
        clock.tick(FPS)


def infinite_mode():
    bird = Bird()
    pipes = []
    spawn_pipe = pygame.USEREVENT + 1
    pygame.time.set_timer(spawn_pipe, 1500)
    score = 0
    time_elapsed = 0
    global PIPE_SPEED, PIPE_GAP
    highscore = send_data_to_server(open('User_data.txt', 'r').read()[:-1] + "3")
    print(highscore)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    bird.flap()
            if event.type == spawn_pipe:
                height = random.randint(100, HEIGHT - 300)
                pipes.append(Pipe(WIDTH + 100, height, random.choice([True, False])))

        bird.update()

        if bird.rect.top < 0 or bird.rect.bottom > HEIGHT:
            if score > int(highscore):
                send_data_to_server(open('User_data.txt', 'r').read()[:-1] + "4;" + str(score))
            game_over_animation(score, int(highscore))
            running = False

        time_elapsed += 1 / FPS
        if time_elapsed >= 10:
            time_elapsed = 0
            PIPE_SPEED += 0.5
            PIPE_GAP = max(100, PIPE_GAP - 10)

        pipes = [p for p in pipes if not p.off_screen()]
        for pipe in pipes:
            pipe.update()
            if not pipe.passed and pipe.x < bird.x:
                score += 1
                pipe.passed = True

            if bird.rect.colliderect(pipe.rect):
                if score > int(highscore):
                    send_data_to_server(open('User_data.txt', 'r').read()[:-1] + "4;" + str(score))
                game_over_animation(score, int(highscore))
                running = False

        screen.blit(background_img, (0, 0))
        bird.draw(screen)
        for pipe in pipes:
            pipe.draw(screen)

        score_text = font.render(f"Счет: {score}", True, (255, 255, 255))
        screen.blit(score_text, (10, 10))

        pygame.display.update()
        clock.tick(FPS)


def you_win_animation():
    text = big_font.render("YOU WIN!", True, (0, 255, 0))
    y = -100
    velocity = 0
    gravity = 0.7
    damping = 0.8

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return

        velocity += gravity
        y += velocity

        if y > HEIGHT // 2 - 50:
            y = HEIGHT // 2 - 50
            velocity = -velocity * damping
            if abs(velocity) < 1:
                break

        screen.blit(background_img, (0, 0))
        screen.blit(text, (WIDTH // 2 - text.get_width() // 2, int(y)))
        pygame.display.update()
        clock.tick(FPS)


def load_level_from_file(filename):
    pipes = []
    try:
        with open(filename, 'r') as f:
            lines = [line.strip() for line in f.readlines()]
            column_spacing = 50
            start_x = WIDTH + 100

            for col_idx in range(len(lines[0])):
                column_x = start_x + col_idx * column_spacing
                found_pipe = False

                # Поиск первой звездочки сверху вниз
                for row_idx, row in enumerate(lines):
                    if row[col_idx] == '*':
                        pipe_height = (len(lines) - row_idx) * 30
                        pipes.append(Pipe(column_x, pipe_height, False))  # Нижняя труба
                        pipes.append(Pipe(column_x, HEIGHT - pipe_height - 150, True))  # Верхняя труба
                        found_pipe = True
                        break

    except Exception as e:
        print(f"Ошибка загрузки уровня: {e}")
    return pipes


def play_level(filename):
    bird = Bird()
    pipes = load_level_from_file(filename)
    running = True
    passed_all = False

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                bird.flap()

        bird.update()

        all_passed = all(pipe.passed for pipe in pipes)
        if all_passed and not passed_all:
            passed_all = True
            you_win_animation()
            running = False

        if bird.rect.top < 0 or bird.rect.bottom > HEIGHT:
            game_over_animation(0, 0)
            running = False

        for pipe in pipes:
            pipe.update()
            if bird.rect.colliderect(pipe.rect):
                game_over_animation(0, 0)
                running = False

            if not pipe.passed and pipe.x < bird.x:
                pipe.passed = True

        screen.blit(background_img, (0, 0))
        bird.draw(screen)
        for pipe in pipes:
            pipe.draw(screen)
        pygame.display.update()
        clock.tick(FPS)


def level_selection():
    level_files = []
    for filename in os.listdir():
        if filename.startswith('level') and filename.endswith('.txt'):
            match = re.match(r'level(\d+)\.txt', filename)
            if match:
                level_num = int(match.group(1))
                level_files.append((level_num, filename))

    level_files.sort()

    buttons = []
    for i, (level_num, filename) in enumerate(level_files):
        buttons.append({
            "rect": pygame.Rect(100, 100 + i * 70, 600, 60),
            "text": f"Уровень {level_num}",
            "filename": filename
        })

    while True:
        screen.blit(background_img, (0, 0))

        for btn in buttons:
            draw_button(btn["text"], btn["rect"].x, btn["rect"].y,
                        btn["rect"].width, btn["rect"].height, (200, 200, 200))

        back_btn = draw_button("Назад", 10, HEIGHT - 60, 100, 50, (200, 200, 200))

        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()

            if event.type == pygame.MOUSEBUTTONDOWN:
                pos = pygame.mouse.get_pos()
                for btn in buttons:
                    if btn["rect"].collidepoint(pos):
                        play_level(btn["filename"])
                if back_btn.collidepoint(pos):
                    return


def draw_button(text, x, y, width, height, color):
    rect = pygame.Rect(x, y, width, height)
    pygame.draw.rect(screen, color, rect)
    text_surf = font.render(text, True, (0, 0, 0))
    screen.blit(text_surf, (x + 10, y + 10))
    return rect


def send_data_to_server(message, host='127.0.0.1', port=65432):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((host, port))
            s.sendall(message.encode())
            return s.recv(1024).decode()
    except:
        return "False"


def splash_screen():
    start_time = pygame.time.get_ticks()
    alpha = 0
    loading_progress = 0

    title = big_font.render("Bird", True, (255, 255, 255))
    title_rect = title.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 50))

    while True:
        current_time = pygame.time.get_ticks()
        elapsed = current_time - start_time

        if elapsed < 2000:
            alpha = min(255, alpha + 5)
        else:
            loading_progress = min(100, (elapsed - 2000) / 30)

        if elapsed > 5000:
            break

        screen.fill((0, 0, 0))

        title.set_alpha(alpha)
        screen.blit(title, title_rect)

        pygame.draw.rect(screen, (255, 255, 255), (WIDTH // 2 - 100, HEIGHT // 2 + 50, 200, 20), 2)
        pygame.draw.rect(screen, (255, 255, 255), (WIDTH // 2 - 98, HEIGHT // 2 + 52, loading_progress * 1.96, 16))

        pygame.display.flip()
        clock.tick(30)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()


def level_editor():
    grid = [['.' for _ in range(20)] for _ in range(10)]  # 10x20 grid
    cell_size = 30
    grid_offset_x = 50
    grid_offset_y = 100
    selected_char = '*'
    filename = ""
    input_active = False
    error_message = ""

    existing_levels = [int(f[5:-4]) for f in os.listdir() if f.startswith('level') and f.endswith('.txt')]
    next_level = max(existing_levels) + 1 if existing_levels else 1

    running = True
    while running:
        screen.blit(background_img, (0, 0))

        for y in range(10):
            for x in range(20):
                rect = pygame.Rect(
                    grid_offset_x + x * cell_size,
                    grid_offset_y + y * cell_size,
                    cell_size - 2,
                    cell_size - 2
                )
                color = (100, 100, 200) if grid[y][x] == '*' else (200, 200, 200)
                pygame.draw.rect(screen, color, rect)
                pygame.draw.rect(screen, (0, 0, 0), rect, 1)

        save_btn = draw_button("Сохранить", 400, 50, 150, 40, (100, 200, 100))
        back_btn = draw_button("Назад", WIDTH - 150, HEIGHT - 60, 100, 40, (200, 100, 100))

        info_text = font.render("ЛКМ - поставить *, ПКМ - очистить", True, (255, 255, 255))
        screen.blit(info_text, (50, HEIGHT - 60))

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()

            if event.type == pygame.MOUSEBUTTONDOWN:
                x, y = pygame.mouse.get_pos()
                if grid_offset_x <= x < grid_offset_x + 20 * cell_size and grid_offset_y <= y < grid_offset_y + 10 * cell_size:
                    grid_x = (x - grid_offset_x) // cell_size
                    grid_y = (y - grid_offset_y) // cell_size
                    if event.button == 1:  # ЛКМ
                        grid[grid_y][grid_x] = '*'
                    elif event.button == 3:  # ПКМ
                        grid[grid_y][grid_x] = '.'
                if save_btn.collidepoint(event.pos):
                    has_pipes = any('*' in row for row in grid)
                    if not has_pipes:
                        error_message = "Добавьте хотя бы одну трубу!"
                    else:
                        with open(f'level{next_level}.txt', 'w') as f:
                            for row in grid:
                                f.write(''.join(row) + '\n')
                        running = False

                if back_btn.collidepoint(event.pos):
                    running = False

        clock.tick(FPS)


def auth_system():
    current_screen = "login"
    username_text = ''
    password_text = ''
    active_input = None
    error_message = ''

    username_rect = pygame.Rect(300, 200, 200, 32)
    password_rect = pygame.Rect(300, 300, 200, 32)
    if os.path.exists('User_data.txt'):
        if send_data_to_server(open('User_data.txt', 'r').read()) == "True":
            splash_screen()
            main_menu()
            return
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()

            if event.type == pygame.MOUSEBUTTONDOWN:
                if username_rect.collidepoint(event.pos):
                    active_input = "username"
                elif password_rect.collidepoint(event.pos):
                    active_input = "password"
                else:
                    active_input = None

                mouse_pos = pygame.mouse.get_pos()
                if pygame.Rect(300, 400, 200, 40).collidepoint(mouse_pos):
                    if username_text and password_text:
                        if send_data_to_server(f"{username_text};{password_text};1") == "True":
                            with open('User_data.txt', 'w') as f:
                                f.write(f"{username_text};{password_text};2")
                            splash_screen()
                            main_menu()
                            return
                        else:
                            error_message = "User exists!"
                    else:
                        error_message = "Fill all fields!"

                elif pygame.Rect(300, 450, 200, 40).collidepoint(mouse_pos):
                    if username_text and password_text:
                        if send_data_to_server(f"{username_text};{password_text};2") == "True":
                            with open('User_data.txt', 'w') as f:
                                f.write(f"{username_text};{password_text};2")
                            splash_screen()
                            main_menu()
                            return
                        else:
                            error_message = "Invalid credentials!"
                    else:
                        error_message = "Fill all fields!"

            if event.type == pygame.KEYDOWN and active_input:
                if event.key == pygame.K_BACKSPACE:
                    if active_input == "username":
                        username_text = username_text[:-1]
                    else:
                        password_text = password_text[:-1]
                else:
                    if active_input == "username":
                        username_text += event.unicode
                    else:
                        password_text += event.unicode

        screen.fill((255, 255, 255))

        pygame.draw.rect(screen, (0, 0, 255) if active_input == "username" else (200, 200, 200), username_rect)
        pygame.draw.rect(screen, (0, 0, 255) if active_input == "password" else (200, 200, 200), password_rect)

        screen.blit(font.render("Username:", True, (0, 0, 0)), (100, 200))
        screen.blit(font.render("Password:", True, (0, 0, 0)), (100, 300))

        screen.blit(font.render(username_text, True, (0, 0, 0)), (username_rect.x + 5, username_rect.y + 5))
        screen.blit(font.render('*' * len(password_text), True, (0, 0, 0)), (password_rect.x + 5, password_rect.y + 5))

        pygame.draw.rect(screen, (200, 200, 200), (300, 400, 200, 40))
        screen.blit(font.render("Register", True, (0, 0, 0)), (360, 410))

        pygame.draw.rect(screen, (200, 200, 200), (300, 450, 200, 40))
        screen.blit(font.render("Login", True, (0, 0, 0)), (370, 460))

        if error_message:
            screen.blit(font.render(error_message, True, (255, 0, 0)), (300, 500))

        pygame.display.update()
        clock.tick(30)


def instruction_screen():
    lines = [
        "Инструкция к игре:",
        "Управление:",
        "- Пробел: прыжок птички",
        "",
        "Правила игры:",
        "1. В бесконечном режиме:",
        "- Пролетайте между трубами",
        "- Сложность растет со временем",
        "- Чем дальше пролетите, тем лучше!",
        "2. В уровнях:",
        "- Пройдите все препятствия",
        "- Достигните финишной точки",
        "",
        "Создавайте свои уровни в редакторе:",
        "Нажимайте на квадраты, которые означают колонны",
        "Когда всё готово - нажимайте сохранить и в уровнях играйте в него"
    ]

    while True:
        screen.blit(background_img, (0, 0))

        y = 50
        for line in lines:
            text = font.render(line, True, "black")
            screen.blit(text, (50, y))
            y += 25

        back_btn = draw_button("Назад", WIDTH // 2 - 50, HEIGHT - 80, 100, 50, (200, 200, 200))
        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if back_btn.collidepoint(event.pos):
                    return
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return


def main_menu():
    buttons = [
        {"text": "Уровни", "action": "levels"},
        {"text": "Бесконечный режим", "action": "infinite"},
        {"text": "Редактор уровней", "action": "editor"},
        {"text": "Инструкция", "action": "instructions"}  # Новая кнопка
    ]

    while True:
        screen.blit(background_img, (0, 0))

        # Отрисовка кнопок
        btn_rects = []
        y = 200
        for btn in buttons:
            rect = draw_button(btn["text"], 280, y, 275, 50, (200, 200, 200))
            btn_rects.append((rect, btn["action"]))
            y += 70

        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()

            if event.type == pygame.MOUSEBUTTONDOWN:
                pos = pygame.mouse.get_pos()
                for rect, action in btn_rects:
                    if rect.collidepoint(pos):
                        if action == "levels":
                            level_selection()
                        elif action == "infinite":
                            infinite_mode()
                        elif action == "editor":
                            level_editor()
                        elif action == "instructions":
                            instruction_screen()


if __name__ == "__main__":
    auth_system()
    pygame.quit()