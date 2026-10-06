import pygame
import serial
import math
import time

# ============================================================
# ESP32 SETTINGS
# ============================================================

SERIAL_PORT = "COM3"
BAUD_RATE = 115200

# ============================================================
# WINDOW & RADAR DIMENSIONS
# ============================================================

WIDTH = 1200
HEIGHT = 700

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Ultrasonic Radar - Real-Time Response")
clock = pygame.time.Clock()

CENTER_X = WIDTH // 2
CENTER_Y = HEIGHT - 50

RADAR_RADIUS = 480
MAX_DISTANCE = 200.0  # Max distance in cm

# ============================================================
# FONTS & COLORS
# ============================================================

radar_font = pygame.font.SysFont("courier", 16, bold=True)
status_font = pygame.font.SysFont("courier", 20, bold=True)

DARK_BG = (20, 20, 20)
GRID_GREEN = (30, 200, 60)
TEXT_GREEN = (30, 230, 70)
SWEEP_GREEN = (30, 255, 80)
RED_ALERT = (240, 30, 30)

# ============================================================
# SERIAL CONNECTION
# ============================================================

try:
    esp32 = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=0.05)
    time.sleep(1.5)
    print("ESP32 Connected on", SERIAL_PORT)
except Exception as e:
    esp32 = None
    print("Serial Connection Error:", e)

# ============================================================
# GLOBAL VARIABLES
# ============================================================

distance = None
sweep_angle = 0
sweep_dir = 1

# ============================================================
# HELPER FUNCTIONS
# ============================================================

def read_sensor():
    global distance
    if esp32 is None:
        return

    try:
        while esp32.in_waiting:
            line = esp32.readline().decode("utf-8", errors="ignore").strip()
            if not line:
                continue
            val = float(line)
            if 2 <= val <= MAX_DISTANCE:
                distance = val
            else:
                distance = None
    except (ValueError, serial.SerialException):
        pass

def polar_to_screen(angle_deg, radius):
    rad = math.radians(angle_deg)
    x = CENTER_X + math.cos(rad) * radius
    y = CENTER_Y - math.sin(rad) * radius
    return int(x), int(y)

# ============================================================
# DRAW RADAR GRID
# ============================================================

def draw_radar_grid():
    # 1. Concentric Arcs (Upward)
    for i in range(1, 5):
        r = RADAR_RADIUS * (i / 4.0)
        rect = pygame.Rect(CENTER_X - r, CENTER_Y - r, r * 2, r * 2)
        pygame.draw.arc(screen, GRID_GREEN, rect, 0, math.pi, 2)

    # 2. Radial Lines & Degree Markings
    for deg in [30, 60, 90, 120, 150]:
        end_pt = polar_to_screen(deg, RADAR_RADIUS)
        pygame.draw.line(screen, GRID_GREEN, (CENTER_X, CENTER_Y), end_pt, 2)

        lbl_pt = polar_to_screen(deg, RADAR_RADIUS + 22)
        lbl_text = radar_font.render(f"{deg}°", True, TEXT_GREEN)
        rect_text = lbl_text.get_rect(center=lbl_pt)
        screen.blit(lbl_text, rect_text)

    # 3. Outer Rim Arc
    outer_rect = pygame.Rect(
        CENTER_X - RADAR_RADIUS,
        CENTER_Y - RADAR_RADIUS,
        RADAR_RADIUS * 2,
        RADAR_RADIUS * 2
    )
    pygame.draw.arc(screen, GRID_GREEN, outer_rect, 0, math.pi, 3)

    # 4. Baseline
    pygame.draw.line(
        screen, GRID_GREEN,
        (CENTER_X - RADAR_RADIUS, CENTER_Y),
        (CENTER_X + RADAR_RADIUS, CENTER_Y),
        2
    )

    # 5. Distance Markings along Baseline
    for dist_val in [50, 100, 150, 200]:
        r = (dist_val / MAX_DISTANCE) * RADAR_RADIUS
        x_pos = CENTER_X + r - 20
        y_pos = CENTER_Y - 22
        txt = radar_font.render(f"{dist_val}cm", True, TEXT_GREEN)
        screen.blit(txt, (x_pos, y_pos))

# ============================================================
# LIVE DYNAMIC SWEEP BEAM
# ============================================================

def draw_sweep_and_obstacles():
    max_pt = polar_to_screen(sweep_angle, RADAR_RADIUS)

    # Check if object is currently within range
    if distance is not None and distance < MAX_DISTANCE:
        d_px = (distance / MAX_DISTANCE) * RADAR_RADIUS
        hit_pt = polar_to_screen(sweep_angle, d_px)

        # Green beam up to object distance
        pygame.draw.line(screen, SWEEP_GREEN, (CENTER_X, CENTER_Y), hit_pt, 3)
        # Red warning beam past the object
        pygame.draw.line(screen, RED_ALERT, hit_pt, max_pt, 3)

        # Highlight detected point blip
        pygame.draw.circle(screen, RED_ALERT, hit_pt, 6)
    else:
        # Full green sweep line when area is clear
        pygame.draw.line(screen, SWEEP_GREEN, (CENTER_X, CENTER_Y), max_pt, 3)

# ============================================================
# STATUS BAR
# ============================================================

def draw_status_bar():
    pygame.draw.line(screen, GRID_GREEN, (0, HEIGHT - 35), (WIDTH, HEIGHT - 35), 2)

    if distance is not None and distance < MAX_DISTANCE:
        obj_str = "In Range"
        dist_str = f"{distance:.1f} cm"
    else:
        obj_str = "Out of Range"
        dist_str = "---"

    ang_str = f"{int(sweep_angle)}°"

    obj_txt = status_font.render(f"Object: {obj_str}", True, TEXT_GREEN)
    ang_txt = status_font.render(f"Angle: {ang_str}", True, TEXT_GREEN)
    dist_txt = status_font.render(f"Distance: {dist_str}", True, TEXT_GREEN)

    screen.blit(obj_txt, (30, HEIGHT - 25))
    screen.blit(ang_txt, (WIDTH // 2 - 60, HEIGHT - 25))
    screen.blit(dist_txt, (WIDTH - 260, HEIGHT - 25))

# ============================================================
# MAIN LOOP
# ============================================================

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    read_sensor()

    # Smooth sweep motion back & forth
    sweep_angle += 1.5 * sweep_dir
    if sweep_angle >= 180:
        sweep_angle = 180
        sweep_dir = -1
    elif sweep_angle <= 0:
        sweep_angle = 0
        sweep_dir = 1

    screen.fill(DARK_BG)
    draw_radar_grid()
    draw_sweep_and_obstacles()
    draw_status_bar()

    pygame.display.flip()
    clock.tick(60)

if esp32 is not None:
    esp32.close()
pygame.quit()
