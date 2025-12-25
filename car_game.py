#                                           hello guys
#                          this is a project which we make a 2d car racing game 

#                                         (PYTHON VERSION)

#                                made by = tate42hadi   &    satouro0
import pygame
import math
import random
import sys

# --- Configuration ---
SCREEN_WIDTH = 2000
SCREEN_HEIGHT = 1400
FPS = 60

# Set this lower to zoom out, higher to zoom in
ZOOM = 0.4 

# Colors (R, G, B)
COLOR_BG = (10, 10, 15)
COLOR_GRID = (30, 30, 40)
COLOR_NEON_BLUE = (0, 243, 255)
COLOR_NEON_PINK = (255, 0, 85)
COLOR_NEON_YELLOW = (255, 230, 0)
COLOR_TEXT = (255, 255, 255)

# Physics
ACCELERATION = 0.25
MAX_SPEED = 14.0
FRICTION = 0.96
OFFROAD_DRAG = 0.85
TURN_SPEED = 4.0

# --- Helper Classes for Visuals ---

class GlowSprite:
    """Pre-renders a glowing circle to improve performance"""
    def __init__(self, radius, color):
        self.base_radius = radius
        self.color = color
        self.surface = pygame.Surface((radius*2, radius*2), pygame.SRCALPHA)
        self.render_glow()

    def render_glow(self):
        # Create a radial gradient for neon effect
        for r in range(self.base_radius, 0, -1):
            alpha = int((1 - (r / self.base_radius)) * 100) 
            pygame.draw.circle(self.surface, (*self.color, alpha), (self.base_radius, self.base_radius), r)
        
        # Solid center
        pygame.draw.circle(self.surface, (*self.color, 255), (self.base_radius, self.base_radius), 2)

    def draw(self, target_surface, pos, scale=1.0):
        # Apply both the global ZOOM and any specific sprite scale
        final_scale = scale * ZOOM
        if final_scale != 1.0:
            size = int(self.base_radius * 2 * final_scale)
            if size < 1: size = 1
            scaled = pygame.transform.scale(self.surface, (size, size))
            target_surface.blit(scaled, (pos[0] - size//2, pos[1] - size//2), special_flags=pygame.BLEND_ADD)
        else:
            target_surface.blit(self.surface, (pos[0] - self.base_radius, pos[1] - self.base_radius), special_flags=pygame.BLEND_ADD)

class Particle:
    def __init__(self, x, y, color, life, size_decay=0.1):
        self.x = x
        self.y = y
        self.color = color
        self.life = life
        self.max_life = life
        self.size = random.uniform(3, 6)
        self.decay = size_decay
        
        angle = random.uniform(0, 6.28)
        speed = random.uniform(0.5, 2)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.life -= 1
        self.size -= self.decay

    def draw(self, surface, camera_center):
        if self.life > 0 and self.size > 0:
            screen_x = (self.x - camera_center[0]) * ZOOM + SCREEN_WIDTH / 2
            screen_y = (self.y - camera_center[1]) * ZOOM + SCREEN_HEIGHT / 2
            
            scaled_size = int(self.size * ZOOM)
            if scaled_size < 1: scaled_size = 1
            
            alpha = int((self.life / self.max_life) * 255)
            s = pygame.Surface((scaled_size*2, scaled_size*2), pygame.SRCALPHA)
            pygame.draw.circle(s, (*self.color, alpha), (scaled_size, scaled_size), scaled_size)
            
            surface.blit(s, (screen_x - scaled_size, screen_y - scaled_size), special_flags=pygame.BLEND_ADD)

# --- Game Objects ---

class Camera:
    def __init__(self):
        self.center = [0, 0]

    def update(self, target_x, target_y):
        # Smooth follow (Lerp)
        self.center[0] += (target_x - self.center[0]) * 0.1
        self.center[1] += (target_y - self.center[1]) * 0.1

class Track:
    def __init__(self):
        # World Coordinates
        self.outer_rect = pygame.Rect(-500, -500, 2000, 2000)
        self.inner_rect = pygame.Rect(-200, -200, 1400, 1400)
        
        # Checkered flag area
        self.start_line = pygame.Rect(500, -500, 100, 20)

    def world_to_screen(self, rect, camera_center):
        """Helper to convert a world rect to a screen rect based on camera and zoom"""
        # Calculate position relative to camera center
        rel_x = rect.x - camera_center[0]
        rel_y = rect.y - camera_center[1]
        
        # Scale by zoom and offset to screen center
        screen_x = int(rel_x * ZOOM + SCREEN_WIDTH / 2)
        screen_y = int(rel_y * ZOOM + SCREEN_HEIGHT / 2)
        screen_w = int(rect.width * ZOOM)
        screen_h = int(rect.height * ZOOM)
        
        return pygame.Rect(screen_x, screen_y, screen_w, screen_h)

    def draw(self, screen, camera_center):
        # 1. Draw Parallax Grid
        grid_size = 100
        scaled_grid_size = int(grid_size * ZOOM)
        
        # Calculate offset based on camera movement (Parallax factor 0.5)
        off_x = int(camera_center[0] * 0.5 * ZOOM) % scaled_grid_size
        off_y = int(camera_center[1] * 0.5 * ZOOM) % scaled_grid_size
        
        for x in range(-scaled_grid_size, SCREEN_WIDTH + scaled_grid_size, scaled_grid_size):
            pygame.draw.line(screen, COLOR_GRID, (x - off_x, 0), (x - off_x, SCREEN_HEIGHT))
        for y in range(-scaled_grid_size, SCREEN_HEIGHT + scaled_grid_size, scaled_grid_size):
            pygame.draw.line(screen, COLOR_GRID, (0, y - off_y), (SCREEN_WIDTH, y - off_y))

        # 2. Draw Track Shapes
        # Asphalt Background (Outer Rect)
        scr_outer = self.world_to_screen(self.outer_rect, camera_center)
        scr_border_rad = int(400 * ZOOM)
        pygame.draw.rect(screen, (20, 20, 25), scr_outer, border_radius=scr_border_rad)
        
        # Inner "Grass" (Inner Rect - drawn over asphalt to make a hole)
        scr_inner = self.world_to_screen(self.inner_rect, camera_center)
        scr_inner_rad = int(250 * ZOOM)
        pygame.draw.rect(screen, COLOR_BG, scr_inner, border_radius=scr_inner_rad)
        
        # Neon Kerbs
        pygame.draw.rect(screen, COLOR_NEON_BLUE, scr_outer, max(1, int(10 * ZOOM)), border_radius=scr_border_rad)
        pygame.draw.rect(screen, COLOR_NEON_BLUE, scr_inner, max(1, int(10 * ZOOM)), border_radius=scr_inner_rad)
        
        # Start/Finish Line
        scr_start = self.world_to_screen(self.start_line, camera_center)
        pygame.draw.rect(screen, COLOR_TEXT, scr_start)
        
        # Checkers
        checker_size = int(20 * ZOOM)
        if checker_size > 0:
            for i in range(5):
                for j in range(2):
                    col = (0,0,0) if (i+j)%2==0 else (255,255,255)
                    cx = scr_start.x + i * checker_size
                    cy = scr_start.y + j * (checker_size//2)
                    pygame.draw.rect(screen, col, (cx, cy, checker_size, checker_size//2))

    def is_on_track(self, x, y):
        # Simple collision logic (World Coords)
        in_outer = self.outer_rect.collidepoint(x, y)
        in_inner = self.inner_rect.collidepoint(x, y)
        return in_outer and not in_inner

class Car:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.color = color
        self.angle = 0
        self.speed = 0
        self.vel_x = 0
        self.vel_y = 0
        
        self.particles = []
        self.skidmarks = []
        
        self.glow = GlowSprite(40, color)
        self.braking = False

    def update(self, keys, track):
        # 1. Input & Physics
        move_fwd = keys[pygame.K_UP] or keys[pygame.K_w]
        move_bwd = keys[pygame.K_DOWN] or keys[pygame.K_s]
        turn_left = keys[pygame.K_LEFT] or keys[pygame.K_a]
        turn_right = keys[pygame.K_RIGHT] or keys[pygame.K_d]

        if move_fwd: self.speed += ACCELERATION
        if move_bwd: self.speed -= ACCELERATION
        self.braking = move_bwd and self.speed > 0

        if abs(self.speed) > 0.5:
            direction = 1 if self.speed > 0 else -1
            if turn_left: self.angle += TURN_SPEED * direction
            if turn_right: self.angle -= TURN_SPEED * direction
            
            if (turn_left or turn_right) and abs(self.speed) > MAX_SPEED * 0.7:
                if track.is_on_track(self.x, self.y):
                     self.skidmarks.append({'x': self.x, 'y': self.y, 'age': 255})

        on_road = track.is_on_track(self.x, self.y)
        current_drag = FRICTION if on_road else OFFROAD_DRAG
        self.speed *= current_drag
        
        rad = math.radians(self.angle)
        target_vx = math.cos(rad) * self.speed
        target_vy = math.sin(rad) * self.speed
        
        traction = 0.1 if on_road else 0.05
        self.vel_x += (target_vx - self.vel_x) * traction
        self.vel_y += (target_vy - self.vel_y) * traction

        self.x += self.vel_x
        self.y += self.vel_y

        limit = MAX_SPEED if on_road else MAX_SPEED * 0.5
        self.speed = max(min(self.speed, limit), -limit/2)

        # Particles
        if move_fwd and random.random() < 0.3:
            self.particles.append(Particle(self.x, self.y, (200, 200, 200), 30))
        if abs(self.speed) > MAX_SPEED * 0.8 and (turn_left or turn_right):
             self.particles.append(Particle(self.x, self.y, (100, 100, 100), 20))

        for p in self.particles: p.update()
        self.particles = [p for p in self.particles if p.life > 0]

        for s in self.skidmarks: s['age'] -= 2
        self.skidmarks = [s for s in self.skidmarks if s['age'] > 0]

    def draw(self, screen, camera_center):
        cx = int((self.x - camera_center[0]) * ZOOM + SCREEN_WIDTH / 2)
        cy = int((self.y - camera_center[1]) * ZOOM + SCREEN_HEIGHT / 2)
        
        # 1. Skidmarks
        if len(self.skidmarks) > 1:
            points = []
            for s in self.skidmarks:
                sx = (s['x'] - camera_center[0]) * ZOOM + SCREEN_WIDTH / 2
                sy = (s['y'] - camera_center[1]) * ZOOM + SCREEN_HEIGHT / 2
                points.append((sx, sy))
            if len(points) > 1:
                pygame.draw.lines(screen, (20, 20, 20), False, points, int(6 * ZOOM))

        # 2. Particles
        for p in self.particles:
            p.draw(screen, camera_center)

        # 3. Car Body
        car_w, car_h = 40, 24
        car_surf = pygame.Surface((car_w, car_h), pygame.SRCALPHA)
        pygame.draw.rect(car_surf, self.color, (0, 0, car_w, car_h), border_radius=4)
        pygame.draw.rect(car_surf, (0, 0, 0), (20, 2, 12, 20))
        
        rotated_car = pygame.transform.rotate(car_surf, -self.angle)
        
        final_w = int(rotated_car.get_width() * ZOOM)
        final_h = int(rotated_car.get_height() * ZOOM)
        scaled_car = pygame.transform.smoothscale(rotated_car, (final_w, final_h))
        
        rect = scaled_car.get_rect(center=(cx, cy))
        screen.blit(scaled_car, rect)

        # 4. Glow
        self.glow.draw(screen, (cx, cy))

        # 5. Headlights
        rad = math.radians(self.angle)
        head_len = 100 * ZOOM 
        offset_x = math.cos(rad) * 20 * ZOOM 
        offset_y = math.sin(rad) * 20 * ZOOM
        
        head_poly = [
            (cx + math.cos(rad - 0.3) * 20 * ZOOM, cy + math.sin(rad - 0.3) * 20 * ZOOM),
            (cx + math.cos(rad - 0.5) * head_len, cy + math.sin(rad - 0.5) * head_len),
            (cx + math.cos(rad + 0.5) * head_len, cy + math.sin(rad + 0.5) * head_len),
            (cx + math.cos(rad + 0.3) * 20 * ZOOM, cy + math.sin(rad + 0.3) * 20 * ZOOM)
        ]
        
        beam_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        pygame.draw.polygon(beam_surf, (*COLOR_NEON_YELLOW, 50), head_poly)
        screen.blit(beam_surf, (0,0), special_flags=pygame.BLEND_ADD)

        # 6. Tail Lights
        if self.braking:
            tail_color = (255, 0, 0)
            glow_scale = 2.0
        else:
            tail_color = (100, 0, 0)
            glow_scale = 1.0
            
        tl = (cx + math.cos(rad + 3.14) * 15 * ZOOM, cy + math.sin(rad + 3.14) * 8 * ZOOM)
        tr = (cx + math.cos(rad + 3.14) * 15 * ZOOM, cy + math.sin(rad + 3.14) * -8 * ZOOM)
        radius = max(1, int(3 * ZOOM))
        pygame.draw.circle(screen, tail_color, (int(tl[0]), int(tl[1])), radius)
        pygame.draw.circle(screen, tail_color, (int(tr[0]), int(tr[1])), radius)

# --- Main Game Loop ---

def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("NEON DRIFT: ZOOMED OUT EDITION")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("Verdana", 20, bold=True)

    track = Track()
    player = Car(550, -450, COLOR_NEON_BLUE) 
    camera = Camera()

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                # Zoom Toggles
                global ZOOM
                if event.key == pygame.K_EQUALS: 
                    ZOOM = min(1.0, ZOOM + 0.05)
                if event.key == pygame.K_MINUS: 
                    ZOOM = max(0.1, ZOOM - 0.05)

        keys = pygame.key.get_pressed()

        player.update(keys, track)
        camera.update(player.x, player.y)

        screen.fill(COLOR_BG)
        
        # Draw World
        track.draw(screen, camera.center)
        player.draw(screen, camera.center)

        # HUD
        bar_width = 300
        bar_height = 20
        fill_pct = min(abs(player.speed) / MAX_SPEED, 1.0)
        
        pygame.draw.rect(screen, (50,50,50), (20, SCREEN_HEIGHT - 50, bar_width, bar_height))
        grad_color = (
            int(0 + fill_pct * 255), 
            int(243 - fill_pct * 200), 
            int(255)
        )
        pygame.draw.rect(screen, grad_color, (20, SCREEN_HEIGHT - 50, int(bar_width * fill_pct), bar_height))
        
        spd_text = font.render(f"SPEED: {int(abs(player.speed)*15)}  |  ZOOM: {int(ZOOM*100)}%", True, COLOR_TEXT)
        screen.blit(spd_text, (20, SCREEN_HEIGHT - 80))
        
        instr_text = font.render("WASD / ARROWS to Drive | +/- to Zoom", True, (150, 150, 150))
        screen.blit(instr_text, (SCREEN_WIDTH - 350, SCREEN_HEIGHT - 40))

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
