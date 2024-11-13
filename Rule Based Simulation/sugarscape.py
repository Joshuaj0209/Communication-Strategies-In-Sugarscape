import random
import pygame
import math
from constants import *
# from ant import Ant
import numpy as np
from BaselineAnt import BaselineAnt

class SugarScape:
    def __init__(self, shared_agent=None):
        padding = 120  # Padding from the edges
        patch_size = int(math.sqrt(SUGAR_MAX)) * SQUARE_SIZE  # Size of the entire sugar patch

        # Top left and bottom right sugar patches with padding
        self.sugar_spots = [
            (padding + patch_size // 2, padding + patch_size // 2),  # Top left
            (GAME_WIDTH - padding - patch_size // 2, HEIGHT - padding - patch_size // 2)  # Bottom right
        ]

        # Initialize ants
        # self.ants = [Ant(random.randint(0, GAME_WIDTH), random.randint(0, HEIGHT), shared_agent, ant_id=i) for i in range(NUM_ANTS)]
        self.ants = [BaselineAnt(random.randint(0, GAME_WIDTH), random.randint(0, HEIGHT), ant_id=i) for i in range(NUM_ANTS)]

        self.all_ants = self.ants.copy()  # Keep a copy of all ants

        self.sugar_patches = self.initialize_sugar_patches()
        self.consumed_sugar_count = 0
        self.dead_ants_count = 0
        self.next_sugar_time = NEW_SUGAR_INTERVAL
        self.communicated_locations = {}  # Store locations with their communication counts
        self.total_lifespan_of_dead_ants = 0

        # Choose two false broadcaster ants
        self.false_broadcasters = random.sample(self.ants, 2)  # NB: Change back to 3 if using 25 ants
         # Set the is_false_broadcaster flag to True for selected ants
        for ant in self.false_broadcasters:
            ant.is_false_broadcaster = True

        # Initialize broadcast times for each false broadcaster
        self.broadcast_times = {ant: 600 for ant in self.false_broadcasters}
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

        self.lifespan_of_dead_ants = []     # List to store lifespans of dead ants
        self.lifespan_of_alive_ants = []    # List to store lifespans of currently alive ants


    def initialize_sugar_patches(self):
        patches = []
        for (x, y) in self.sugar_spots:
            patch = {
                'x': x,
                'y': y,
                'count': 70,  # Starting sugar count
                'radius': SUGAR_PATCH_RADIUS
            }
            patches.append(patch)
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
                
                # self.lifespan_of_alive_ants.append(ant.lifespan)

            else:
                self.dead_ants_count += 1
                self.total_lifespan_of_dead_ants += ant.lifespan
                self.lifespan_of_dead_ants.append(ant.lifespan)  # Add to dead lifespans

        self.ants = alive_ants

        if current_time >= self.next_sugar_time:
            self.add_new_sugar_patch()
            self.next_sugar_time += NEW_SUGAR_INTERVAL



    def add_new_sugar_patch(self):
        max_attempts = 100
        min_distance_sugar = 180  # Minimum distance from existing sugar patches
        min_distance_false = 150  # Minimum distance from historical false locations
        padding = 20

        for attempt in range(max_attempts):
            x = random.randint(padding + SUGAR_PATCH_RADIUS, GAME_WIDTH - padding - SUGAR_PATCH_RADIUS)
            y = random.randint(padding + SUGAR_PATCH_RADIUS, HEIGHT - padding - SUGAR_PATCH_RADIUS)

            # Check distance from existing sugar patches
            too_close_sugar = any(
                math.hypot(x - sugar['x'], y - sugar['y']) < min_distance_sugar for sugar in self.sugar_patches
            )

            # Check distance from historical false locations
            too_close_false = any(
                math.hypot(x - false_loc[0], y - false_loc[1]) < min_distance_false for false_loc in self.historical_false_locations
            )

            if not too_close_sugar and not too_close_false:
                patch = {'x': x, 'y': y, 'count': 70, 'radius': SUGAR_PATCH_RADIUS}
                self.sugar_patches.append(patch)
                # print(f"New sugar patch added at ({x}, {y}) on attempt {attempt + 1}.")
                break
        else:
            # Handle the case where a valid location wasn't found after max_attempts
            # print(f"Failed to add a new sugar patch after {max_attempts} attempts.")
            pass




    def draw(self, screen):
        screen.fill(WHITE)

        font = pygame.font.Font(None, 24)
     
        # Draw the sugar patches
        for sugar in self.sugar_patches:
            if sugar['count'] > 0:
                color = GREEN
            else:
                color = GRAY  # Use a different color for depleted patches
            pygame.draw.circle(screen, color, (int(sugar['x']), int(sugar['y'])), sugar['radius'])
            
            # Draw the sugar count (only if count > 0)
            if sugar['count'] > 0:
                count_text = font.render(str(sugar['count']), True, BLACK)
            else:
                count_text = font.render("0", True, RED)  # Indicate depleted with "0" in red
            
            text_rect = count_text.get_rect(center=(int(sugar['x']), int(sugar['y'])))
            screen.blit(count_text, text_rect)

        # Draw ants and their communication radius
        for ant in self.ants:
            # Draw the communication radius as a circle around the ant
            pygame.draw.circle(screen, (135, 206, 235, 128), (int(ant.x), int(ant.y)), COMMUNICATION_RADIUS, 1)  # Light blue, semi-transparent
            
            # Draw the ant itself
            # color = GREEN if ant in self.false_broadcasters else RED
            color = RED
            pygame.draw.circle(screen, color, (int(ant.x), int(ant.y)), ANT_SIZE)

            # Render and draw the ant's ID number on top of it
            ant_id_text = font.render(str(ant.id), True, BLACK)  # Convert ant.id to string
            text_rect = ant_id_text.get_rect(center=(int(ant.x), int(ant.y) - ANT_SIZE - 10))  # Position text above the ant
            # screen.blit(ant_id_text, text_rect)
            
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
        # Collect lifespans of alive ants at the end of the episode
        for ant in self.ants:
            self.lifespan_of_alive_ants.append(ant.lifespan)

        # Combine lifespans of dead and alive ants
        all_lifespans = self.lifespan_of_dead_ants + self.lifespan_of_alive_ants

        if not all_lifespans:
            average_lifespan = 0
        else:
            # Convert to NumPy array for percentile calculations
            lifespans_array = np.array(all_lifespans)

            # Calculate Q1 and Q3
            Q1 = np.percentile(lifespans_array, 25)
            Q3 = np.percentile(lifespans_array, 75)
            IQR = Q3 - Q1

            # Define bounds for acceptable lifespans
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR

            # Filter lifespans within the bounds
            filtered_lifespans = lifespans_array[(lifespans_array >= lower_bound) & (lifespans_array <= upper_bound)]

            if len(filtered_lifespans) == 0:
                # If all lifespans are outliers, fallback to median
                average_lifespan = np.median(lifespans_array)
            else:
                # Calculate the mean of the filtered lifespans
                average_lifespan = np.mean(filtered_lifespans)

        # Reset lifespan lists for the next episode
        self.lifespan_of_dead_ants = []
        self.lifespan_of_alive_ants = []

        # Tracking statistics
        return {
            'Total Sugar Patches': len(self.sugar_patches),
            'Consumed Sugar': self.consumed_sugar_count,
            'Number of Ants': len(self.ants),
            'Dead Ants': self.dead_ants_count,
            'Average Lifespan': average_lifespan,
            'True Positives': self.true_positives,
            'False Positives': self.false_positives,
            'Exploits': self.exploit_count,
            'Explores': self.explore_count
        }


