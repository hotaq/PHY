import pygame
import pymunk
import sys
from pymunk import Vec2d
import math
import matplotlib.pyplot as plt
from collections import deque
import numpy as np

# Initialize Pygame and Pymunk
pygame.init()
WIDTH = 800
HEIGHT = 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Multiple Lato-lato Simulation")

# Enhanced colors - Define all colors at the start
BACKGROUND = (220, 220, 220)  # Lighter gray
BUTTON_COLOR = (80, 80, 80)   # Dark gray
BUTTON_HOVER = (100, 100, 100)
TEXT_COLOR = (40, 40, 40)     # Almost black
BALL_RED = (255, 50, 50)      # Brighter red
BALL_SHINE = (255, 150, 150)  # Light red for shine
BALL_SHADOW = (200, 30, 30)   # Darker red for shadow
STRING_COLOR = (160, 120, 80)  # Warmer brown
RED = BALL_RED  # Define RED to maintain compatibility

# Setup Pymunk space
space = pymunk.Space()
space.gravity = Vec2d(0, 981)

class Button:
    def __init__(self, x, y, width, height, text):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = BUTTON_COLOR
        self.hover_color = BUTTON_HOVER
        self.font = pygame.font.Font(None, 36)
        
    def draw(self, screen):
        color = self.hover_color if self.is_hovered() else self.color
        # Draw button shadow
        shadow_rect = self.rect.copy()
        shadow_rect.y += 2
        pygame.draw.rect(screen, (50, 50, 50), shadow_rect, border_radius=5)
        # Draw main button
        pygame.draw.rect(screen, color, self.rect, border_radius=5)
        # Draw button highlight
        pygame.draw.rect(screen, (color[0]+20, color[1]+20, color[2]+20), 
                        self.rect, border_radius=5, width=2)
        
        text_surface = self.font.render(self.text, True, (255, 255, 255))
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)
        
    def is_hovered(self):
        return self.rect.collidepoint(pygame.mouse.get_pos())

class AutomationSettings:
    def __init__(self):
        self.is_automated = False
        self.interval = 2.0
        self.timer = 0
        self.is_up = False
        self.last_update = 0
        self.stop_time = 10.0
        self.start_time = 0
        self.is_finished = False
        self.pull_force = 200  # Default pull-up force
        self.max_force = 400   # Maximum allowed force
        self.min_force = 50    # Minimum allowed force

class GraphData:
    def __init__(self, width=400, height=200, max_points=600):
        self.width = width
        self.height = height
        self.max_points = max_points
        self.times = deque(maxlen=max_points)
        self.angles = deque(maxlen=max_points)
        self.start_time = None
        self.window_start = 0  # Track the start of the visible time window
        self.surface = pygame.Surface((width, height), pygame.SRCALPHA)
        self.rect = pygame.Rect(WIDTH - width - 40, HEIGHT - height - 40, width, height)
        
    def update(self, current_time, angle):
        if self.start_time is None:
            self.start_time = current_time
            
        time = current_time - self.start_time
        
        # Update window start time to create scrolling effect
        if time > 10:  # When we pass 10 seconds
            self.window_start = time - 10  # Keep the last 10 seconds visible
        
        self.times.append(time)
        self.angles.append(abs(angle))
        
    def draw(self, screen):
        self.surface.fill((220, 220, 220, 240))
        
        # Draw grid
        grid_color = (180, 180, 180, 255)
        # Vertical lines every second
        window_end = self.window_start + 10
        for i in range(11):
            time_value = self.window_start + i
            x = int(30 + ((i / 10.0) * (self.width - 60)))
            pygame.draw.line(self.surface, grid_color, (x, 30), (x, self.height - 30))
            if i % 2 == 0:  # Label every 2 seconds
                time_label = pygame.font.Font(None, 20).render(f"{time_value:.0f}", True, (0, 0, 0))
                self.surface.blit(time_label, (x - 10, self.height - 25))
        
        # Horizontal lines
        for i in range(8):
            y = int(self.height - ((i * 0.25 / 1.75) * (self.height - 60)) - 30)
            pygame.draw.line(self.surface, grid_color, (30, y), (self.width - 30, y))
            angle_label = pygame.font.Font(None, 20).render(f"{i*0.25:.2f}", True, (0, 0, 0))
            self.surface.blit(angle_label, (5, y - 8))
        
        # Draw axes
        axes_color = (0, 0, 0, 255)
        pygame.draw.line(self.surface, axes_color, (30, self.height - 30), 
                        (self.width - 30, self.height - 30), 2)
        pygame.draw.line(self.surface, axes_color, (30, 30), 
                        (30, self.height - 30), 2)
        
        # Draw labels
        font = pygame.font.Font(None, 24)
        title = font.render('θ as a Function of Time (Kapitza Model)', True, (0, 0, 0))
        x_label = font.render('Time (s)', True, (0, 0, 0))
        y_label = font.render('θ(t) (rad)', True, (0, 0, 0))
        
        self.surface.blit(title, (self.width//2 - title.get_width()//2, 5))
        self.surface.blit(x_label, (self.width//2 - x_label.get_width()//2, self.height - 15))
        y_label_rotated = pygame.transform.rotate(y_label, 90)
        self.surface.blit(y_label_rotated, (5, self.height//2 - y_label_rotated.get_width()//2))
        
        # Draw data points with scrolling
        if len(self.times) > 1:
            points = []
            for i in range(len(self.times)):
                time = self.times[i]
                if time >= self.window_start and time <= window_end:
                    # Scale x based on the current window
                    x = int(30 + ((time - self.window_start) / 10.0) * (self.width - 60))
                    # Scale y from 0-1.75 radians
                    y = int(self.height - 30 - (self.angles[i] / 1.75) * (self.height - 60))
                    # Ensure points stay within bounds
                    x = max(30, min(x, self.width - 30))
                    y = max(30, min(y, self.height - 30))
                    points.append((x, y))
            
            if len(points) > 1:
                pygame.draw.lines(self.surface, (0, 100, 255, 255), False, points, 2)
        
        # Draw border
        pygame.draw.rect(self.surface, (0, 0, 0, 255), (0, 0, self.width, self.height), 2)
        
        # Draw current window time range
        time_range = font.render(f"Time Window: {self.window_start:.1f}s - {window_end:.1f}s", 
                               True, (0, 0, 0))
        screen.blit(self.surface, self.rect)

def create_lato_system():
    bodies = []
    shapes = []
    strings = []
    
    # Center the hand position
    hand = pymunk.Body(body_type=pymunk.Body.STATIC)
    hand.position = (WIDTH//2, HEIGHT//3)  # Moved down for better centering
    
    # Create two lato-lato balls with different sizes
    spread = 80  # Reduced spread for more centered look
    start_x = hand.position.x - spread/2
    
    # Ball sizes and positions
    ball_configs = [
        {"radius": 25, "y_offset": 150},  # Closer/larger ball
        {"radius": 25, "y_offset": 150}   # Further/smaller ball
    ]
    
    for i, config in enumerate(ball_configs):
        mass = 1
        radius = config["radius"]
        moment = pymunk.moment_for_circle(mass, 0, radius)
        body = pymunk.Body(mass, moment)
        
        body.position = (start_x + (i * spread), hand.position.y + config["y_offset"])
        
        shape = pymunk.Circle(body, radius)
        shape.elasticity = 0
        shape.friction = 0.5
        shape.color = RED
        
        string = pymunk.PinJoint(hand, body)
        
        bodies.append(body)
        shapes.append(shape)
        strings.append(string)
    
    return hand, bodies, shapes, strings

def create_boundaries():
    # Ground
    ground = pymunk.Segment(space.static_body, (0, HEIGHT-10), (WIDTH, HEIGHT-10), 5)
    ground.elasticity = 0.8
    ground.friction = 0.5
    
    # Walls
    left_wall = pymunk.Segment(space.static_body, (0, 0), (0, HEIGHT), 5)
    right_wall = pymunk.Segment(space.static_body, (WIDTH, 0), (WIDTH, HEIGHT), 5)
    
    left_wall.elasticity = 0.8
    right_wall.elasticity = 0.8
    
    return [ground, left_wall, right_wall]

def calculate_angle(hand_pos, ball_pos):
    """Calculate angle from vertical in degrees"""
    dx = ball_pos.x - hand_pos.x
    dy = ball_pos.y - hand_pos.y
    # Calculate angle from vertical (90 degrees offset from atan2)
    angle = math.degrees(math.atan2(dx, dy))
    return angle

def draw_ball(screen, pos, radius):
    # Draw shadow
    shadow_offset = 3
    pygame.draw.circle(screen, (150, 150, 150),
                      (int(pos.x + shadow_offset), int(pos.y + shadow_offset)),
                      int(radius))
    
    # Draw main ball
    pygame.draw.circle(screen, BALL_SHADOW,
                      (int(pos.x), int(pos.y)),
                      int(radius))
    pygame.draw.circle(screen, BALL_RED,
                      (int(pos.x), int(pos.y)),
                      int(radius-2))
    
    # Draw shine effect
    shine_pos = (int(pos.x-radius/3), int(pos.y-radius/3))
    shine_radius = int(radius/3)
    pygame.draw.circle(screen, BALL_SHINE, shine_pos, shine_radius)

def main():
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 36)
    
    # Create buttons
    pull_button = Button(WIDTH//2 - 180, 20, 120, 40, "Pull Up")
    auto_button = Button(WIDTH//2 + 60, 20, 120, 40, "Auto Mode")
    
    # Time control buttons
    time_up = Button(WIDTH - 140, 70, 30, 30, "+")
    time_down = Button(WIDTH - 180, 70, 30, 30, "-")
    
    # Stop time control buttons
    stop_time_up = Button(WIDTH - 140, 110, 30, 30, "+")
    stop_time_down = Button(WIDTH - 180, 110, 30, 30, "-")
    
    # Force control buttons
    force_up = Button(WIDTH - 140, 150, 30, 30, "+")
    force_down = Button(WIDTH - 180, 150, 30, 30, "-")
    
    automation = AutomationSettings()
    
    hand, bodies, shapes, strings = create_lato_system()
    
    for body, shape, string in zip(bodies, shapes, strings):
        space.add(body, shape, string)
    
    # Initial impulses
    bodies[0].apply_impulse_at_local_point((-300, 0))
    bodies[1].apply_impulse_at_local_point((300, 0))
    
    # Target Y position for pull up animation
    original_y = hand.position.y
    target_y = original_y
    
    prev_angles = [0, 0]
    angular_velocities = [0, 0]
    
    current_time = 0
    
    # Initialize graph
    graph = GraphData()
    
    while True:
        dt = clock.get_time() / 1000.0
        current_time += dt
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                if pull_button.is_hovered():
                    automation.is_automated = False
                    automation.is_finished = False
                    target_y = original_y - automation.pull_force if target_y == original_y else original_y
                
                elif auto_button.is_hovered():
                    automation.is_automated = not automation.is_automated
                    automation.timer = 0
                    automation.is_up = False
                    automation.last_update = current_time
                    automation.start_time = current_time
                    automation.is_finished = False
                    if automation.is_automated:
                        target_y = original_y - automation.pull_force
                        automation.is_up = True
                
                elif time_up.is_hovered():
                    automation.interval = min(10.0, automation.interval + 0.5)
                
                elif time_down.is_hovered():
                    automation.interval = max(0.5, automation.interval - 0.5)
                
                elif stop_time_up.is_hovered():
                    automation.stop_time = min(30.0, automation.stop_time + 1.0)
                
                elif stop_time_down.is_hovered():
                    automation.stop_time = max(1.0, automation.stop_time - 1.0)
                
                elif force_up.is_hovered():
                    automation.pull_force = min(automation.max_force, 
                                             automation.pull_force + 25)
                
                elif force_down.is_hovered():
                    automation.pull_force = max(automation.min_force, 
                                             automation.pull_force - 25)
        
        # Handle automation and stop time
        if automation.is_automated and not automation.is_finished:
            elapsed_time = current_time - automation.start_time
            if elapsed_time >= automation.stop_time:
                automation.is_automated = False
                automation.is_finished = True
                target_y = original_y
            else:
                if current_time - automation.last_update >= automation.interval:
                    automation.last_update = current_time
                    automation.is_up = not automation.is_up
                    target_y = original_y - automation.pull_force if automation.is_up else original_y
        
        # Smooth pull up/down animation
        current_y = hand.position.y
        if current_y != target_y:
            dy = (target_y - current_y) * 0.1
            hand.position = (hand.position.x, current_y + dy)
        
        # Calculate angles and update graph
        current_angles = []
        for i, body in enumerate(bodies):
            angle = calculate_angle(hand.position, body.position)
            current_angles.append(angle)
            angular_velocities[i] = (angle - prev_angles[i])
            prev_angles[i] = angle
            
            # Update graph with first ball's angle
            if i == 0:
                graph.update(current_time, math.radians(abs(angle)))
        
        space.step(1/60.0)
        
        # Drawing
        screen.fill(BACKGROUND)
        
        # Draw strings with gradient effect
        for body in bodies:
            start_pos = hand.position
            end_pos = body.position
            points = [(start_pos.x, start_pos.y)]
            
            # Create slight curve in string
            mid_x = (start_pos.x + end_pos.x) / 2
            mid_y = (start_pos.y + end_pos.y) / 2 + 10
            points.append((mid_x, mid_y))
            points.append((end_pos.x, end_pos.y))
            
            pygame.draw.lines(screen, STRING_COLOR, False, points, 2)
        
        # Draw balls with enhanced effects
        for shape in shapes:
            draw_ball(screen, shape.body.position, shape.radius)
        
        # Draw hand grip with shadow
        hand_pos = hand.position
        grip_rect = pygame.Rect(hand_pos.x - 15, hand_pos.y - 8, 30, 16)
        shadow_rect = grip_rect.copy()
        shadow_rect.y += 2
        pygame.draw.rect(screen, (150, 150, 150), shadow_rect, border_radius=5)
        pygame.draw.rect(screen, BALL_RED, grip_rect, border_radius=5)
        
        # Draw buttons
        pull_button.draw(screen)
        auto_button.draw(screen)
        time_up.draw(screen)
        time_down.draw(screen)
        stop_time_up.draw(screen)
        stop_time_down.draw(screen)
        force_up.draw(screen)
        force_down.draw(screen)
        
        # Display information with better formatting
        info_surface = pygame.Surface((250, 200))
        info_surface.set_alpha(220)
        info_surface.fill(BACKGROUND)
        screen.blit(info_surface, (WIDTH - 270, 10))
        
        y_pos = 20
        texts = [
            f"Auto: {'ON' if automation.is_automated else 'OFF'}",
            f"Interval: {automation.interval:.1f}s",
            f"Stop Time: {automation.stop_time:.1f}s",
            f"Pull Force: {automation.pull_force:.0f}"
        ]
        
        if automation.is_automated and not automation.is_finished:
            elapsed = current_time - automation.start_time
            remaining = max(0, automation.stop_time - elapsed)
            texts.append(f"Time Left: {remaining:.1f}s")
            texts.append(f"Next Move: {max(0, automation.interval - (current_time - automation.last_update)):.1f}s")
        elif automation.is_finished:
            texts.append("Automation Complete!")
        
        for text in texts:
            text_surface = font.render(text, True, TEXT_COLOR)
            screen.blit(text_surface, (WIDTH - 250, y_pos))
            y_pos += 30
        
        # Draw graph
        graph.draw(screen)
        
        pygame.display.flip()
        clock.tick(60)

if __name__ == "__main__":
    main()
