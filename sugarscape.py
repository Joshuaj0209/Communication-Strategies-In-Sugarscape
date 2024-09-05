import random
import pygame
import math
from constants import *
from ant import Ant

class SugarScape:
    def __init__(self):
        padding = 120  # Padding from the edges
        patch_size = int(math.sqrt(SUGAR_MAX)) * SQUARE_SIZE  # Size of the entire sugar patch

        # Top left and bottom right sugar patches with padding
        self.sugar_spots = [
            (padding + patch_size // 2, padding + patch_size // 2),  # Top left
            (GAME_WIDTH - padding - patch_size // 2, HEIGHT - padding - patch_size // 2)  # Bottom right
        ]

        # Initialize ants
        self.ants = [Ant(random.randint(0, GAME_WIDTH), random.randint(0, HEIGHT)) for _ in range(NUM_ANTS)]
        self.sugar_patches = self.initialize_sugar_patches()
        self.consumed_sugar_count = 0
        self.dead_ants_count = 0
        self.next_sugar_time = pygame.time.get_ticks() + NEW_SUGAR_INTERVAL
        self.communicated_locations = {}  # Store locations with their communication counts
        self.total_lifespan_of_dead_ants = 0

        # Choose a false broadcaster ant
        self.false_broadcaster = random.choice(self.ants)
        self.broadcast_time = pygame.time.get_ticks() + 1000

        # Tracking statistics for positive/negative broadcasts
        self.true_positives = 0
        self.true_negatives = 0
        self.false_positives = 0
        self.false_negatives = 0

        # Provide each ant with a reference to the Sugarscape instance
        for ant in self.ants:
            ant.sugarscape = self

    def initialize_sugar_patches(self):
        patches = []
        grid_size = int(math.sqrt(SUGAR_MAX))
        half_grid = grid_size // 2
        
        for (x, y) in self.sugar_spots:
            # Calculate the center of the patch
            center_x = x
            center_y = y
            
            for n in range(SUGAR_MAX):
                square_x = x + (n % grid_size) * SQUARE_SIZE - half_grid * SQUARE_SIZE
                square_y = y + (n // grid_size) * SQUARE_SIZE - half_grid * SQUARE_SIZE
                # Store the sugar location along with the center of the patch
                patches.append([square_x, square_y, True, (center_x, center_y)])
        
        return patches

    def update(self):
        current_time = pygame.time.get_ticks()
        alive_ants = []

        for ant in self.ants:
            if ant.is_alive():
                ant.move(self.sugar_patches, self)

                for sugar in self.sugar_patches:
                    if sugar[2]:  # Check if sugar is available
                        dx = sugar[0] - ant.x
                        dy = sugar[1] - ant.y
                        dist = math.sqrt(dx ** 2 + dy ** 2)
                        if dist < SUGAR_RADIUS and ant.needs_to_eat():
                            sugar[2] = False  # Mark sugar as consumed
                            self.consumed_sugar_count += 1
                            ant.eat_sugar()
                            # Ant broadcasts sugar location, handled within the Ant class
                            ant.broadcast_sugar_location()
                
                # False broadcaster logic
                if ant == self.false_broadcaster and current_time >= self.broadcast_time:
                    ant.false_broadcast_location = None  # Reset for new false location
                    self.broadcast_time += 10000  # Reset interval

                alive_ants.append(ant)
            else:
                self.dead_ants_count += 1
                self.total_lifespan_of_dead_ants += ant.lifespan

        self.ants = alive_ants

        if current_time >= self.next_sugar_time:
            self.add_new_sugar_patch()
            self.next_sugar_time += NEW_SUGAR_INTERVAL

    def add_new_sugar_patch(self):
        max_attempts = 100  
        min_distance = 100  

        grid_size = int(math.sqrt(SUGAR_MAX)) 
        half_grid = grid_size // 2

        for attempt in range(max_attempts):
            x = random.randint(0, GAME_WIDTH)
            y = random.randint(0, HEIGHT)
            
            too_close = any(math.sqrt((x - sugar[0]) ** 2 + (y - sugar[1]) ** 2) < min_distance for sugar in self.sugar_patches)
            
            if not too_close:
                # Calculate the center of the patch
                center_x = x
                center_y = y
                
                for n in range(SUGAR_MAX):
                    square_x = x + (n % grid_size) * SQUARE_SIZE - half_grid * SQUARE_SIZE
                    square_y = y + (n // grid_size) * SQUARE_SIZE - half_grid * SQUARE_SIZE
                    # Store the sugar location along with the center of the patch
                    self.sugar_patches.append([square_x, square_y, True, (center_x, center_y)])
                break

    def draw(self, screen):
        screen.fill(WHITE)
        for sugar in self.sugar_patches:
            if sugar[2]:
                pygame.draw.rect(screen, GREEN, (sugar[0], sugar[1], SQUARE_SIZE, SQUARE_SIZE))
            else:
                pygame.draw.rect(screen, YELLOW, (sugar[0], sugar[1], SQUARE_SIZE, SQUARE_SIZE))
        for ant in self.ants:
            color = GREEN if ant == self.false_broadcaster else RED
            pygame.draw.circle(screen, color, (int(ant.x), int(ant.y)), ANT_SIZE)
        for loc, count in self.communicated_locations.items():
            base_intensity = 150  # Start with darker red 
            color_intensity = max(0, base_intensity - count * 40)  # Decrease intensity by 20 per communication
            color = (255, color_intensity, color_intensity)  # Darken red progressively
            pygame.draw.rect(screen, color, (loc[0], loc[1], SQUARE_SIZE, SQUARE_SIZE))

    def get_analytics_data(self):
        average_lifespan = self.total_lifespan_of_dead_ants / self.dead_ants_count if self.dead_ants_count > 0 else 0
        return {
            'Total Sugar Patches': len(self.sugar_patches),
            'Consumed Sugar': self.consumed_sugar_count,
            'Remaining Sugar': len([s for s in self.sugar_patches if s[2]]),
            'Number of Ants': len(self.ants),
            'Dead Ants': self.dead_ants_count,
            'Average Lifespan': average_lifespan,
            'True Positives': self.true_positives,
            'False Positives': self.false_positives,
        }
