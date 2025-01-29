import pygame
import pymunk
import pymunk.pygame_util
import math
from typing import Dict, List, Tuple, Optional
import numpy as np
import collections

pygame.init()

# Constants
WIDTH, HEIGHT = 1200, 800  # Increased width to accommodate menu
SIMULATION_WIDTH = 700  # Original simulation area
MENU_WIDTH = WIDTH - SIMULATION_WIDTH
MENU_X = SIMULATION_WIDTH
PIXELS_PER_CM = 10  # 10 pixels = 1 cm
CM_PER_PIXEL = 1/PIXELS_PER_CM

# Colors
GRAY = (211, 211, 211)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
DARK_GRAY = (100, 100, 100)
YELLOW = (255, 255, 0)
GREEN = (0, 255, 0)
PURPLE = (128, 0, 128)
GRADIENT_BLUE = (41, 128, 185)
GRADIENT_GREEN = (46, 204, 113)
ROPE_COLOR = (120, 66, 18)
BALL_GRADIENT = [(255, 0, 0), (255, 100, 100)]
GRID_COLOR = (230, 230, 230)
TITLE_COLOR = (44, 62, 80)
GRAPH_LINE_WIDTH = 2
BALL_SHINE = True

class Slider:
    def __init__(self, x, y, width, min_val, max_val, initial_val, label):
        self.x = x
        self.y = y
        self.width = width
        self.height = 10
        self.min_val = min_val
        self.max_val = max_val
        self.value = initial_val
        self.label = label
        self.dragging = False
        
        # Calculate initial position of slider button
        self.button_x = self.x + (self.value - self.min_val) / (self.max_val - self.min_val) * self.width
        
    def draw(self, window):
        # Draw label
        font = pygame.font.Font(None, 24)
        label_text = font.render(f"{self.label}: {self.value:.1f}", True, BLACK)
        window.blit(label_text, (self.x, self.y - 20))
        
        # Draw track
        pygame.draw.rect(window, DARK_GRAY, (self.x, self.y, self.width, self.height))
        
        # Draw button
        pygame.draw.circle(window, BLUE, (int(self.button_x), self.y + self.height//2), 10)
    
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()
            button_rect = pygame.Rect(self.button_x - 10, self.y - 5, 20, 20)
            if button_rect.collidepoint(mouse_pos):
                self.dragging = True
                
        elif event.type == pygame.MOUSEBUTTONUP:
            self.dragging = False
            
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            mouse_x = event.pos[0]
            self.button_x = max(self.x, min(mouse_x, self.x + self.width))
            self.value = self.min_val + (self.button_x - self.x) / self.width * (self.max_val - self.min_val)

class AdvancedSlider(Slider):
    """Enhanced slider with better visual feedback"""
    def __init__(self, x, y, width, min_val, max_val, initial_val, label, unit=""):
        super().__init__(x, y, width, min_val, max_val, initial_val, label)
        self.unit = unit
        self.hover = False
        
    def draw(self, window):
        # Draw label with units
        font = pygame.font.Font(None, 24)
        if "Length" in self.label:
            # Show length in both pixels and cm
            label_text = font.render(
                f"{self.label}: {self.value:.1f} px ({px_to_cm(self.value):.1f} cm)", 
                True, BLACK
            )
        else:
            label_text = font.render(f"{self.label}: {self.value:.1f}{self.unit}", True, BLACK)
        window.blit(label_text, (self.x, self.y - 20))
        
        # Draw track with gradient
        gradient_rect = pygame.Surface((self.width, self.height))
        for i in range(self.width):
            progress = i / self.width
            color = tuple(int(a + (b - a) * progress) for a, b in zip(BLUE, GREEN))
            pygame.draw.line(gradient_rect, color, (i, 0), (i, self.height))
        window.blit(gradient_rect, (self.x, self.y))
        
        # Draw button with hover effect
        button_color = YELLOW if self.hover else BLUE
        pygame.draw.circle(window, button_color, (int(self.button_x), self.y + self.height//2), 10)
        
    def handle_event(self, event):
        super().handle_event(event)
        if event.type == pygame.MOUSEMOTION:
            mouse_pos = pygame.mouse.get_pos()
            button_rect = pygame.Rect(self.button_x - 10, self.y - 5, 20, 20)
            self.hover = button_rect.collidepoint(mouse_pos)

class Graph:
    def __init__(self, x, y, width, height, max_points=200):  # Increased buffer size
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.max_points = max_points
        self.data_ball1 = collections.deque([0] * max_points, maxlen=max_points)
        self.data_ball2 = collections.deque([0] * max_points, maxlen=max_points)
        self.max_value = 100  # Start with smaller scale
        self.min_value = -100
        
    def add_data_point(self, value1, value2):
        self.data_ball1.append(value1)
        self.data_ball2.append(value2)
        
        # Dynamic scale adjustment
        all_values = list(self.data_ball1) + list(self.data_ball2)
        if all_values:
            max_val = max(all_values)
            min_val = min(all_values)
            max_abs = max(abs(max_val), abs(min_val))
            
            # Smooth scale changes
            target_max = max_abs * 1.2
            self.max_value = min(max(100, target_max), 2000)  # Limit scale range
            self.min_value = -self.max_value
    
    def draw(self, window):
        # Draw background with grid
        pygame.draw.rect(window, WHITE, (self.x, self.y, self.width, self.height))
        
        # Draw grid
        grid_color = (220, 220, 220)
        grid_steps = 10
        for i in range(grid_steps + 1):
            # Horizontal lines
            y = self.y + (i * self.height // grid_steps)
            pygame.draw.line(window, grid_color, (self.x, y), (self.x + self.width, y), 1)
            # Vertical lines
            x = self.x + (i * self.width // grid_steps)
            pygame.draw.line(window, grid_color, (x, self.y), (x, self.y + self.height), 1)
        
        # Draw center line
        mid_y = self.y + self.height // 2
        pygame.draw.line(window, (150, 150, 150), 
                        (self.x, mid_y), 
                        (self.x + self.width, mid_y), 2)
        
        # Draw scale labels
        font = pygame.font.Font(None, 20)
        # Top value
        scale_label = font.render(f"{self.max_value:.0f}", True, BLACK)
        window.blit(scale_label, (self.x - 40, self.y))
        # Center value
        scale_label = font.render("0", True, BLACK)
        window.blit(scale_label, (self.x - 40, mid_y - 10))
        # Bottom value
        scale_label = font.render(f"{self.min_value:.0f}", True, BLACK)
        window.blit(scale_label, (self.x - 40, self.y + self.height - 15))
        
        # Draw data lines
        def draw_line(data, color):
            points = []
            for i, value in enumerate(data):
                x = self.x + (i * self.width // self.max_points)
                y = self.y + self.height//2 - (value * (self.height//2) / self.max_value)
                points.append((x, int(y)))
            if len(points) > 1:
                pygame.draw.lines(window, color, False, points, 2)
        
        # Draw both lines
        draw_line(self.data_ball1, RED)
        draw_line(self.data_ball2, BLUE)
        
        # Draw border
        pygame.draw.rect(window, BLACK, (self.x, self.y, self.width, self.height), 2)

class CollisionGraph(Graph):
    def __init__(self, x, y, width, height, max_points=200):
        super().__init__(x, y, width, height, max_points)
        self.collision_count = 0
        self.collision_times = []
        self.last_collision_time = 0
        self.collision_cooldown = 5  # Reduced cooldown
        
    def add_collision(self, time_stamp):
        if time_stamp - self.last_collision_time > self.collision_cooldown:
            self.collision_count += 1
            self.collision_times.append(time_stamp)
            self.last_collision_time = time_stamp
            # Add spike to both data series
            self.data_ball1.append(1)
            self.data_ball2.append(1)
        
    def update(self, time_stamp):
        # Add zero if no collision
        if time_stamp - self.last_collision_time > self.collision_cooldown:
            self.data_ball1.append(0)
            self.data_ball2.append(0)
    
    def draw(self, window):
        # Draw background with grid
        pygame.draw.rect(window, WHITE, (self.x, self.y, self.width, self.height))
        
        # Draw grid
        grid_color = (220, 220, 220)
        for i in range(10):
            y = self.y + (i * self.height // 10)
            pygame.draw.line(window, grid_color, (self.x, y), (self.x + self.width, y), 1)
            x = self.x + (i * self.width // 10)
            pygame.draw.line(window, grid_color, (x, self.y), (x, self.y + self.height), 1)
        
        # Draw collision events
        for i, value in enumerate(self.data_ball1):
            x = self.x + (i * self.width // self.max_points)
            if value > 0:
                pygame.draw.line(window, RED, 
                               (x, self.y + self.height),
                               (x, self.y), 2)
        
        # Draw border and count
        pygame.draw.rect(window, BLACK, (self.x, self.y, self.width, self.height), 2)
        font = pygame.font.Font(None, 24)
        text = font.render(f"Collisions: {self.collision_count}", True, BLACK)
        window.blit(text, (self.x + 5, self.y - 25))

def calculate_distance(point1, point2):
    return math.sqrt((point1[0] - point2[0])**2 + (point1[1] - point2[1])**2)

def px_to_cm(pixels):
    """Convert pixels to centimeters"""
    return pixels * CM_PER_PIXEL

def cm_to_px(cm):
    """Convert centimeters to pixels"""
    return cm * PIXELS_PER_CM

def draw_ball_with_gradient(window, pos, radius):
    """Draw a ball with gradient and shine effect"""
    # Main ball gradient
    for r in range(radius, 0, -1):
        progress = r/radius
        color = [int(a + (b-a)*progress) for a, b in zip(BALL_GRADIENT[0], BALL_GRADIENT[1])]
        pygame.draw.circle(window, color, (int(pos.x), int(pos.y)), r)
    
    # Add shine effect
    if BALL_SHINE:
        shine_pos = (int(pos.x - radius/3), int(pos.y - radius/3))
        pygame.draw.circle(window, (255, 255, 255), shine_pos, radius//4)

def draw(space, window, balls, sliders, stats, graphs):
    # Draw simulation area with gradient background
    background = pygame.Surface((SIMULATION_WIDTH, HEIGHT))
    for y in range(HEIGHT):
        progress = y/HEIGHT
        color = [int(a + (b-a)*progress) for a, b in zip(GRAY, (180, 180, 180))]
        pygame.draw.line(background, color, (0, y), (SIMULATION_WIDTH, y))
    window.blit(background, (0, 0))
    
    # Draw top line with thickness
    for shape in space.shapes:
        if isinstance(shape, pymunk.Segment):
            p1 = shape.a
            p2 = shape.b
            # Draw shadow
            shadow_offset = 3
            pygame.draw.line(window, (50, 50, 50), 
                           (p1.x + shadow_offset, p1.y + shadow_offset),
                           (p2.x + shadow_offset, p2.y + shadow_offset), 8)
            # Draw main line
            pygame.draw.line(window, DARK_GRAY, 
                           (p1.x, p1.y), (p2.x, p2.y), 8)
    
    # Draw springs and ropes
    for c in space.constraints:
        if isinstance(c, pymunk.DampedSpring):
            p1 = c.a.position
            p2 = c.b.position
            # Draw shadow
            shadow_offset = 3
            pygame.draw.line(window, (0, 0, 0, 50), 
                           (p1.x + shadow_offset, p1.y + shadow_offset),
                           (p2.x + shadow_offset, p2.y + shadow_offset), 4)
            # Draw spring/rope
            pygame.draw.line(window, ROPE_COLOR, p1, p2, 3)
    
    # Draw balls with enhanced effects
    for ball in balls:
        draw_ball_with_gradient(window, ball.position, 15)
    
    # Draw menu panel with gradient
    menu_background = pygame.Surface((MENU_WIDTH, HEIGHT))
    for y in range(HEIGHT):
        progress = y/HEIGHT
        color = [int(255 - 10*progress)] * 3  # Subtle gradient
        pygame.draw.line(menu_background, color, (0, y), (MENU_WIDTH, y))
    window.blit(menu_background, (SIMULATION_WIDTH, 0))
    
    # Draw title with shadow
    font = pygame.font.Font(None, 40)
    title_shadow = font.render("Physics Controls", True, (100, 100, 100))
    title = font.render("Physics Controls", True, TITLE_COLOR)
    window.blit(title_shadow, (SIMULATION_WIDTH + 22, 22))
    window.blit(title, (SIMULATION_WIDTH + 20, 20))
    
    # Draw sliders
    for slider in sliders:
        slider.draw(window)
    
    # Draw statistics with enhanced styling
    stats_y = 400
    font = pygame.font.Font(None, 24)
    for label, value in stats.items():
        # Draw stat box with shadow
        stat_box = pygame.Rect(SIMULATION_WIDTH + 15, stats_y - 5, MENU_WIDTH - 30, 30)
        pygame.draw.rect(window, (245, 245, 245), stat_box)
        pygame.draw.rect(window, (200, 200, 200), stat_box, 1)
        
        if "Distance" in label:
            text = font.render(f"{label}: {value:.1f} px ({px_to_cm(value):.1f} cm)", True, TITLE_COLOR)
        elif "Velocity" in label:
            text = font.render(f"{label}: {value:.1f} px/s ({px_to_cm(value):.1f} cm/s)", True, TITLE_COLOR)
        else:
            text = font.render(f"{label}: {value:.1f}", True, TITLE_COLOR)
        window.blit(text, (SIMULATION_WIDTH + 20, stats_y))
        stats_y += 35
    
    # Draw graph titles with style
    font = pygame.font.Font(None, 28)
    for title, y_pos in [("Velocity Graph", 380), ("Collision Graph", 580)]:
        text = font.render(title, True, TITLE_COLOR)
        text_shadow = font.render(title, True, (200, 200, 200))
        window.blit(text_shadow, (SIMULATION_WIDTH + 22, y_pos + 2))
        window.blit(text, (SIMULATION_WIDTH + 20, y_pos))
    
    # Draw graphs
    for graph in graphs:
        graph.draw(window)

def create_balls(space, initial_pos=None, rope_length=100, rope_stiffness=1.0, pull_height=0):
    """Create balls with enhanced rope physics and pullable top line"""
    # Create static line segment on top with adjustable height
    base_height = 100  # Increased base height
    current_height = base_height - pull_height
    
    # Create the top bar as a static body
    top_bar = pymunk.Body(body_type=pymunk.Body.STATIC)
    line_segment = pymunk.Segment(
        top_bar,
        (100, current_height),  # Extended line length
        (SIMULATION_WIDTH-100, current_height),
        5
    )
    line_segment.friction = 0.5
    line_segment.elasticity = 0.5
    space.add(line_segment)
    
    # Create anchor points for springs at fixed distances on the line
    anchor1 = pymunk.Body(body_type=pymunk.Body.STATIC)
    anchor2 = pymunk.Body(body_type=pymunk.Body.STATIC)
    anchor1.position = (SIMULATION_WIDTH/2 - 100, current_height)  # Increased spacing
    anchor2.position = (SIMULATION_WIDTH/2 + 100, current_height)  # Increased spacing
    
    # Create balls
    ball1 = pymunk.Body(1, pymunk.moment_for_circle(1, 0, 15))
    ball2 = pymunk.Body(1, pymunk.moment_for_circle(1, 0, 15))
    
    # Set initial positions
    if initial_pos and all(isinstance(pos, (tuple, list)) for pos in initial_pos.values()):
        ball1.position = initial_pos['ball1']
        ball2.position = initial_pos['ball2']
    else:
        ball1.position = (anchor1.position.x, anchor1.position.y + rope_length)
        ball2.position = (anchor2.position.x, anchor2.position.y + rope_length)
    
    shape1 = pymunk.Circle(ball1, 15)
    shape2 = pymunk.Circle(ball2, 15)
    
    for shape in [shape1, shape2]:
        shape.mass = 3
        shape.friction = 0.5
        shape.elasticity = 0.95
        shape.collision_type = 1
    
    space.add(ball1, ball2, shape1, shape2)
    
    # Create springs with damping
    spring1 = pymunk.DampedSpring(
        anchor1, ball1, 
        (0, 0), (0, 0), 
        rope_length, 
        rope_stiffness * 100, 
        1.0
    )
    spring2 = pymunk.DampedSpring(
        anchor2, ball2, 
        (0, 0), (0, 0), 
        rope_length, 
        rope_stiffness * 100, 
        1.0
    )
    
    # Create rope constraint between balls
    rope = pymunk.DampedSpring(
        ball1, ball2, 
        (0, 0), (0, 0), 
        100,  # Fixed distance between balls
        rope_stiffness * 50, 
        0.5
    )
    
    space.add(spring1, spring2, rope)
    
    return [ball1, ball2], [anchor1, anchor2], top_bar

def draw_setup_screen(window, ball_positions):
    """Draw setup screen for initial ball positions"""
    window.fill(WHITE)
    pygame.draw.rect(window, GRAY, (0, 0, SIMULATION_WIDTH, HEIGHT))
    
    # Draw balls
    for pos in ball_positions.values():
        pygame.draw.circle(window, RED, (int(pos[0]), int(pos[1])), 15)
    
    # Draw instructions
    font = pygame.font.Font(None, 36)
    text = font.render("Click and drag balls to set initial positions", True, BLACK)
    window.blit(text, (SIMULATION_WIDTH/4, 50))
    
    # Draw start button
    button_rect = pygame.Rect(SIMULATION_WIDTH/2 - 50, HEIGHT - 100, 100, 40)
    pygame.draw.rect(window, BLUE, button_rect)
    text = font.render("Start", True, WHITE)
    text_rect = text.get_rect(center=button_rect.center)
    window.blit(text, text_rect)
    
    pygame.display.update()
    return button_rect

def run(window, width, height):
    run = True
    clock = pygame.time.Clock()
    simulation_started = False
    
    # Initial ball positions
    ball_positions = {
        'ball1': (SIMULATION_WIDTH/2 - 30, 200),
        'ball2': (SIMULATION_WIDTH/2 + 30, 200)
    }
    
    # Setup phase
    selected_ball = None
    start_button = None
    
    # Add these initialization variables back
    current_rope_length = 100  # Initial rope length
    current_rope_stiffness = 1.0  # Initial rope stiffness
    
    while not simulation_started and run:
        start_button = draw_setup_screen(window, ball_positions)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
            
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = event.pos
                # Check if start button clicked
                if start_button.collidepoint(mouse_pos):
                    simulation_started = True
                    break
                
                # Check if ball clicked
                for ball_key, pos in ball_positions.items():
                    if calculate_distance(mouse_pos, pos) < 20:
                        selected_ball = ball_key
            
            elif event.type == pygame.MOUSEBUTTONUP:
                selected_ball = None
            
            elif event.type == pygame.MOUSEMOTION:
                if selected_ball and event.pos[0] < SIMULATION_WIDTH:
                    ball_positions[selected_ball] = event.pos
    
    # Initialize physics simulation
    space = pymunk.Space()
    space.gravity = (0, 981)
    
    balls, anchors, top_bar = create_balls(space, ball_positions, 
                                         current_rope_length, 
                                         current_rope_stiffness)
    
    # Enhanced sliders with units
    sliders = [
        AdvancedSlider(MENU_X + 10, 80, MENU_WIDTH - 40, 0, 2000, 981, "Gravity", " px/s²"),
        AdvancedSlider(MENU_X + 10, 130, MENU_WIDTH - 40, 0, 2, 1, "Mass", " kg"),
        AdvancedSlider(MENU_X + 10, 180, MENU_WIDTH - 40, 0, 1, 0.95, "Elasticity", ""),
        AdvancedSlider(MENU_X + 10, 230, MENU_WIDTH - 40, 0, 1, 0.5, "Friction", ""),
        AdvancedSlider(MENU_X + 10, 280, MENU_WIDTH - 40, 
                      cm_to_px(5), cm_to_px(30), cm_to_px(10), "Rope Length", ""),
        AdvancedSlider(MENU_X + 10, 330, MENU_WIDTH - 40, 0.1, 5.0, 1.0, "Rope Stiffness", "")
    ]
    
    # Create graphs
    velocity_graph = Graph(MENU_X + 20, 420, MENU_WIDTH - 40, 150)
    collision_graph = CollisionGraph(MENU_X + 20, 620, MENU_WIDTH - 40, 150)
    graphs = [velocity_graph, collision_graph]
    
    # Create simulation time counter
    simulation_time = 0
    
    # Set up collision handling with time data
    space.add_collision_handler(1, 1).begin = lambda arb, space, _: collision_handler(
        arb, space, (collision_graph, simulation_time)
    )
    
    def reset_simulation(space, balls, handle, settings):
        """Reset simulation with new settings"""
        space = pymunk.Space()
        space.gravity = (0, settings['gravity'])
        
        # Create new balls with current settings
        balls, handle = create_balls(space, 
                                   initial_pos={'ball1': balls[0].position, 
                                              'ball2': balls[1].position},
                                   rope_length=settings['rope_length'],
                                   rope_stiffness=settings['rope_stiffness'])
        
        # Apply other physics properties
        for ball in balls:
            ball.mass = settings['mass']
            for shape in space.shapes:
                if shape.body == ball:
                    shape.elasticity = settings['elasticity']
                    shape.friction = settings['friction']
        
        return space, balls, handle
    
    while run and simulation_started:
        simulation_time += 1  # Increment time counter
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
            
            # Handle slider events and check for changes
            settings_changed = False
            current_settings = {
                'gravity': space.gravity.y,
                'mass': balls[0].mass,
                'elasticity': next(shape.elasticity for shape in space.shapes if shape.body == balls[0]),
                'friction': next(shape.friction for shape in space.shapes if shape.body == balls[0]),
                'rope_length': current_rope_length,
                'rope_stiffness': current_rope_stiffness
            }
            
            for i, slider in enumerate(sliders):
                old_value = slider.value
                slider.handle_event(event)
                if old_value != slider.value:
                    settings_changed = True
            
            new_settings = {
                'gravity': sliders[0].value,
                'mass': sliders[1].value,
                'elasticity': sliders[2].value,
                'friction': sliders[3].value,
                'rope_length': sliders[4].value,
                'rope_stiffness': sliders[5].value
            }
            
            # Reset simulation if settings changed
            if settings_changed:
                space, balls, handle = reset_simulation(space, balls, handle, new_settings)
                current_rope_length = new_settings['rope_length']
                current_rope_stiffness = new_settings['rope_stiffness']
            
            # Handle ball interaction
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = event.pos
                for ball in balls:
                    if calculate_distance(mouse_pos, ball.position) < 20:
                        selected_ball = ball
            
            elif event.type == pygame.MOUSEBUTTONUP:
                if selected_ball:
                    mouse_pos = pygame.mouse.get_pos()
                    force_x = (selected_ball.position.x - mouse_pos[0]) * 5
                    force_y = (selected_ball.position.y - mouse_pos[1]) * 5
                    selected_ball.apply_impulse_at_local_point((force_x, force_y))
                    selected_ball = None
            
            elif event.type == pygame.MOUSEMOTION:
                if selected_ball and event.pos[0] < SIMULATION_WIDTH:
                    selected_ball.position = event.pos
        
        # Update physics with fixed timestep
        space.step(1/60.0)
        
        # Update graphs
        velocity_graph.add_data_point(
            float(balls[0].velocity.y),
            float(balls[1].velocity.y)
        )
        collision_graph.update(simulation_time)
        
        # Update stats
        stats = {
            "Ball 1 Velocity": math.sqrt(balls[0].velocity.x**2 + balls[0].velocity.y**2),
            "Ball 2 Velocity": math.sqrt(balls[1].velocity.x**2 + balls[1].velocity.y**2),
            "Distance": calculate_distance(balls[0].position, balls[1].position),
            "Collisions": collision_graph.collision_count
        }
        
        # Update drawing
        draw(space, window, balls, sliders, stats, graphs)
        
        pygame.display.update()
        clock.tick(60)
    
    pygame.quit()

def collision_handler(arbiter, space, data):
    """Enhanced collision handler with time stamp"""
    collision_graph, current_time = data
    collision_graph.add_collision(current_time)
    
    # Add visual effect at collision point
    point = arbiter.contact_point_set.points[0].point_a
    # You could add particle effects or other visual feedback here
    
    return True

def calculate_pendulum_energy(ball, length, gravity=981):
    """Calculate pendulum energy using formula from section 2.1"""
    # E = mgl(1-cos θ) + (ml²θ̇²)/2
    mass = ball.mass
    angle = math.atan2(ball.position.y - length, ball.position.x - SIMULATION_WIDTH/2)
    angular_velocity = ball.angular_velocity
    
    potential_energy = mass * gravity * length * (1 - math.cos(angle))
    kinetic_energy = 0.5 * mass * (length**2) * (angular_velocity**2)
    
    return potential_energy + kinetic_energy

def check_slack_condition(ball, length, gravity=981):
    """Check slack condition using formula from section 2.2.1"""
    # mlθ̇² + mgcos θ > 0
    mass = ball.mass
    angle = math.atan2(ball.position.y - length, ball.position.x - SIMULATION_WIDTH/2)
    angular_velocity = ball.angular_velocity
    
    return (mass * length * angular_velocity**2 + mass * gravity * math.cos(angle)) > 0

def calculate_slack_time(ball, length, gravity=981):
    """Calculate slack time using formula from section 2.2.2"""
    # t = 4v₀sin θ/g
    velocity = math.sqrt(ball.velocity.x**2 + ball.velocity.y**2)
    angle = math.atan2(ball.position.y - length, ball.position.x - SIMULATION_WIDTH/2)
    
    return 4 * velocity * math.sin(angle) / gravity

def update_ball_physics(ball, handle, length, stiffness, dt):
    """Update ball physics using Mathieu's equation from section 2.3"""
    # -θ̈ = (g - a₀ω²cos ωt)sin θ
    gravity = 981
    omega = math.sqrt(gravity/length)  # Natural frequency
    
    angle = math.atan2(ball.position.y - handle.position.y, 
                      ball.position.x - handle.position.x)
    
    # Calculate acceleration
    angular_acceleration = -(gravity/length) * math.sin(angle)
    angular_acceleration -= (stiffness * omega**2 * math.cos(omega * dt)) * math.sin(angle)
    
    # Update angular velocity
    ball.angular_velocity += angular_acceleration * dt
    
    # Update position
    new_x = handle.position.x + length * math.sin(angle + ball.angular_velocity * dt)
    new_y = handle.position.y + length * math.cos(angle + ball.angular_velocity * dt)
    
    ball.position = pymunk.Vec2d(new_x, new_y)

if __name__ == "__main__":
    window = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Physics Simulation Controls")
    run(window, WIDTH, HEIGHT)