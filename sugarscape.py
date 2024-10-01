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
        self.next_sugar_time = NEW_SUGAR_INTERVAL
        self.communicated_locations = {}  # Store locations with their communication counts
        self.total_lifespan_of_dead_ants = 0

        # Choose two false broadcaster ants
        self.false_broadcasters = random.sample(self.ants, 2)
        # Initialize broadcast times for each false broadcaster
        self.broadcast_times = {ant:600 for ant in self.false_broadcasters}
        self.false_broadcasters_locations = set()  # Track false locations
        self.historical_false_locations = set()  # Track all false locations historically


        # Tracking statistics for positive/negative broadcasts
        self.true_positives = 0
        self.true_negatives = 0
        self.false_positives = 0
        self.false_negatives = 0

        self.explore_count = 0
        self.exploit_count = 0

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

    def update(self, sim_time):
        current_time = sim_time
        alive_ants = []

        for ant in self.ants:
            if ant.is_alive():
                ant.move(self.sugar_patches, self, sim_time)
                alive_ants.append(ant)

                # Track false broadcast locations historically
                if ant in self.false_broadcasters and ant.false_broadcast_location:
                    self.false_broadcasters_locations.add(ant.false_broadcast_location)
                    self.historical_false_locations.add(ant.false_broadcast_location)  # Track all false locations
            else:
                self.dead_ants_count += 1
                self.total_lifespan_of_dead_ants += ant.lifespan

        self.ants = alive_ants

        if current_time >= self.next_sugar_time:
            self.add_new_sugar_patch()
            self.next_sugar_time += NEW_SUGAR_INTERVAL



    def add_new_sugar_patch(self):
        max_attempts = 100  
        min_distance = 150  

        grid_size = int(math.sqrt(SUGAR_MAX)) 
        half_grid = grid_size // 2

        patch_size = int(math.sqrt(SUGAR_MAX)) * SQUARE_SIZE  # Calculate patch size based on SUGAR_MAX
        padding = 20 

        for attempt in range(max_attempts):
            # Ensure x and y are within the allowed area, considering the patch size and padding
            x = random.randint(padding + patch_size // 2, GAME_WIDTH - padding - patch_size // 2)
            y = random.randint(padding + patch_size // 2, HEIGHT - padding - patch_size // 2)

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
        
        # Draw the sugar patches
        for sugar in self.sugar_patches:
            if sugar[2]:
                pygame.draw.rect(screen, GREEN, (sugar[0], sugar[1], SQUARE_SIZE, SQUARE_SIZE))
            else:
                pygame.draw.rect(screen, YELLOW, (sugar[0], sugar[1], SQUARE_SIZE, SQUARE_SIZE))
        
        # Draw ants and their communication radius
        for ant in self.ants:
            # Draw the communication radius as a circle around the ant
            pygame.draw.circle(screen, (135, 206, 235, 128), (int(ant.x), int(ant.y)), COMMUNICATION_RADIUS, 1)  # Light blue, semi-transparent
            
            # Draw the ant itself
            color = GREEN if ant in self.false_broadcasters else RED
            pygame.draw.circle(screen, color, (int(ant.x), int(ant.y)), ANT_SIZE)
        
        # Collect all false broadcast locations from false broadcasters
        false_locations = set()
        for ant in self.false_broadcasters:
            if ant.false_broadcast_location:
                false_locations.add(ant.false_broadcast_location)

        # Draw a red square at each false location
        for location in self.historical_false_locations:
            x, y = location
            pygame.draw.rect(screen, (255, 0, 0), pygame.Rect(int(x) - 3, int(y) - 3, 6, 6))


    def get_analytics_data(self):
        total_lifespan = self.total_lifespan_of_dead_ants  # Start with total lifespan of dead ants
        
        # Add the lifespan (age) of living ants
        for ant in self.ants:
            total_lifespan += ant.lifespan  # Add each living ant's current age

        total_ants = self.dead_ants_count + len(self.ants)  # Total number of ants, dead + alive
        average_lifespan = total_lifespan / total_ants if total_ants > 0 else 0  # Calculate average

        return {
            'Total Sugar Patches': len(self.sugar_patches),
            'Consumed Sugar': self.consumed_sugar_count,
            'Remaining Sugar': len([s for s in self.sugar_patches if s[2]]),
            'Number of Ants': len(self.ants),
            'Dead Ants': self.dead_ants_count,
            'Average Lifespan': average_lifespan,
            'True Positives': self.true_positives,
            'False Positives': self.false_positives,
            'Exploits': self.exploit_count,
            'Explores': self.explore_count
        }

