# sugarscape.py

import random
import pygame
import math
from constants import *
from ant import Ant

class SugarScape:
    def __init__(self):
        self.sugar_spots = [(200, 350), (500, 350)]
        self.ants = [Ant(random.randint(0, GAME_WIDTH), random.randint(0, HEIGHT)) for _ in range(NUM_ANTS)]
        self.sugar_patches = self.initialize_sugar_patches()
        self.consumed_sugar_count = 0
        self.dead_ants_count = 0
        self.next_sugar_time = pygame.time.get_ticks() + NEW_SUGAR_INTERVAL
        self.communicated_locations = []
        self.total_lifespan_of_dead_ants = 0
        self.false_broadcaster = random.choice(self.ants)
        self.broadcast_time = pygame.time.get_ticks() + 1000

    def initialize_sugar_patches(self):
        patches = []
        grid_size = int(math.sqrt(SUGAR_MAX))  
        half_grid = grid_size // 2
        for (x, y) in self.sugar_spots:
            for n in range(SUGAR_MAX):
                square_x = x + (n % grid_size) * SQUARE_SIZE - half_grid * SQUARE_SIZE
                square_y = y + (n // grid_size) * SQUARE_SIZE - half_grid * SQUARE_SIZE
                patches.append([square_x, square_y, True])
        return patches

    def update(self):
        current_time = pygame.time.get_ticks()
        alive_ants = []

        for ant in self.ants:
            if ant.is_alive():
                sugar_detected = ant.detect_sugar(self.sugar_patches)
                if not sugar_detected and not ant.target and ant.needs_to_eat():
                    if ant.communicated_target:
                        ant.target = ant.communicated_target
                        ant.communicated_target = None
                ant.move()

                for sugar in self.sugar_patches:
                    if sugar[2]:
                        dx = sugar[0] - ant.x
                        dy = sugar[1] - ant.y
                        dist = math.sqrt(dx ** 2 + dy ** 2)
                        if dist < SUGAR_RADIUS and ant.needs_to_eat():
                            sugar[2] = False
                            self.consumed_sugar_count += 1
                            ant.eat_sugar()
                            self.broadcast_sugar_location(ant, sugar[0], sugar[1])
                            break
                
                if ant == self.false_broadcaster and current_time >= self.broadcast_time:
                    self.broadcast_sugar_location(ant, None, None, false_location=True)
                    self.broadcast_time += 10000

                alive_ants.append(ant)
            else:
                self.dead_ants_count += 1
                self.total_lifespan_of_dead_ants += ant.lifespan

        self.ants = alive_ants

        # Check if it's time to add a new sugar patch
        if current_time >= self.next_sugar_time:
            self.add_new_sugar_patch()
            self.next_sugar_time += NEW_SUGAR_INTERVAL

    def broadcast_sugar_location(self, ant, sugar_x, sugar_y, false_location=False):
        if false_location:
            broadcast_x = random.randint(0, GAME_WIDTH)
            broadcast_y = random.randint(0, HEIGHT)
        else:
            broadcast_x, broadcast_y = sugar_x, sugar_y

        for other_ant in self.ants:
            if other_ant != ant:
                dx = other_ant.x - ant.x
                dy = other_ant.y - ant.y
                dist = math.sqrt(dx ** 2 + dy ** 2)
                if dist < COMMUNICATION_RADIUS and not other_ant.target:
                    other_ant.communicated_target = (broadcast_x, broadcast_y)
        self.communicated_locations.append((broadcast_x, broadcast_y))

    def add_new_sugar_patch(self):
        max_attempts = 100  # Limit the number of attempts to find a suitable location
        min_distance = 100  # Minimum distance from existing sugar patches

        grid_size = int(math.sqrt(SUGAR_MAX)) 
        half_grid = grid_size // 2

        for attempt in range(max_attempts):
            x = random.randint(0, GAME_WIDTH)
            y = random.randint(0, HEIGHT)
            
            # Check if the new patch is too close to existing patches
            too_close = any(math.sqrt((x - sugar[0]) ** 2 + (y - sugar[1]) ** 2) < min_distance for sugar in self.sugar_patches)
            
            if not too_close:
                for n in range(SUGAR_MAX):
                    square_x = x + (n % grid_size) * SQUARE_SIZE - half_grid * SQUARE_SIZE
                    square_y = y + (n // grid_size) * SQUARE_SIZE - half_grid * SQUARE_SIZE
                    self.sugar_patches.append([square_x, square_y, True])
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
