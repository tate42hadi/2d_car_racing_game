#                                           hello guys
#                          this is a project which we make a 2d car racing game 

#                                         (PYTHON VERSION)

#                                made by = tate42hadi   &    bruh098715 
import pygame
import math
import random
import sys

# --- Configuration ---
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 700
FPS = 60

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
        self.radius = radius
        self.color = color
        self.surface = pygame.Surface((radius*2, radius*2), pygame.SRCALPHA)
        self.render_glow()

    def render_glow(self):
        # Create a radial gradient for neon effect
        for r in range(self.radius, 0, -1):
            alpha = int((1 - (r / self.radius)) * 100) # Transparency increases towards edge
            # We draw many circles with decreasing alpha
            pygame.draw.circle(self.surface, (*self.color, alpha), (self.radius, self.radius), r)
        
        # Solid center
        pygame.draw.circle(self.surface, (*self.color, 255), (self.radius, self.radius), 2)

    def draw(self, target_surface, pos, scale=1.0):
        if scale != 1.0:
            size = int(self.radius * 2 * scale)
            scaled = pygame.transform.scale(self.surface, (size, size))
            target_surface.blit(scaled, (pos[0] - size//2, pos[1] - size//2), special_flags=pygame.BLEND_ADD)
        else:
            target_surface.blit(self.surface, (pos[0] - self.radius, pos[1] - self.radius), special_flags=pygame.BLEND_ADD)

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

    def draw(self, surface, camera_offset):
        if self.life > 0 and self.size > 0:
            alpha = int((self.life / self.max_life) * 255)
            # Create a small surface for the particle to support alpha
            s = pygame.Surface((int(self.size)*2, int(self.size)*2), pygame.SRCALPHA)
            pygame.draw.circle(s, (*self.color, alpha), (int(self.size), int(self.size)), int(self.size))
            
            # Draw with additive blending for "fire" effect
            draw_pos = (self.x - camera_offset[0] - self.size, self.y - camera_offset[1] - self.size)
            surface.blit(s, draw_pos, special_flags=pygame.BLEND_ADD)

# --- Game Objects ---

class Camera:
    def __init__(self):
        self.offset = [0, 0]

    def update(self, target_x, target_y):
        # Smooth follow
        target_offset_x = target_x - SCREEN_WIDTH // 2
        target_offset_y = target_y - SCREEN_HEIGHT // 2
        
        self.offset[0] += (target_offset_x - self.offset[0]) * 0.1
        self.offset[1] += (target_offset_y - self.offset[1]) * 0.1

class Track:
    def __init__(self):
        # A large rounded rect track
        self.outer_rect = pygame.Rect(-500, -500, 2000, 2000)
        self.inner_rect = pygame.Rect(-200, -200, 1400, 1400)
        self.road_width = 300
        
        # Pre-render the static track background to save FPS
        self.surface = pygame.Surface((2000, 2000))
        self.render_static_track()

    def render_static_track(self):
        # Fill Background (Asphalt)
        self.surface.fill(COLOR_BG) # Clear
        pygame.draw.rect(self.surface, (20, 20, 25), self.outer_rect, border_radius=400)
        
        # Draw "Kerbs" (Neon borders)
        pygame.draw.rect(self.surface, COLOR_NEON_BLUE, self.outer_rect, 10, border_radius=400)
        pygame.draw.rect(self.surface, COLOR_NEON_BLUE, self.inner_rect, 10, border_radius=250)
        
        # Start/Finish Line
        pygame.draw.rect(self.surface, COLOR_TEXT, (500, -500, 100, 20))
        # Checkers
        for i in range(5):
            for j in range(2):
                col = (0,0,0) if (i+j)%2==0 else (255,255,255)
                pygame.draw.rect(self.surface, col, (500 + i*20, -500 + j*10, 20, 10))

    def draw(self, screen, camera_offset):
        # Draw grid background (Parallax effect - moves slower than camera)
        grid_size = 100
        off_x = int(camera_offset[0] * 0.5) % grid_size
        off_y = int(camera_offset[1] * 0.5) % grid_size
        
        for x in range(-grid_size, SCREEN_WIDTH + grid_size, grid_size):
            pygame.draw.line(screen, COLOR_GRID, (x - off_x, 0), (x - off_x, SCREEN_HEIGHT))
        for y in range(-grid_size, SCREEN_HEIGHT + grid_size, grid_size):
            pygame.draw.line(screen, COLOR_GRID, (0, y - off_y), (SCREEN_WIDTH, y - off_y))

        # Draw the pre-rendered track
        screen.blit(self.surface, (-camera_offset[0], -camera_offset[1]))

    def is_on_track(self, x, y):
        # Simple point-in-rect collision (assuming rounded rect roughly)
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
        self.skidmarks = [] # List of points (x, y)
        
        # Graphics helpers
        self.glow = GlowSprite(40, color)
        self.braking = False

    def update(self, keys, track):
        # 1. Input & Physics
        move_fwd = keys[pygame.K_UP] or keys[pygame.K_w]
        move_bwd = keys[pygame.K_DOWN] or keys[pygame.K_s]
        turn_left = keys[pygame.K_LEFT] or keys[pygame.K_a]
        turn_right = keys[pygame.K_RIGHT] or keys[pygame.K_d]

        # Acceleration
        if move_fwd: self.speed += ACCELERATION
        if move_bwd: self.speed -= ACCELERATION
        
        self.braking = move_bwd and self.speed > 0

        # Steering
        if abs(self.speed) > 0.5:
            direction = 1 if self.speed > 0 else -1
            if turn_left: self.angle += TURN_SPEED * direction
            if turn_right: self.angle -= TURN_SPEED * direction
            
            # Add skidmarks if turning hard at speed
            if (turn_left or turn_right) and abs(self.speed) > MAX_SPEED * 0.7:
                if track.is_on_track(self.x, self.y):
                     self.skidmarks.append({'x': self.x, 'y': self.y, 'age': 255})

        # Friction
        on_road = track.is_on_track(self.x, self.y)
        current_drag = FRICTION if on_road else OFFROAD_DRAG
        self.speed *= current_drag
        
        # Velocity Calculation (Drift physics)
        rad = math.radians(self.angle)
        target_vx = math.cos(rad) * self.speed
        target_vy = math.sin(rad) * self.speed
        
        # Traction: Lerp current velocity towards target velocity
        traction = 0.1 if on_road else 0.05
        self.vel_x += (target_vx - self.vel_x) * traction
        self.vel_y += (target_vy - self.vel_y) * traction

        # Update Pos
        self.x += self.vel_x
        self.y += self.vel_y

        # Cap Speed
        limit = MAX_SPEED if on_road else MAX_SPEED * 0.5
        self.speed = max(min(self.speed, limit), -limit/2)

        # 2. Particles
        # Engine Smoke
        if move_fwd and random.random() < 0.3:
            self.particles.append(Particle(self.x, self.y, (200, 200, 200), 30))
        
        # Drift Smoke
        if abs(self.speed) > MAX_SPEED * 0.8 and (turn_left or turn_right):
             self.particles.append(Particle(self.x, self.y, (100, 100, 100), 20))

        # Update particles
        for p in self.particles:
            p.update()
        self.particles = [p for p in self.particles if p.life > 0]

        # Update Skidmarks (Fade out)
        for s in self.skidmarks:
            s['age'] -= 2
        self.skidmarks = [s for s in self.skidmarks if s['age'] > 0]

    def draw(self, screen, camera_offset):
        cx, cy = self.x - camera_offset[0], self.y - camera_offset[1]
        
        # 1. Draw Skidmarks
        if len(self.skidmarks) > 1:
            points = [(s['x'] - camera_offset[0], s['y'] - camera_offset[1]) for s in self.skidmarks]
            # Draw lines with alpha is hard in pygame directly, so we draw simple lines
            # For better visual, we could draw to a surface, but simple lines work for "burnt rubber"
            if len(points) > 1:
                pygame.draw.lines(screen, (20, 20, 20), False, points, 6)

        # 2. Draw Particles
        for p in self.particles:
            p.draw(screen, camera_offset)

        # 3. Draw Car Body
        # We rotate a surface instead of calculating polygons manually for cleaner look
        car_surf = pygame.Surface((40, 24), pygame.SRCALPHA)
        # Body
        pygame.draw.rect(car_surf, self.color, (0, 0, 40, 24), border_radius=4)
        # Windshield
        pygame.draw.rect(car_surf, (0, 0, 0), (20, 2, 12, 20))
        
        # Rotate Car
        rotated_car = pygame.transform.rotate(car_surf, -self.angle)
        rect = rotated_car.get_rect(center=(cx, cy))
        screen.blit(rotated_car, rect)

        # 4. Glow Effect (Behind car)
        self.glow.draw(screen, (cx, cy))

        # 5. Headlights
        rad = math.radians(self.angle)
        head_len = 100
        head_poly = [
            (cx + math.cos(rad - 0.3) * 20, cy + math.sin(rad - 0.3) * 20),
            (cx + math.cos(rad - 0.5) * head_len, cy + math.sin(rad - 0.5) * head_len),
            (cx + math.cos(rad + 0.5) * head_len, cy + math.sin(rad + 0.5) * head_len),
            (cx + math.cos(rad + 0.3) * 20, cy + math.sin(rad + 0.3) * 20)
        ]
        
        # Draw transparent beams
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
            
        # Simple rear lights
        tl = (cx + math.cos(rad + 3.14) * 15, cy + math.sin(rad + 3.14) * 8)
        tr = (cx + math.cos(rad + 3.14) * 15, cy + math.sin(rad + 3.14) * -8)
        pygame.draw.circle(screen, tail_color, (int(tl[0]), int(tl[1])), 3)
        pygame.draw.circle(screen, tail_color, (int(tr[0]), int(tr[1])), 3)

# --- Main Game Loop ---

def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("NEON DRIFT: PYTHON EDITION")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("Verdana", 20, bold=True)
    big_font = pygame.font.SysFont("Verdana", 40, bold=True)

    # Init Objects
    track = Track()
    player = Car(550, -450, COLOR_NEON_BLUE) # Start position near top of track
    camera = Camera()

    running = True
    while running:
        # 1. Event Handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False

        keys = pygame.key.get_pressed()

        # 2. Update
        player.update(keys, track)
        camera.update(player.x, player.y)

        # 3. Draw
        screen.fill(COLOR_BG)
        
        # Draw World
        track.draw(screen, (int(camera.offset[0]), int(camera.offset[1])))
        player.draw(screen, (int(camera.offset[0]), int(camera.offset[1])))

        # 4. HUD
        # Speed Bar
        bar_width = 300
        bar_height = 20
        fill_pct = min(abs(player.speed) / MAX_SPEED, 1.0)
        
        # Background of bar
        pygame.draw.rect(screen, (50,50,50), (20, SCREEN_HEIGHT - 50, bar_width, bar_height))
        # Fill
        grad_color = (
            int(0 + fill_pct * 255), # Redder as faster
            int(243 - fill_pct * 200), 
            int(255)
        )
        pygame.draw.rect(screen, grad_color, (20, SCREEN_HEIGHT - 50, int(bar_width * fill_pct), bar_height))
        # Text
        spd_text = font.render(f"SPEED: {int(abs(player.speed)*15)}", True, COLOR_TEXT)
        screen.blit(spd_text, (20, SCREEN_HEIGHT - 80))
        
        # Instructions
        instr_text = font.render("WASD / ARROWS to Drive", True, (150, 150, 150))
        screen.blit(instr_text, (SCREEN_WIDTH - 280, SCREEN_HEIGHT - 40))

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()