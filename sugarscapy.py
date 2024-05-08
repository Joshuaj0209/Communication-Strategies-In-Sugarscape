import pygame
import random
import math

# Constants
WIDTH, HEIGHT = 800, 600
SUGAR_RADIUS = 20  # Radius to define sugar patch area
ANT_SIZE = 10
ANT_SPEED = 1
NUM_ANTS = 20
SUGAR_MAX = 100  # Max sugar per patch
SUGAR_REGENERATION_RATE = 0.1
SQUARE_SIZE = 5  # Size of each sugar square

# Colors
WHITE = (255, 255, 255)
BROWN = (139, 69, 19)
RED = (255, 0, 0)
GREEN = (0, 255, 0)  # Color for sugar squares

# Ant class
class Ant:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.direction = random.uniform(0, 2 * math.pi)  # Random initial direction
        self.target_sugar = None

    def move(self):
        if self.target_sugar:
            # Move towards the target sugar
            dx = self.target_sugar[0] - self.x
            dy = self.target_sugar[1] - self.y
            dist = math.sqrt(dx**2 + dy**2)
            if dist > ANT_SPEED:
                self.x += ANT_SPEED * dx / dist
                self.y += ANT_SPEED * dy / dist
            else:
                # Consume sugar and look for next closest sugar
                self.x, self.y = self.target_sugar
                self.target_sugar = None
        else:
            # Move randomly
            self.direction = random.uniform(0, 2 * math.pi)
            self.x += ANT_SPEED * math.cos(self.direction)
            self.y += ANT_SPEED * math.sin(self.direction)

        # Ensure the ant stays within the screen boundaries
        self.x = max(0, min(self.x, WIDTH))
        self.y = max(0, min(self.y, HEIGHT))

    def find_closest_sugar(self, sugar_patches):
        min_distance = float('inf')
        closest_sugar = None
        for sugar in sugar_patches:
            if sugar[2]:  # Check if sugar is still available
                dx = sugar[0] - self.x
                dy = sugar[1] - self.y
                distance = math.sqrt(dx**2 + dy**2)
                if distance < min_distance:
                    min_distance = distance
                    closest_sugar = sugar

        self.target_sugar = (closest_sugar[0], closest_sugar[1]) if closest_sugar else None
        if closest_sugar:
            closest_sugar[2] = False  # Mark this sugar as consumed

# SugarScape class
class SugarScape:
    def __init__(self):
        self.sugar_spots = [(200, 300), (600, 300)]
        self.ants = [Ant(random.randint(0, WIDTH), random.randint(0, HEIGHT)) for _ in range(NUM_ANTS)]
        self.sugar_patches = self.initialize_sugar_patches()

    def initialize_sugar_patches(self):
        patches = []
        for (x, y) in self.sugar_spots:
            for n in range(SUGAR_MAX):
                square_x = x + (n % 10) * SQUARE_SIZE - 5 * SQUARE_SIZE
                square_y = y + (n // 10) * SQUARE_SIZE - 5 * SQUARE_SIZE
                patches.append([square_x, square_y, True])  # True indicates sugar is available
        return patches

    def update(self):
        for ant in self.ants:
            if not ant.target_sugar:
                ant.find_closest_sugar(self.sugar_patches)
            ant.move()

    def draw(self, screen):
        screen.fill(WHITE)
        # Draw sugar patches
        for sugar in self.sugar_patches:
            if sugar[2]:  # Only draw available sugar
                pygame.draw.rect(screen, GREEN, (sugar[0], sugar[1], SQUARE_SIZE, SQUARE_SIZE))
        # Draw ants
        for ant in self.ants:
            pygame.draw.circle(screen, RED, (int(ant.x), int(ant.y)), ANT_SIZE)

# Main function
def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("SugarScape Simulation")
    clock = pygame.time.Clock()

    sugarscape = SugarScape()

    running = True
    while running:
        for event in pygame.event.get():
            if event.type is pygame.QUIT:
                running = False

        sugarscape.update()
        sugarscape.draw(screen)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()

if __name__ == "__main__":
    main()
