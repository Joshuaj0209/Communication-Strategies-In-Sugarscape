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

        # Set the mean and standard deviation for the target selection interval
        self.mean_interval = 8000  # Mean interval of 8000ms
        self.std_deviation = 2000  # Standard deviation of 2000ms

        # Use a normal distribution for the first target selection interval
        self.target_selection_interval = max(500, random.gauss(self.mean_interval, self.std_deviation))
        self.next_target_selection_time = pygame.time.get_ticks() + self.target_selection_interval

        self.communicated_sugar_locations = []  # List of tuples: (sugar_location, communicated_ants)
        self.following_true_location = False  # Track if the ant is following a true location
        self.following_false_location = False  # Track if the ant is following a false location
        self.confirmed_false_locations = []  # List to store confirmed false locations
        self.confirmed_true_locations = []  # List to store confirmed true locations

        self.sugarscape = None  # Reference to the Sugarscape instance
        self.false_broadcast_location = None  # Store the current false location being broadcast
        self.target_patch_center = None  # Store the center of the sugar patch for broadcasting
        
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
            # Set the target patch center for broadcasting
            self.target_patch_center = closest_sugar[3]  # Use the center of the sugar patch
            return True
        
        return False

    def select_new_target(self, sugarscape):
        if self.communicated_targets:
            best_target = None
            best_score = -float('inf')  # Start with the lowest possible score

            for (target_info, count) in self.communicated_targets.items():
                # Skip confirmed false or true locations
                if target_info[:2] in self.confirmed_false_locations or target_info[:2] in self.confirmed_true_locations:
                    continue

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
                    score = count / (distance**3 + 1)  # +1 to avoid division by zero

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

    def broadcast_sugar_location(self, false_location=False):
        if false_location:
            # If this ant is one of the designated false broadcasters, broadcast the current false location
            if self in self.sugarscape.false_broadcasters:
                if not self.false_broadcast_location:
                    padding = 100
                    self.false_broadcast_location = (
                        random.randint(padding, GAME_WIDTH - padding),
                        random.randint(padding, HEIGHT - padding),
                    )
                broadcast_x, broadcast_y = self.false_broadcast_location
            else:
                broadcast_x, broadcast_y = None, None  # Should not happen for non-broadcasters
            location_type = "false"
        else:
            if self.target_patch_center:
                # Broadcast the center of the sugar patch
                broadcast_x, broadcast_y = self.target_patch_center
                location_type = "true"
            else:
                return  # No target to broadcast

        # Check if the sugar location has already been communicated by this ant
        communicated_location_entry = None
        for loc, ants in self.communicated_sugar_locations:
            if loc == (broadcast_x, broadcast_y):
                communicated_location_entry = (loc, ants)
                break

        # If this location hasn't been communicated, add it to the list
        if communicated_location_entry is None:
            communicated_location_entry = ((broadcast_x, broadcast_y), [])
            self.communicated_sugar_locations.append(communicated_location_entry)

        # Update the communication count for this location in Sugarscape
        if (broadcast_x, broadcast_y) in self.sugarscape.communicated_locations:
            self.sugarscape.communicated_locations[(broadcast_x, broadcast_y)] += 1
        else:
            self.sugarscape.communicated_locations[(broadcast_x, broadcast_y)] = 1

        # Broadcast to other ants within the communication radius
        for other_ant in self.sugarscape.ants:
            if other_ant != self:
                dx = other_ant.x - self.x
                dy = other_ant.y - self.y
                dist = math.sqrt(dx ** 2 + dy ** 2)

                # Only communicate if the other ant is within the communication radius
                if dist <= COMMUNICATION_RADIUS:
                    # Check if this other ant has already been communicated this location
                    if other_ant not in communicated_location_entry[1]:
                        # Append the other ant to the list of communicated ants for this location
                        communicated_location_entry[1].append(other_ant)

                        # Update the other ant's communicated targets
                        if (broadcast_x, broadcast_y, location_type) in other_ant.communicated_targets:
                            other_ant.communicated_targets[(broadcast_x, broadcast_y, location_type)] += 1  # Increment count if already communicated
                        else:
                            other_ant.communicated_targets[(broadcast_x, broadcast_y, location_type)] = 1  # Add new target with count 1

    
    def move(self, sugar_patches, sugarscape):
        current_time = pygame.time.get_ticks()

        # Detect sugar and set target if available and needed
        sugar_detected = self.detect_sugar(sugar_patches)
        
        # If no sugar detected and the ant needs to eat, check for communicated targets
        if not sugar_detected and not self.target and self.needs_to_eat():
            # Check if it's time to select a new target
            if current_time >= self.next_target_selection_time:
                if self.communicated_targets:
                    self.select_new_target(sugarscape)
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

                # Generate a new target selection interval based on a normal distribution
                self.target_selection_interval = max(500, random.gauss(self.mean_interval, self.std_deviation))
                self.next_target_selection_time += self.target_selection_interval

        # Move towards the target if one is selected
        if self.target:
            dx = self.target[0] - self.x
            dy = self.target[1] - self.y
            distance = math.sqrt(dx**2 + dy**2)

            if distance < ANT_SPEED:
                self.x, self.y = self.target
                # Check if the target was false and add it to confirmed_false_locations
                if self.following_false_location:
                    self.confirmed_false_locations.append(self.target)
                elif self.following_true_location:
                    self.confirmed_true_locations.append(self.target)
                
                # Remove the target from communicated_targets
                target_key = (self.target[0], self.target[1], "false" if self.following_false_location else "true")
                if target_key in self.communicated_targets:
                    del self.communicated_targets[target_key]

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

        # Broadcast sugar or false location
        self.broadcast_sugar_location(false_location=self in self.sugarscape.false_broadcasters)

    def needs_to_eat(self):
        return self.health < self.initial_health

    def eat_sugar(self):
        if self.needs_to_eat():
            self.health = min(self.health + HEALTH_INCREASE_AMOUNT, self.max_health)

    def is_alive(self):
        return self.health > 0
