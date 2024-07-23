import pygame
import random
import math

# Constants
GAME_WIDTH, HEIGHT = 700, 700  # Width of the game area
ANALYTICS_WIDTH = 300  # Width of the analytics area (increased for better readability)
WIDTH = GAME_WIDTH + ANALYTICS_WIDTH  # Total width
SUGAR_RADIUS = 20  # Radius to define proximity for sugar detection
ANT_SIZE = 10
ANT_SPEED = 1
NUM_ANTS = 20
SUGAR_MAX = 100  # Max sugar per patch
SUGAR_REGENERATION_RATE = 0.0002
SQUARE_SIZE = 5  # Size of each sugar square

# Ant health constants
INITIAL_HEALTH = 100
MAX_HEALTH = 150
HEALTH_DECREASE_RATE = 0.1
HEALTH_INCREASE_AMOUNT = 20

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
        self.max_health = MAX_HEALTH

    def move(self):
        # Smooth random movement
        self.direction += random.uniform(-self.turn_angle, self.turn_angle)
        self.x += ANT_SPEED * math.cos(self.direction)
        self.y += ANT_SPEED * math.sin(self.direction)

        # Ensure the ant stays within the game area boundaries
        self.x = max(0, min(self.x, GAME_WIDTH))
        self.y = max(0, min(self.y, HEIGHT))

        # Decrease health over time
        self.health -= HEALTH_DECREASE_RATE

    def eat_sugar(self):
        self.health = min(self.health + HEALTH_INCREASE_AMOUNT, self.max_health)  # Increase health but not above max

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

    def initialize_sugar_patches(self):
        patches = []
        for (x, y) in self.sugar_spots:
            for n in range(SUGAR_MAX):
                square_x = x + (n % 10) * SQUARE_SIZE - 5 * SQUARE_SIZE
                square_y = y + (n // 10) * SQUARE_SIZE - 5 * SQUARE_SIZE
                patches.append([square_x, square_y, True])  # True indicates sugar is available
        return patches

    def update(self):
        alive_ants = []
        for ant in self.ants:
            if ant.is_alive():
                for sugar in self.sugar_patches:
                    if sugar[2]:  # Sugar is available
                        dx = sugar[0] - ant.x
                        dy = sugar[1] - ant.y
                        dist = math.sqrt(dx ** 2 + dy ** 2)
                        if dist < SUGAR_RADIUS:
                            sugar[2] = False  # Mark sugar as consumed
                            self.consumed_sugar_count += 1
                            ant.eat_sugar()
                            break

                ant.move()  # Move ant whether or not sugar was found
                alive_ants.append(ant)
            else:
                self.dead_ants_count += 1  # Count the dead ant

        self.ants = alive_ants  # Update the list of alive ants

        # Regenerate sugar over time
        for sugar in self.sugar_patches:
            if not sugar[2]:  # If the sugar is consumed
                if random.random() < SUGAR_REGENERATION_RATE:
                    sugar[2] = True  # Regenerate sugar

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
            pygame.draw.circle(screen, RED, (int(ant.x), int(ant.y)), ANT_SIZE)

    def get_analytics_data(self):
        return {
            'Total Sugar Patches': len(self.sugar_patches),
            'Consumed Sugar': self.consumed_sugar_count,
            'Remaining Sugar': len([s for s in self.sugar_patches if s[2]]),
            'Number of Ants': len(self.ants),
            'Dead Ants': self.dead_ants_count,
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
