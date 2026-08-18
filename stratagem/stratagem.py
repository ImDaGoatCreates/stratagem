import os
os.environ["SDL_TOUCH_MOUSE_EVENTS"] = "0"
os.environ["SDL_MOUSE_TOUCH_EVENTS"] = "0"

import pygame
import sys
import time
import random

pygame.init()
pygame.mixer.init()

# 🔊 Allow multiple simultaneous sounds
pygame.mixer.set_num_channels(16)

# -----------------------------
# RESOLUTION SYSTEM
# -----------------------------
VIRTUAL_WIDTH = 800
VIRTUAL_HEIGHT = 480

screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
REAL_WIDTH, REAL_HEIGHT = screen.get_size()

surface = pygame.Surface((VIRTUAL_WIDTH, VIRTUAL_HEIGHT))

WIDTH = VIRTUAL_WIDTH
HEIGHT = VIRTUAL_HEIGHT

pygame.mouse.set_visible(True)

# -----------------------------
# PATHS
# -----------------------------
IMG_PATH = "images"
SOUND_PATH = "sounds"

# -----------------------------
# COLORS
# -----------------------------
BG = (5, 10, 15)
BLUE = (80, 150, 255)
WHITE = (255, 255, 255)

# -----------------------------
# FONT
# -----------------------------
font = pygame.font.SysFont("Arial", int(HEIGHT * 0.08))

# -----------------------------
# IMAGES
# -----------------------------
def scale_image(img):
    max_w = WIDTH * 0.85
    max_h = HEIGHT * 0.75
    w, h = img.get_size()
    scale = min(max_w / w, max_h / h)
    return pygame.transform.scale(img, (int(w * scale), int(h * scale)))

images = {
    "500KG": pygame.image.load(os.path.join(IMG_PATH, "500kg.jpg")),
    "MG": pygame.image.load(os.path.join(IMG_PATH, "MG.jpg")),
    "FRV": pygame.image.load(os.path.join(IMG_PATH, "FRV.jpg")),
    "MINES": pygame.image.load(os.path.join(IMG_PATH, "mines.jpg")),
    "REINFORCE": pygame.image.load(os.path.join(IMG_PATH, "reinforce.jpg")),
    "RESUPPLY": pygame.image.load(os.path.join(IMG_PATH, "resupply.jpg")),
    "SOS": pygame.image.load(os.path.join(IMG_PATH, "SOS.jpg")),
    "HELLBOMB": pygame.image.load(os.path.join(IMG_PATH, "HB.jpg")),
}

for k in images:
    images[k] = scale_image(images[k])

# -----------------------------
# SOUNDS
# -----------------------------
def load(name):
    return pygame.mixer.Sound(os.path.join(SOUND_PATH, name))

all_files = os.listdir(SOUND_PATH)

click_sound = load("stratagem_sound.mp3")

eagle_sounds = [load(f) for f in all_files if f.startswith("Eagle 1")]

mg_sounds = [
    load("Super Destroyer - Sending down a support weapon.mp3"),
    load("Super Destroyer - Deploying support weapon.mp3"),
]

hellbomb_sounds = [
    load("Super Destroyer - Hellbomb request approved, deploying now.mp3"),
    load("Super Destroyer - Hellbomb request approved, on it's way now..mp3"),
]

reinforce_sounds = [
    load("Super Destroyer - Request approved, reinforcements have been launched.mp3"),
    load("Super Destroyer - Request approved, reinforcements on the way.mp3"),
]

resupply_sounds = [
    load("Super Destroyer - Deploying equipment package.mp3"),
    load("Super Destroyer - Deploying equipment package 2.mp3"),
]

mines_sound = load("Super Destroyer - Deploying minefield.mp3")

# Voice channel (separate from clicks)
voice_channel = pygame.mixer.Channel(1)

pending_sound = None
sound_timer = 0
SOUND_DELAY = 0.5

def trigger_sound(name):
    global pending_sound, sound_timer
    pending_sound = name
    sound_timer = time.time()

# -----------------------------
# STRATAGEMS
# -----------------------------
STRATAGEMS = {
    "500KG": ["UP","RIGHT","DOWN","DOWN","DOWN"],
    "MG": ["DOWN","LEFT","DOWN","UP","RIGHT"],
    "FRV": ["LEFT","DOWN","LEFT","LEFT","DOWN","UP","RIGHT"],
    "MINES": ["DOWN","LEFT","LEFT","DOWN"],
    "REINFORCE": ["UP","DOWN","RIGHT","LEFT","UP"],
    "RESUPPLY": ["DOWN","DOWN","UP","RIGHT"],
    "SOS": ["UP","DOWN","RIGHT","LEFT"],
    "HELLBOMB": ["DOWN","UP","LEFT","DOWN","UP","RIGHT","DOWN","UP"],
}

PREFIX_TIMEOUT = 1.0
RESET_TIMEOUT = 3.0

# -----------------------------
# LAYOUT
# -----------------------------
size = int(HEIGHT * 0.20)
spacing_x = int(WIDTH * 0.38)
spacing_y = int(HEIGHT * 0.24)

cx = WIDTH // 2
cy = HEIGHT // 2 + int(HEIGHT * 0.05)

buttons = {
    "UP": pygame.Rect(cx - size//2, int(cy - spacing_y - size//2), size, size),
    "LEFT": pygame.Rect(cx - spacing_x - size//2, int(cy - size//2), size, size),
    "RIGHT": pygame.Rect(cx + spacing_x - size//2, int(cy - size//2), size, size),
    "DOWN": pygame.Rect(cx - size//2, int(cy + spacing_y*1.4 - size//2), size, size),
}

pressed = {k: False for k in buttons}

# -----------------------------
# STATE
# -----------------------------
input_sequence = []
last_input_time = 0
prefix_timer_start = 0
pending_stratagem = None
show_image = None
image_timer = 0

# -----------------------------
# MATCHING
# -----------------------------
def get_exact_match():
    for name, seq in STRATAGEMS.items():
        if input_sequence == seq:
            return name
    return None

def is_prefix_of_longer(seq):
    return any(seq != other and seq == other[:len(seq)] for other in STRATAGEMS.values())

# -----------------------------
# DRAW
# -----------------------------
def draw_arrow(direction, rect, color):
    cx, cy, w = rect.centerx, rect.centery, rect.width
    shaft, head = w*0.35, w*0.5

    if direction=="UP":
        pts=[(cx-shaft/2,cy+shaft),(cx-shaft/2,cy),(cx-w*0.45,cy),(cx,cy-head),
             (cx+w*0.45,cy),(cx+shaft/2,cy),(cx+shaft/2,cy+shaft)]
    elif direction=="DOWN":
        pts=[(cx-shaft/2,cy-shaft),(cx-shaft/2,cy),(cx-w*0.45,cy),(cx,cy+head),
             (cx+w*0.45,cy),(cx+shaft/2,cy),(cx+shaft/2,cy-shaft)]
    elif direction=="LEFT":
        pts=[(cx+shaft,cy-shaft/2),(cx,cy-shaft/2),(cx,cy-w*0.45),(cx-head,cy),
             (cx,cy+w*0.45),(cx,cy+shaft/2),(cx+shaft,cy+shaft/2)]
    elif direction=="RIGHT":
        pts=[(cx-shaft,cy-shaft/2),(cx,cy-shaft/2),(cx,cy-w*0.45),(cx+head,cy),
             (cx,cy+w*0.45),(cx,cy+shaft/2),(cx-shaft,cy+shaft/2)]

    pygame.draw.polygon(surface, color, pts)

def draw_input():
    arrows = {"UP":"↑","DOWN":"↓","LEFT":"←","RIGHT":"→"}
    txt = " ".join(arrows[i] for i in input_sequence)
    surf = font.render(txt, True, WHITE)
    surface.blit(surf, (WIDTH//2 - surf.get_width()//2, int(HEIGHT*0.05)))

# -----------------------------
# MAIN LOOP
# -----------------------------
while True:
    surface.fill(BG)
    now = time.time()

    # delayed voice playback
    if pending_sound and (now - sound_timer > SOUND_DELAY):
        voice_channel.stop()

        if pending_sound == "500KG" and eagle_sounds:
            voice_channel.play(random.choice(eagle_sounds))
        elif pending_sound == "MG":
            voice_channel.play(random.choice(mg_sounds))
        elif pending_sound == "HELLBOMB":
            voice_channel.play(random.choice(hellbomb_sounds))
        elif pending_sound == "REINFORCE":
            voice_channel.play(random.choice(reinforce_sounds))
        elif pending_sound == "RESUPPLY":
            voice_channel.play(random.choice(resupply_sounds))
        elif pending_sound == "MINES":
            voice_channel.play(mines_sound)

        pending_sound = None

    # prefix system
    if pending_stratagem and now - prefix_timer_start > PREFIX_TIMEOUT:
        show_image = pending_stratagem
        image_timer = now
        trigger_sound(pending_stratagem)
        input_sequence.clear()
        pending_stratagem = None

    # reset
    if input_sequence and now - last_input_time > RESET_TIMEOUT:
        input_sequence.clear()
        pending_stratagem = None

    if show_image:
        img = images[show_image]
        surface.blit(img, (WIDTH//2 - img.get_width()//2, HEIGHT//2 - img.get_height()//2))
        if now - image_timer > 5:
            show_image = None
    else:
        for d,r in buttons.items():
            draw_arrow(d, r, WHITE if pressed[d] else BLUE)
        draw_input()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit(); sys.exit()

        if event.type == pygame.MOUSEBUTTONDOWN:
            x, y = pygame.mouse.get_pos()

            vx = int(x * WIDTH / REAL_WIDTH)
            vy = int(y * HEIGHT / REAL_HEIGHT)

            for d,r in buttons.items():
                if r.collidepoint((vx,vy)):
                    pressed[d]=True
                    input_sequence.append(d)

                    last_input_time=now
                    prefix_timer_start=now
                    pending_stratagem=None

                    # 🔊 IMPORTANT: this now allows overlap
                    click_sound.play()

                    result = get_exact_match()
                    if result:
                        if is_prefix_of_longer(input_sequence):
                            pending_stratagem = result
                        else:
                            show_image=result
                            image_timer=now
                            trigger_sound(result)
                            input_sequence.clear()

        if event.type == pygame.MOUSEBUTTONUP:
            for k in pressed:
                pressed[k]=False

    scaled = pygame.transform.smoothscale(surface, (REAL_WIDTH, REAL_HEIGHT))
    screen.blit(scaled, (0, 0))
    pygame.display.flip()