import pygame
import random
import math

# Constants
WIDTH, HEIGHT = 800, 600
SUGAR_RADIUS = 20
ANT_SIZE = 10
ANT_SPEED = 1
NUM_ANTS = 20
SUGAR_MAX = 100
SUGAR_REGENERATION_RATE = 0.1

# Colors
WHITE = (255, 255, 255)
BROWN = (139, 69, 19)
RED = (255, 0, 0)

# Ant class
class Ant:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.direction = random.uniform(0, 2*math.pi)  # Random initial direction
        self.inertia_countdown = random.randint(10, 30)  # Initial inertia countdown

    def move(self, discovered_sugar):
            if discovered_sugar:
                # Move towards the discovered sugar spot
                dx = discovered_sugar[0] - self.x
                dy = discovered_sugar[1] - self.y
                dist = math.sqrt(dx**2 + dy**2)
                if dist > ANT_SPEED:
                    self.x += ANT_SPEED * dx / dist
                    self.y += ANT_SPEED * dy / dist
                else:
                    self.x = discovered_sugar[0]
                    self.y = discovered_sugar[1]
            else:
                # Move randomly
                if self.inertia_countdown == 0:
                    self.direction = random.uniform(0, 2*math.pi)
                    self.inertia_countdown = random.randint(10, 30)
                else:
                    self.x += ANT_SPEED * math.cos(self.direction)
                    self.y += ANT_SPEED * math.sin(self.direction)
                    self.inertia_countdown -= 1

                # Ensure the ant stays within the screen boundaries
                self.x = max(0, min(self.x, WIDTH))
                self.y = max(0, min(self.y, HEIGHT))



# SugarScape class
class SugarScape:
    def __init__(self):
        self.sugar_spots = [(200, 300), (600, 300)]  # Two circular positions
        self.ants = [Ant(random.randint(0, WIDTH), random.randint(0, HEIGHT)) for _ in range(NUM_ANTS)]
        self.sugar_levels = [SUGAR_MAX for _ in range(len(self.sugar_spots))]
        self.discovered_sugar = None

    def update(self):
        for ant in self.ants:
            ant.move(self.discovered_sugar)

        # Check if ants have found sugar
        for ant in self.ants:
            for sugar_x, sugar_y in self.sugar_spots:
                if math.sqrt((ant.x - sugar_x)**2 + (ant.y - sugar_y)**2) < SUGAR_RADIUS:
                    # Consume sugar if available
                    sugar_index = self.sugar_spots.index((sugar_x, sugar_y))
                    if self.sugar_levels[sugar_index] > 0:
                        self.sugar_levels[sugar_index] -= 1
                        self.discovered_sugar = (sugar_x, sugar_y)

        # Regenerate sugar
        for i in range(len(self.sugar_spots)):
            self.sugar_levels[i] = min(self.sugar_levels[i] + SUGAR_REGENERATION_RATE, SUGAR_MAX)

    def find_nearest_sugar(self, x, y):
        nearest_sugar = None
        min_dist = float('inf')
        for sugar_x, sugar_y in self.sugar_spots:
            dist = math.sqrt((x - sugar_x)**2 + (y - sugar_y)**2)
            if dist < min_dist:
                nearest_sugar = (sugar_x, sugar_y)
                min_dist = dist
        return nearest_sugar

    def draw(self, screen):
        screen.fill(WHITE)
        # Draw sugar
        for i, (x, y) in enumerate(self.sugar_spots):
            pygame.draw.circle(screen, BROWN, (int(x), int(y)), SUGAR_RADIUS)
            font = pygame.font.Font(None, 36)
            text = font.render(str(int(self.sugar_levels[i])), True, RED)
            text_rect = text.get_rect(center=(x, y))
            screen.blit(text, text_rect)
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
            if event.type == pygame.QUIT:
                running = False

        sugarscape.update()
        sugarscape.draw(screen)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()

if __name__ == "__main__":
    main()
