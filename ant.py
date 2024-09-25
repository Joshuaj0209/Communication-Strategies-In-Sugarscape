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
        self.communicated_targets = {}  # Key: (x, y), Value: {'accepted': count, 'rejected': count, 'confirmed': count}
        self.already_communicated = {}  # Key: (location, characteristic), Value: set of ants
        self.current_broadcast_characteristic = None  # Track current broadcast characteristic

        self.lifespan = 0

        # Set the mean and standard deviation for the target selection interval
        self.mean_interval = 8000  # Mean interval of 8000ms
        self.std_deviation = 2000  # Standard deviation of 2000ms

        # Use a normal distribution for the first target selection interval
        self.target_selection_interval = max(500, random.gauss(self.mean_interval, self.std_deviation))
        self.next_target_selection_time = pygame.time.get_ticks() + self.target_selection_interval

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
        max_distance = self.health / HEALTH_DECREASE_RATE * ANT_SPEED

        viable_targets = []
        total_weight = 0

        for location, counts in self.communicated_targets.items():
            if location in self.confirmed_false_locations or location in self.confirmed_true_locations:
                continue

            dx = location[0] - self.x
            dy = location[1] - self.y
            distance = math.sqrt(dx**2 + dy**2)

            if distance <= max_distance:
                confirmed = counts.get('confirmed', 0)
                accepted = counts.get('accepted', 0)
                rejected = counts.get('rejected', 0)

                score = (confirmed + 0.5 * accepted) / (rejected + 1) / (distance**2 + 1)
                viable_targets.append((location, score))
                total_weight += score

        if viable_targets:
            rand_value = random.uniform(0, total_weight)
            cumulative_weight = 0
            for location, weight in viable_targets:
                cumulative_weight += weight
                if rand_value <= cumulative_weight:
                    self.target = location
                    sugarscape.exploit_count += 1
                    self.broadcast_sugar_location('accepted')
                    return

        # If there are no viable targets, explore
        self.explore()
        sugarscape.explore_count += 1

    def explore(self):
        # Exploration logic: move randomly within the environment
        self.target = (random.randint(0, GAME_WIDTH), random.randint(0, HEIGHT))

    def broadcast_sugar_location(self, characteristic, false_location=False):
        if false_location:
            if self in self.sugarscape.false_broadcasters:
                if not self.false_broadcast_location:
                    padding = 100
                    self.false_broadcast_location = (
                        random.randint(padding, GAME_WIDTH - padding),
                        random.randint(padding, HEIGHT - padding),
                    )
                broadcast_x, broadcast_y = self.false_broadcast_location
            else:
                return  # Non-false broadcasters should not broadcast false locations
        else:
            if self.target_patch_center:
                broadcast_x, broadcast_y = self.target_patch_center
            elif self.target:
                broadcast_x, broadcast_y = self.target
            else:
                return  # No valid location to broadcast

        location = (broadcast_x, broadcast_y)
        key = (location, characteristic)

        # Initialize the set if not already done
        if key not in self.already_communicated:
            self.already_communicated[key] = set()

        # Broadcast to other ants within the communication radius
        for other_ant in self.sugarscape.ants:
            if other_ant != self:
                dx = other_ant.x - self.x
                dy = other_ant.y - self.y
                dist = math.sqrt(dx ** 2 + dy ** 2)

                if dist <= COMMUNICATION_RADIUS:
                    # Check if we have already communicated this location and characteristic to this ant
                    if other_ant not in self.already_communicated[key]:
                        # Update the other ant's communicated targets
                        if location in other_ant.communicated_targets:
                            if characteristic in other_ant.communicated_targets[location]:
                                other_ant.communicated_targets[location][characteristic] += 1
                            else:
                                other_ant.communicated_targets[location][characteristic] = 1
                        else:
                            other_ant.communicated_targets[location] = {characteristic: 1}
                        # Mark that we have communicated this to the other ant
                        self.already_communicated[key].add(other_ant)
        

    
    def move(self, sugar_patches, sugarscape):
        current_time = pygame.time.get_ticks()

        sugar_detected = self.detect_sugar(sugar_patches)

        # Store the previous broadcast characteristic and location
        previous_characteristic = self.current_broadcast_characteristic
        previous_location = self.target if self.target else getattr(self, 'last_location', None)

        # Ant continuously broadcasts its current target location or last known location
        if self.target or getattr(self, 'last_location', None):
            if self.target:
                location = self.target
            else:
                location = self.last_location

            if location in self.confirmed_true_locations:
                self.current_broadcast_characteristic = 'confirmed'
            elif location in self.confirmed_false_locations:
                self.current_broadcast_characteristic = 'rejected'
            else:
                self.current_broadcast_characteristic = 'accepted'

            # If the characteristic or location has changed, reset communication tracking
            if (self.current_broadcast_characteristic != previous_characteristic or
                    location != previous_location):
                key = (location, previous_characteristic)
                if key in self.already_communicated:
                    del self.already_communicated[key]

            self.broadcast_sugar_location(self.current_broadcast_characteristic)
        else:
            # If the ant has no target or last location, reset the current broadcast characteristic
            self.current_broadcast_characteristic = None

        # False broadcasters continuously broadcast their false location
        if self in self.sugarscape.false_broadcasters:
            if current_time >= self.sugarscape.broadcast_times[self]:
                # Reset communication for the old false location
                if self.false_broadcast_location:
                    key = (self.false_broadcast_location, 'confirmed')
                    if key in self.already_communicated:
                        del self.already_communicated[key]
                self.false_broadcast_location = None  # Reset for a new false location
                self.sugarscape.broadcast_times[self] += 10000
            self.broadcast_sugar_location('confirmed', false_location=True)

        # Before moving, store the previous target
        previous_target = self.target

        # Movement logic that might change self.target
        if not sugar_detected and not self.target and self.needs_to_eat():
            if current_time >= self.next_target_selection_time:
                if self.communicated_targets:
                    self.select_new_target(sugarscape)
                else:
                    # No viable targets; explore
                    self.explore()
                    sugarscape.explore_count += 1
                self.target_selection_interval = max(500, random.gauss(self.mean_interval, self.std_deviation))
                self.next_target_selection_time += self.target_selection_interval

        if self.target:
            dx = self.target[0] - self.x
            dy = self.target[1] - self.y
            distance = math.sqrt(dx**2 + dy**2)

            if distance < ANT_SPEED:
                self.x, self.y = self.target
                found_sugar = any(
                    sugar[2] and math.hypot(sugar[0] - self.x, sugar[1] - self.y) < SUGAR_RADIUS
                    for sugar in self.sugarscape.sugar_patches
                )

                if found_sugar:
                    self.confirmed_true_locations.append(self.target)
                    # The broadcast has already been handled above
                    # Handle sugar consumption
                    if self.needs_to_eat():
                        for sugar in self.sugarscape.sugar_patches:
                            if sugar[2] and math.hypot(sugar[0] - self.x, sugar[1] - self.y) < SUGAR_RADIUS:
                                sugar[2] = False  # Mark sugar as consumed
                                self.sugarscape.consumed_sugar_count += 1
                                self.eat_sugar()
                                break  # Consume only one sugar
                else:
                    self.confirmed_false_locations.append(self.target)
                    # The broadcast has already been handled above

                # After reaching the target, store it as last_location
                self.last_location = self.target
                self.target = None  # Clear the target after reaching it
            else:
                self.direction = math.atan2(dy, dx)
        else:
            self.direction += random.uniform(-self.turn_angle, self.turn_angle)

        self.x += ANT_SPEED * math.cos(self.direction)
        self.y += ANT_SPEED * math.sin(self.direction)
        self.x = max(0, min(self.x, GAME_WIDTH))
        self.y = max(0, min(self.y, HEIGHT))

        self.health -= HEALTH_DECREASE_RATE
        self.lifespan += 1

        # If the target has changed, reset communication tracking
        if self.target != previous_target:
            if previous_target:
                keys_to_remove = [key for key in self.already_communicated if key[0] == previous_target]
                for key in keys_to_remove:
                    del self.already_communicated[key]
            # Do not reset current_broadcast_characteristic here, since we continue broadcasting after reaching the target



    def needs_to_eat(self):
        return self.health < self.initial_health

    def eat_sugar(self):
        if self.needs_to_eat():
            self.health = min(self.health + HEALTH_INCREASE_AMOUNT, self.max_health)

    def is_alive(self):
        return self.health > 0
