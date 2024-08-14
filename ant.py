import random
import math
import pygame
from constants import *

class Ant:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.direction = random.uniform(0, 2 * math.pi)
        self.turn_angle = math.pi / 8
        self.health = INITIAL_HEALTH
        self.initial_health = INITIAL_HEALTH
        self.max_health = MAX_HEALTH
        self.target = None
        self.communicated_targets = {}  # Dictionary to store communicated locations and their counts
        self.lifespan = 0
        self.next_target_selection_time = pygame.time.get_ticks() + TARGET_SELECTION_INTERVAL  # Initialize the time for the first target selection
        self.communicated_sugar_locations = []  # List to store sugar locations this ant has communicated
        self.following_true_location = False  # Track if the ant is following a true location
        self.following_false_location = False  # Track if the ant is following a false location

    def detect_sugar(self, sugar_patches):
        closest_sugar = None
        closest_distance = float('inf')

        for sugar in sugar_patches:
            if sugar[2]:  # Check if sugar is available
                dx = sugar[0] - self.x
                dy = sugar[1] - self.y
                distance = math.sqrt(dx**2 + dy**2)

                if distance < DETECTION_RADIUS and distance < closest_distance:
                    closest_sugar = sugar
                    closest_distance = distance

        if closest_sugar and self.needs_to_eat():
            self.target = (closest_sugar[0], closest_sugar[1])
            return True
        
        return False

    def select_new_target(self):
        if self.communicated_targets:
            best_target = None
            best_score = -float('inf')  # Start with the lowest possible score

            for (target_info, count) in self.communicated_targets.items():
                # Calculate the distance to the target
                dx = target_info[0] - self.x
                dy = target_info[1] - self.y
                distance = math.sqrt(dx**2 + dy**2)

                # Estimate the time to reach the target
                time_to_reach = distance / ANT_SPEED

                # Estimate health depletion over that time
                health_depletion = time_to_reach * HEALTH_DECREASE_RATE

                # Check if the ant can reach the target before dying
                if self.health > health_depletion:
                    # Calculate the score for this target
                    # The score is higher for targets that are closer and have been communicated more often
                    score = count / (distance*2 + 1)  # +1 to avoid division by zero

                    if score > best_score:
                        best_score = score
                        best_target = target_info

            if best_target:
                self.target = best_target[:2]
                if best_target[2] == "true":
                    self.following_true_location = True
                    self.following_false_location = False
                else:
                    self.following_true_location = False
                    self.following_false_location = True

    def move(self, sugar_patches, sugarscape):
        current_time = pygame.time.get_ticks()

        # Detect sugar and set target if available and needed
        sugar_detected = self.detect_sugar(sugar_patches)
        
        # If no sugar detected and the ant needs to eat, check for communicated targets
        if not sugar_detected and not self.target and self.needs_to_eat():
            # Check if it's time to select a new target
            if current_time >= self.next_target_selection_time:
                if self.communicated_targets:
                    self.select_new_target()
                    # Determine if the selection is true or false
                    if self.following_true_location:
                        sugarscape.true_positives += 1
                    elif self.following_false_location:
                        sugarscape.false_positives += 1
                else:
                    # No target selected means the ant denied all locations
                    if self.following_true_location:
                        sugarscape.false_negatives += 1
                    elif self.following_false_location:
                        sugarscape.true_negatives += 1

                self.next_target_selection_time += TARGET_SELECTION_INTERVAL

        # Move towards the target if one is selected
        if self.target:
            dx = self.target[0] - self.x
            dy = self.target[1] - self.y
            distance = math.sqrt(dx**2 + dy**2)

            if distance < ANT_SPEED:
                self.x, self.y = self.target
                self.target = None
            else:
                self.direction = math.atan2(dy, dx)
        else:
            # Continue moving randomly if no target
            self.direction += random.uniform(-self.turn_angle, self.turn_angle)

        # Update the ant's position
        self.x += ANT_SPEED * math.cos(self.direction)
        self.y += ANT_SPEED * math.sin(self.direction)

        # Keep the ant within the game boundaries
        self.x = max(0, min(self.x, GAME_WIDTH))
        self.y = max(0, min(self.y, HEIGHT))

        # Decrease health over time and increase lifespan
        self.health -= HEALTH_DECREASE_RATE
        self.lifespan += 1

    def needs_to_eat(self):
        return self.health < self.initial_health

    def eat_sugar(self):
        if self.needs_to_eat():
            self.health = min(self.health + HEALTH_INCREASE_AMOUNT, self.max_health)

    def is_alive(self):
        return self.health > 0
