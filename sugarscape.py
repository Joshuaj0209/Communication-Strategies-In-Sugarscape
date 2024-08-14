import pygame
import random
import math

# Constants
GAME_WIDTH, HEIGHT = 700, 700  # Width of the game area
ANALYTICS_WIDTH = 300  # Width of the analytics area (increased for better readability)
WIDTH = GAME_WIDTH + ANALYTICS_WIDTH  # Total width
SUGAR_RADIUS = 20  # Radius to define proximity for sugar consumption
ANT_SIZE = 10
ANT_SPEED = 1
NUM_ANTS = 5
SUGAR_MAX = 100  # Max sugar per patch
SUGAR_REGENERATION_RATE = 0.0002
SQUARE_SIZE = 5  # Size of each sugar square
NEW_SUGAR_INTERVAL = 5000  # Interval in milliseconds to add new sugar patches
COMMUNICATION_RADIUS = 700  # Communication range for ants
DETECTION_RADIUS = 60  # Radius for ant's "vision"

# Ant health constants
INITIAL_HEALTH = 100
MAX_HEALTH = 150
HEALTH_DECREASE_RATE = 0.1
HEALTH_INCREASE_AMOUNT = 10

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)  # Color for sugar squares
YELLOW = (255, 255, 0)  # Color for consumed sugar squares
GRAY = (200, 200, 200)  # Border color

# Ant class
class Ant:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.direction = random.uniform(0, 2 * math.pi)  # Random initial direction
        self.turn_angle = math.pi / 8  # Maximum turn angle per step
        self.health = INITIAL_HEALTH
        self.initial_health = INITIAL_HEALTH
        self.max_health = MAX_HEALTH
        self.target = None  # New attribute to store target sugar location
        self.communicated_target = None
        self.lifespan = 0  # Track the lifespan of the ant

    def detect_sugar(self, sugar_patches):
        closest_sugar = None
        closest_distance = float('inf')
        
        # Check for sugar within detection radius
        for sugar in sugar_patches:
            if sugar[2]:  # If sugar is available
                dx = sugar[0] - self.x
                dy = sugar[1] - self.y
                distance = math.sqrt(dx**2 + dy**2)
                
                if distance < DETECTION_RADIUS and distance < closest_distance:
                    closest_sugar = sugar
                    closest_distance = distance
        
        # Update target if sugar is found within detection radius
        if closest_sugar and self.needs_to_eat():
            self.target = (closest_sugar[0], closest_sugar[1])
            return True  # Indicate that the target was updated
        
        return False  # Indicate that no sugar was found within detection radius
                
    def move(self):
        if self.target:
            # Move towards the target location
            dx = self.target[0] - self.x
            dy = self.target[1] - self.y
            distance = math.sqrt(dx**2 + dy**2)
            
            if distance < ANT_SPEED:
                # Ant has reached the target
                self.x, self.y = self.target
                self.target = None
            else:
                # Move towards target
                self.direction = math.atan2(dy, dx)
        else:
            # Random movement if no target
            self.direction += random.uniform(-self.turn_angle, self.turn_angle)

        # Move the ant
        self.x += ANT_SPEED * math.cos(self.direction)
        self.y += ANT_SPEED * math.sin(self.direction)

        # Ensure the ant stays within the game area boundaries
        self.x = max(0, min(self.x, GAME_WIDTH))
        self.y = max(0, min(self.y, HEIGHT))

        # Decrease health over time
        self.health -= HEALTH_DECREASE_RATE

        # Increase lifespan
        self.lifespan += 1

    def needs_to_eat(self):
        return self.health < self.initial_health

    def eat_sugar(self):
        if self.needs_to_eat():
            self.health = min(self.health + HEALTH_INCREASE_AMOUNT, self.max_health)

    def is_alive(self):
        return self.health > 0

# SugarScape class
class SugarScape:
    def __init__(self):
        self.sugar_spots = [(200, 350), (500, 350)]
        self.ants = [Ant(random.randint(0, GAME_WIDTH), random.randint(0, HEIGHT)) for _ in range(NUM_ANTS)]
        self.sugar_patches = self.initialize_sugar_patches()
        self.consumed_sugar_count = 0
        self.dead_ants_count = 0
        self.next_sugar_time = pygame.time.get_ticks() + NEW_SUGAR_INTERVAL
        self.communicated_locations = []  # List to store communicated locations
        self.total_lifespan_of_dead_ants = 0  # Track the total lifespan of dead ants
        self.false_broadcaster = random.choice(self.ants)  # Select one ant to broadcast false locations
        self.broadcast_time = pygame.time.get_ticks() + 1000  # Set a specific time for false broadcast (10 seconds from start)

    def initialize_sugar_patches(self):
        patches = []
        for (x, y) in self.sugar_spots:
            for n in range(SUGAR_MAX):
                square_x = x + (n % 10) * SQUARE_SIZE - 5 * SQUARE_SIZE
                square_y = y + (n // 10) * SQUARE_SIZE - 5 * SQUARE_SIZE
                patches.append([square_x, square_y, True])  # True indicates sugar is available
        return patches

    def update(self):
        current_time = pygame.time.get_ticks()
        alive_ants = []
        for ant in self.ants:
            if ant.is_alive():
                # Always check for sugar within detection radius
                sugar_detected = ant.detect_sugar(self.sugar_patches)
                
                # If no sugar detected within radius and no current target, use communicated target
                if not sugar_detected and not ant.target and ant.needs_to_eat():
                    if ant.communicated_target:
                        ant.target = ant.communicated_target
                        ant.communicated_target = None
                
                ant.move()
                
                # Check if ant has reached sugar after moving
                for sugar in self.sugar_patches:
                    if sugar[2]:  # Sugar is available
                        dx = sugar[0] - ant.x
                        dy = sugar[1] - ant.y
                        dist = math.sqrt(dx ** 2 + dy ** 2)
                        if dist < SUGAR_RADIUS and ant.needs_to_eat():
                            sugar[2] = False  # Mark sugar as consumed
                            self.consumed_sugar_count += 1
                            ant.eat_sugar()
                            self.broadcast_sugar_location(ant, sugar[0], sugar[1])
                            break
                
                # Broadcast false sugar location at a specific time
                if ant == self.false_broadcaster and current_time >= self.broadcast_time:
                    self.broadcast_sugar_location(ant, None, None, false_location=True)
                    self.broadcast_time += 10000  # Schedule next broadcast 10 seconds later

                alive_ants.append(ant)
            else:
                self.dead_ants_count += 1
                self.total_lifespan_of_dead_ants += ant.lifespan

        self.ants = alive_ants

    def broadcast_sugar_location(self, ant, sugar_x, sugar_y, false_location=False):
        # Determine if the location to broadcast is true or false
        if false_location:
            broadcast_x = random.randint(0, GAME_WIDTH)  # False location
            broadcast_y = random.randint(0, HEIGHT)  # False location
        else:
            broadcast_x, broadcast_y = sugar_x, sugar_y  # True location

        for other_ant in self.ants:
            if other_ant != ant:
                dx = other_ant.x - ant.x
                dy = other_ant.y - ant.y
                dist = math.sqrt(dx ** 2 + dy ** 2)
                if dist < COMMUNICATION_RADIUS and not other_ant.target:  # Only update if the other ant has no target
                    other_ant.communicated_target = (broadcast_x, broadcast_y)
        # Add the communicated location to the list for debugging
        self.communicated_locations.append((broadcast_x, broadcast_y))

    def add_new_sugar_patch(self):
        x = random.randint(0, GAME_WIDTH)
        y = random.randint(0, HEIGHT)
        for n in range(SUGAR_MAX):
            square_x = x + (n % 10) * SQUARE_SIZE - 5 * SQUARE_SIZE
            square_y = y + (n // 10) * SQUARE_SIZE - 5 * SQUARE_SIZE
            self.sugar_patches.append([square_x, square_y, True])

    def draw(self, screen):
        screen.fill(WHITE)
        # Draw sugar patches
        for sugar in self.sugar_patches:
            if sugar[2]:  # Only draw available sugar
                pygame.draw.rect(screen, GREEN, (sugar[0], sugar[1], SQUARE_SIZE, SQUARE_SIZE))
            else:  # Draw a yellow patch where sugar was consumed
                pygame.draw.rect(screen, YELLOW, (sugar[0], sugar[1], SQUARE_SIZE, SQUARE_SIZE))
        # Draw ants
        for ant in self.ants:
            if ant == self.false_broadcaster:
                pygame.draw.circle(screen, GREEN, (int(ant.x), int(ant.y)), ANT_SIZE)
            else:
                pygame.draw.circle(screen, RED, (int(ant.x), int(ant.y)), ANT_SIZE)
        # Draw communicated locations as red squares
        for loc in self.communicated_locations:
            pygame.draw.rect(screen, RED, (loc[0], loc[1], SQUARE_SIZE, SQUARE_SIZE))

    def get_analytics_data(self):
        average_lifespan = self.total_lifespan_of_dead_ants / self.dead_ants_count if self.dead_ants_count > 0 else 0
        return {
            'Total Sugar Patches': len(self.sugar_patches),
            'Consumed Sugar': self.consumed_sugar_count,
            'Remaining Sugar': len([s for s in self.sugar_patches if s[2]]),
            'Number of Ants': len(self.ants),
            'Dead Ants': self.dead_ants_count,
            'Average Lifespan': average_lifespan,
        }

# Main function
def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("SugarScape Simulation with Analytics")
    clock = pygame.time.Clock()

    sugarscape = SugarScape()

    font = pygame.font.Font(None, 24)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        sugarscape.update()

        # Draw game area
        game_surface = pygame.Surface((GAME_WIDTH, HEIGHT))
        sugarscape.draw(game_surface)
        screen.blit(game_surface, (0, 0))

        # Draw analytics area
        analytics_surface = pygame.Surface((ANALYTICS_WIDTH, HEIGHT))
        analytics_surface.fill(WHITE)
        pygame.draw.line(analytics_surface, GRAY, (0, 0), (0, HEIGHT), 3)  # Draw border line

        analytics_data = sugarscape.get_analytics_data()
        y_offset = 20
        for key, value in analytics_data.items():
            text = font.render(f"{key}: {value}", True, BLACK)
            analytics_surface.blit(text, (10, y_offset))
            y_offset += 30

        screen.blit(analytics_surface, (GAME_WIDTH, 0))

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()

if __name__ == "__main__":
    main()
