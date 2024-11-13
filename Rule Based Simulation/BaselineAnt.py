# BaselineAnt.py

import random
import math
import collections
import numpy as np
from constants import *

class BaselineAnt:
    def __init__(self, x, y, ant_id, is_false_broadcaster=False):
        self.id = ant_id  # Unique identifier for the ant
        self.current_time = 0
        self.is_false_broadcaster = is_false_broadcaster
        self.x = x
        self.y = y
        self.direction = random.uniform(0, 2 * math.pi)
        self.turn_angle = math.pi / 8
        self.health = INITIAL_HEALTH
        self.initial_health = INITIAL_HEALTH
        self.max_health = MAX_HEALTH
        self.target = None
        # Use OrderedDict for communicated_targets to maintain order
        self.communicated_targets = collections.OrderedDict()
        # Key: (x, y), Value: {'accepted': count, 'rejected': count, 'confirmed': count}

        self.already_communicated = {}  # Key: other_ant, Value: {location: characteristic}
        self.current_broadcast_characteristic = None  # Track current broadcast characteristic

        self.lifespan = 0

        # Set the mean and standard deviation for the target selection interval
        self.mean_interval = 500  # Mean interval of 500 frames
        self.std_deviation = 100  # Standard deviation of 100 frames

        # Use a normal distribution for the first target selection interval
        self.target_selection_interval = max(
            300,  # Minimum interval of 300 frames
            int(random.gauss(self.mean_interval, self.std_deviation))
        )
        self.next_target_selection_time = self.target_selection_interval

        self.confirmed_false_locations = set()  # Set to store confirmed false locations
        self.confirmed_true_locations = set()  # Set to store confirmed true locations

        self.sugarscape = None  # Reference to the Sugarscape instance
        self.false_broadcast_location = None  # Store the current false location being broadcast
        self.target_patch_center = None  # Store the center of the sugar patch for broadcasting

        self.is_exploring_target = False  # Initially not exploring
        self.just_ate_sugar = False

        # Track false locations created by this ant if it is a false broadcaster
        self.own_false_locations = set()

        self.has_reached_target = False

        self.arrived_at_target = False  # Flag to indicate arrival at target
        self.frames_since_arrival = 0   # Counter for frames since arrival
        self.max_arrival_frames = 50    # Number of frames to wait after arrival

        self.health_at_action_start = None  # Initialize to None

        self.current_action_type = None

        self.selected_action_characteristics = []  # Used for evaluation

        self.action_in_progress = False

        self.last_location = None  # Initialize last_location


    def detect_sugar(self, sugar_patches):
        closest_sugar = None
        closest_distance = float('inf')
        target_changed = False

        for sugar in sugar_patches:
            if sugar['count'] > 0:  # Only consider patches with sugar
                dx = sugar['x'] - self.x
                dy = sugar['y'] - self.y
                distance = math.hypot(dx, dy)

                if distance < DETECTION_RADIUS and distance < closest_distance:
                    closest_sugar = sugar
                    closest_distance = distance

        if closest_sugar and self.needs_to_eat():
            if self.target != (closest_sugar['x'], closest_sugar['y']):
                # Target is changing
                target_changed = True
            self.target = (closest_sugar['x'], closest_sugar['y'])
            self.target_patch_center = (closest_sugar['x'], closest_sugar['y'])
            return True, target_changed

        return False, False

    def select_new_target(self, sugarscape):
            self.has_reached_target = False
            self.health_at_action_start = self.health  # Record health at action start
            # health_threshold = 0.9  # 90% of max health

            max_distance = math.hypot(GAME_WIDTH, HEIGHT)
            viable_targets = []
            total_weight = 0
            action_characteristics_list = []

            for location, counts in self.communicated_targets.items():
                # Skip locations that are this ant's own false locations
                if location in self.own_false_locations:
                    continue

                # Skip confirmed locations
                if location in self.confirmed_false_locations or location in self.confirmed_true_locations:
                    continue

                dx = location[0] - self.x
                dy = location[1] - self.y
                distance = math.hypot(dx, dy)

                if distance <= max_distance:
                    confirmed = counts.get('confirmed', 0)
                    accepted = counts.get('accepted', 0)
                    rejected = counts.get('rejected', 0)
                    # print("Rejected:", rejected)

                    # Calculate score based on the rule-based function
                    score = (confirmed + 0.5* accepted) / (rejected + 1) / (distance**2 + 1)  ## 
                    viable_targets.append((location, score))

                    # Collect action characteristics for evaluation
                    characteristic_counts = {
                        'confirmed': confirmed,
                        'accepted': accepted,
                        'rejected': rejected,
                    }
                    predominant_characteristic = max(characteristic_counts, key=characteristic_counts.get)
                    predominant_count = characteristic_counts[predominant_characteristic]
                    is_false_location = location in sugarscape.historical_false_locations

                    action_characteristics_list.append({
                        'type': 'target',
                        'location': location,
                        'distance': distance,
                        'counts': characteristic_counts.copy(),
                        'predominant_characteristic': predominant_characteristic,
                        'predominant_count': predominant_count,
                        'is_false_location': is_false_location,
                    })
                    total_weight += score
            
            if viable_targets:
                # Select a target based on weighted probabilities
                rand_value = random.uniform(0, total_weight)
                cumulative_weight = 0
                selected_idx = None
                for idx, (location, weight) in enumerate(viable_targets):
                    cumulative_weight += weight
                    if rand_value <= cumulative_weight:
                        self.target = location
                        sugarscape.exploit_count += 1
                        self.is_exploring_target = False  # Set to False as it's not an explore target
                        self.broadcast_sugar_location('accepted')

                        selected_idx = idx  # Save index to retrieve action characteristics

                        # Check if the accepted location is true or false
                        if location in [(patch['x'], patch['y']) for patch in sugarscape.sugar_patches]:
                            sugarscape.true_positives += 1
                        elif location in sugarscape.historical_false_locations:
                            sugarscape.false_positives += 1
                        break

                # Append the action characteristics of the selected target
                if selected_idx is not None:
                    selected_action_char = action_characteristics_list[selected_idx]
                    self.selected_action_characteristics.append(selected_action_char)
            else:
                # If no viable targets, explore
                self.explore()
                sugarscape.explore_count += 1
                self.current_action_type = 'explore'
                # For evaluation, record the explore action
                self.selected_action_characteristics.append({
                    'type': 'explore',
                    'is_false_location': None,
                })

            self.action_in_progress = True
        
            self.next_target_selection_time = self.current_time + self.target_selection_interval




    def explore(self):
        # Exploration logic: move randomly within the environment
        self.target = None  # Ensure no target is set
        self.is_exploring_target = True  # Mark this target as an exploration target

    def broadcast_sugar_location(self, characteristic, false_location=False):
        if false_location:
            if self.false_broadcast_location:
                broadcast_x, broadcast_y = self.false_broadcast_location
            else:
                return  # No false location to broadcast
        else:
            if self.target_patch_center:
                broadcast_x, broadcast_y = self.target_patch_center
            elif self.target:
                broadcast_x, broadcast_y = self.target
            elif getattr(self, 'last_location', None):
                broadcast_x, broadcast_y = self.last_location
            else:
                return  # No valid location to broadcast

        location = (broadcast_x, broadcast_y)

        # Broadcast to other ants within the communication radius
        for other_ant in self.sugarscape.ants:
            if other_ant != self:
                dx = other_ant.x - self.x
                dy = other_ant.y - self.y
                dist = math.hypot(dx, dy)

                if dist <= COMMUNICATION_RADIUS:
                    if location in other_ant.confirmed_false_locations:
                        continue  # Skip this location
                    # Initialize 'already_communicated' entry for other_ant if not present
                    if other_ant not in self.already_communicated:
                        self.already_communicated[other_ant] = {}
                    # Check if we've previously communicated this location to this ant
                    previous_characteristic = self.already_communicated[other_ant].get(location)
                    if previous_characteristic == characteristic:
                        # Already communicated this characteristic to this ant for this location
                        continue
                    else:
                        # Update other_ant's communicated_targets
                        # Decrement count for previous characteristic if any
                        if previous_characteristic:
                            if location in other_ant.communicated_targets:
                                if previous_characteristic in other_ant.communicated_targets[location]:
                                    other_ant.communicated_targets[location][previous_characteristic] -= 1
                                    if other_ant.communicated_targets[location][previous_characteristic] <= 0:
                                        del other_ant.communicated_targets[location][previous_characteristic]
                                    if not other_ant.communicated_targets[location]:
                                        # Remove the location from communicated_targets
                                        del other_ant.communicated_targets[location]
                        # Increment count for new characteristic
                        if location in other_ant.communicated_targets:
                            # Update counts
                            counts = other_ant.communicated_targets[location]
                            counts[characteristic] = counts.get(characteristic, 0) + 1
                            # Move the location to the end to reflect recent communication
                            other_ant.communicated_targets.move_to_end(location)
                        else:
                            # Add new location
                            other_ant.communicated_targets[location] = {characteristic: 1}
                        # Update 'already_communicated'
                        self.already_communicated[other_ant][location] = characteristic

    def move(self, sugar_patches, sugarscape, sim_time):
        self.current_time = sim_time

        # Store the previous target before detecting sugar
        previous_target = self.target

        # Detect sugar only if not in action or if the action is 'explore'
        if self.target is None:
            sugar_detected, target_changed = self.detect_sugar(sugar_patches)
        else:
            sugar_detected, target_changed = False, False

        if self.action_in_progress and target_changed and not self.has_reached_target and not self.arrived_at_target and self.current_action_type != 'explore':
            # The action has been interrupted due to detecting new sugar
            self.next_target_selection_time = self.current_time + self.target_selection_interval

        if self.action_in_progress and self.current_time >= self.next_target_selection_time and self.current_action_type == 'explore' and not self.arrived_at_target:
            self.action_in_progress = False
            # After ending the action, set the next target selection time
            self.next_target_selection_time = self.current_time + self.target_selection_interval

        # Store the previous broadcast characteristic and location
        previous_characteristic = self.current_broadcast_characteristic
        previous_location = self.target if self.target else getattr(self, 'last_location', None)

        # Ant continuously broadcasts its current target location or last known location
        if (self.target or getattr(self, 'last_location', None)) and not self.is_exploring_target:
            if self.target:
                location = self.target
            else:
                location = self.last_location

            if location in self.confirmed_true_locations:
                self.current_broadcast_characteristic = 'confirmed'
            elif location in self.confirmed_false_locations:
                self.current_broadcast_characteristic = 'rejected'
                # print("Rejecting")
            else:
                self.current_broadcast_characteristic = 'accepted'
            self.broadcast_sugar_location(self.current_broadcast_characteristic)
        else:
            # If the ant has no target or last location, reset the current broadcast characteristic
            self.current_broadcast_characteristic = None

        # False broadcasters continuously broadcast their false location
        if self in self.sugarscape.false_broadcasters:
            if self.false_broadcast_location is None:
                 # Generate a new false location that is at least MIN_FALSE_LOCATION_DISTANCE away from any sugar patch
                padding = 30
                max_attempts = 100  # Maximum number of attempts to find a valid location
                attempts = 0
                valid_location_found = False

                while not valid_location_found and attempts < max_attempts:
                    # Generate a random location within the game area with padding
                    candidate_location = (
                        random.randint(padding, GAME_WIDTH - padding),
                        random.randint(padding, HEIGHT - padding),
                    )
                    valid_location = True
                    # Check distance to all sugar patches
                    for sugar in self.sugarscape.sugar_patches:
                        dx = sugar['x'] - candidate_location[0]
                        dy = sugar['y'] - candidate_location[1]
                        distance = math.hypot(dx, dy)
                        if distance < 150:   # Minimum distance away from any sugar patch
                            valid_location = False
                            break  # No need to check other sugar patches

                    if valid_location:
                        valid_location_found = True
                        self.false_broadcast_location = candidate_location
                        self.sugarscape.broadcast_times[self] = self.current_time + 800  # NB: change back to 1000
                    else:
                        attempts += 1

                if not valid_location_found:
                    # Optional: Handle the case where a valid location wasn't found
                    print(f"Ant {self.id}: Could not find a valid false location after {max_attempts} attempts.")
                    # Decide whether to skip generating a false location or relax the distance requirement
                    # For now, we'll skip this cycle
                    pass
            else:
                if self.current_time >= self.sugarscape.broadcast_times[self]:
                    # Reset communication for the old false location
                    for other_ant in list(self.already_communicated.keys()):
                        if self.false_broadcast_location in self.already_communicated[other_ant]:
                            del self.already_communicated[other_ant][self.false_broadcast_location]
                            if not self.already_communicated[other_ant]:
                                del self.already_communicated[other_ant]
                    self.false_broadcast_location = None  # Reset to generate a new false location in the next frame
                else:
                    # Continue broadcasting the current false location
                    pass  # Do nothing
            if self.false_broadcast_location:
                self.broadcast_sugar_location('confirmed', false_location=True)

        # Movement logic that might change self.target
        if not sugar_detected and not self.target and self.needs_to_eat():
            if self.current_time >= self.next_target_selection_time:
                if self.communicated_targets:
                    self.select_new_target(sugarscape)
                else:
                    # No viable targets; explore
                    self.explore()
                    sugarscape.explore_count += 1
                self.action_in_progress = True
                # self.target_selection_interval = max(300, random.gauss(self.mean_interval, self.std_deviation))
                # self.next_target_selection_time = self.current_time + self.target_selection_interval

        if self.target:
            dx = self.target[0] - self.x
            dy = self.target[1] - self.y
            distance = math.sqrt(dx**2 + dy**2)

            if distance < ANT_SPEED:
                self.x, self.y = self.target
                found_sugar = False

                # Check if ant is within any sugar patch
                for sugar in self.sugarscape.sugar_patches:
                    dx = sugar['x'] - self.x
                    dy = sugar['y'] - self.y
                    distance_to_sugar = math.hypot(dx, dy)

                    if distance_to_sugar <= sugar['radius'] and sugar['count'] > 0:
                        found_sugar = True
                        self.confirmed_true_locations.add(self.target)

                        if not self.is_exploring_target and not self.has_reached_target:
                            pass  # Placeholder for any additional logic

                        if self.needs_to_eat():
                            sugar['count'] -= 1
                            if sugar['count'] <= 0:
                                # Optionally remove or mark the sugar patch as depleted
                                pass
                            self.eat_sugar()
                            self.just_ate_sugar = True
                        break

                if not found_sugar:
                    self.confirmed_false_locations.add(self.target)
                    # print("Added target ",self.target, "to confirmed false locations")
                    if not self.is_exploring_target and not self.has_reached_target:
                        pass  # Placeholder for any additional logic

                # **Modified Logic:**
                if found_sugar:
                    if self.health >= self.initial_health or sugar['count'] <= 0:
                        # Ant's health is replenished or sugar is depleted
                        self.last_location = self.target  # Save the last target location

                        self.target = None
                        self.is_exploring_target = None
                        self.has_reached_target = False  # Reset for the next action
                    else:
                        # Ant needs to keep consuming sugar, so stay at the location
                        self.target = (self.x, self.y)
                        # Continue to consume sugar in subsequent moves
                else:
                    # No sugar found at the location, so move on
                    self.last_location = self.target  # Save the last target location
                    self.target = None
                    self.is_exploring_target = None
                    self.has_reached_target = False  # Reset for the next action

                # Start the arrival timer
                if not self.arrived_at_target:
                    self.arrived_at_target = True
                    self.frames_since_arrival = 0

                self.next_target_selection_time = self.current_time + self.target_selection_interval

            else:
                self.direction = math.atan2(dy, dx)
        else:
            self.direction += random.uniform(-self.turn_angle, self.turn_angle)
            self.direction %= 2 * math.pi  # Ensure direction stays within 0 to 2π

        if self.arrived_at_target:
            # Increment frames since arrival
            self.frames_since_arrival += 1

            # Check if waiting period is over
            if self.frames_since_arrival >= self.max_arrival_frames:
                self.arrived_at_target = False  # Reset flag

                if self.action_in_progress:
                    # Schedule next target selection
                    self.next_target_selection_time = self.current_time + self.target_selection_interval

        self.x += ANT_SPEED * math.cos(self.direction)
        self.y += ANT_SPEED * math.sin(self.direction)
        self.x = max(0, min(self.x, GAME_WIDTH))
        self.y = max(0, min(self.y, HEIGHT))

        if self.is_false_broadcaster:
            self.health -= FALSE_BROADCASTER_HEALTH_DECREASE_RATE
        else:
            self.health -= HEALTH_DECREASE_RATE
        self.lifespan += 1


    def needs_to_eat(self):
        return self.health < self.initial_health

    def eat_sugar(self):
        if self.needs_to_eat():
            self.health = min(self.health + HEALTH_INCREASE_AMOUNT, self.max_health)

    def is_alive(self):
        return self.health > 0

    def count_nearby_ants(self):
        count = 0
        for other_ant in self.sugarscape.ants:
            if other_ant != self:
                dx = other_ant.x - self.x
                dy = other_ant.y - self.y
                distance = math.hypot(dx, dy)
                if distance <= DETECTION_RADIUS:
                    count += 1
        return count
