import random
import math
import pygame
from constants import *
import collections  # Import collections module for OrderedDict
import numpy as np 

class Ant:
    def __init__(self, x, y, agent):
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
        self.mean_interval = 480  # Mean interval of 480 frames (~8000 ms)
        self.std_deviation = 120  # Standard deviation of 120 frames (~2000 ms)

        # Use a normal distribution for the first target selection interval
        self.target_selection_interval = max(
                    30,  # Minimum interval of 30 frames (~500 ms)
                    int(random.gauss(self.mean_interval, self.std_deviation))
                ) 
        self.next_target_selection_time = self.target_selection_interval

        self.confirmed_false_locations = set()  # List to store confirmed false locations
        self.confirmed_true_locations = set()  # List to store confirmed true locations

        self.sugarscape = None  # Reference to the Sugarscape instance
        self.false_broadcast_location = None  # Store the current false location being broadcast
        self.target_patch_center = None  # Store the center of the sugar patch for broadcasting

        self.is_exploring_target = False  # Initially not exploring
        self.just_ate_sugar = False
        self.just_visited_false_location = False
        self.just_reached_true_target = False  # Initialize the new flag
        self.just_reached_false_target = False  # Initialize the new flag

        # Track false locations created by this ant if it is a false broadcaster
        self.own_false_locations = set()

        self.agent = agent

        self.has_reached_target = False  # Add this line

        self.previous_health = self.health  # For tracking health changes

        
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

        self.has_reached_target = False

        # Construct the state
        state = self.get_state()
        
        # Use the RL agent to select an action
        action = self.agent.select_action(state)
        
        # Store the state and action for later use
        self.prev_state = state
        self.prev_action = action
        
        # Determine the action
        N = 5  # Number of communicated targets to consider
        if action < N and action < len(self.communicated_targets):
            # Select the target corresponding to the action
            target_list = list(self.communicated_targets.keys())[:N]
            self.target = target_list[action]
            self.is_exploring_target = False
            self.broadcast_sugar_location('accepted')
        else:
            # Explore
            self.explore()
            sugarscape.explore_count += 1

    def explore(self):
        # Exploration logic: move randomly within the environment
        self.target = (random.randint(0, GAME_WIDTH), random.randint(0, HEIGHT))
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
                            # Ensure communicated_targets remains within size limit
                            if len(other_ant.communicated_targets) > 10:
                                # Remove the oldest item
                                other_ant.communicated_targets.popitem(last=False)
                        # Update 'already_communicated'
                        self.already_communicated[other_ant][location] = characteristic
                        

    
    def move(self, sugar_patches, sugarscape, sim_time):
        current_time = sim_time

        sugar_detected = self.detect_sugar(sugar_patches)

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
            else:
                self.current_broadcast_characteristic = 'accepted'

            # If the characteristic or location has changed, reset communication tracking
            if (self.current_broadcast_characteristic != previous_characteristic or
                    location != previous_location):
                for other_ant in list(self.already_communicated.keys()):
                    if location in self.already_communicated[other_ant]:
                        # Remove the entry for this location
                        del self.already_communicated[other_ant][location]
                        # If the inner dictionary is now empty, remove the entry for this other_ant
                        if not self.already_communicated[other_ant]:
                            del self.already_communicated[other_ant]


            self.broadcast_sugar_location(self.current_broadcast_characteristic)
        else:
            # If the ant has no target or last location, reset the current broadcast characteristic
            self.current_broadcast_characteristic = None

        # False broadcasters continuously broadcast their false location
        if self in self.sugarscape.false_broadcasters:
            if self.false_broadcast_location is None:
                # Generate a new false location
                padding = 100
                self.false_broadcast_location = (
                    random.randint(padding, GAME_WIDTH - padding),
                    random.randint(padding, HEIGHT - padding),
                )
                self.sugarscape.broadcast_times[self] = current_time +  600  # Schedule next change in 6 seconds
            else:
                if current_time >= self.sugarscape.broadcast_times[self]:
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

                # Check if the target is within any sugar patch (regardless of sugar presence)
                is_sugar_location = any(
                    math.hypot(sugar[0] - self.x, sugar[1] - self.y) < SUGAR_RADIUS
                    for sugar in self.sugarscape.sugar_patches
                )

                # Check if there is sugar present at the location
                found_sugar = any(
                    sugar[2] and math.hypot(sugar[0] - self.x, sugar[1] - self.y) < SUGAR_RADIUS
                    for sugar in self.sugarscape.sugar_patches
                )

                if is_sugar_location:
                    self.confirmed_true_locations.add(self.target)
                    if not self.is_exploring_target and not self.has_reached_target:
                        self.just_reached_true_target = True  # Set reward flag
                    if found_sugar:
                        # Handle sugar consumption
                        if self.needs_to_eat():
                            for sugar in self.sugarscape.sugar_patches:
                                if sugar[2] and math.hypot(sugar[0] - self.x, sugar[1] - self.y) < SUGAR_RADIUS:
                                    sugar[2] = False  # Mark sugar as consumed
                                    self.sugarscape.consumed_sugar_count += 1
                                    self.eat_sugar()
                                    self.just_ate_sugar = True  # Set reward flag
                                    break  # Consume only one sugar
                else:
                    self.confirmed_false_locations.add(self.target)
                    if not self.is_exploring_target and not self.has_reached_target:
                        self.just_reached_false_target = True  # Set reward flag
                    self.just_visited_false_location = True  # Set reward flag
                
                # Set has_reached_target to True to prevent repeated rewards
                self.has_reached_target = True

                # After reaching the target, store it as last_location
                self.last_location = self.target
                self.target = None  # Clear the target after reaching it
                self.is_exploring_target = None  # Reset the flag

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
                other_ants_to_remove = []
                for other_ant in list(self.already_communicated.keys()):
                    # If previous_target is in the inner dictionary for this other_ant
                    if previous_target in self.already_communicated[other_ant]:
                        del self.already_communicated[other_ant][previous_target]
                        # If the inner dictionary is now empty, mark this other_ant for removal
                        if not self.already_communicated[other_ant]:
                            other_ants_to_remove.append(other_ant)
                # Remove other_ants with empty dictionaries
                for other_ant in other_ants_to_remove:
                    del self.already_communicated[other_ant]
            # Do not reset current_broadcast_characteristic here, since we continue broadcasting after reaching the target
        
        # Calculate reward
        reward = self.calculate_reward()

        # Get next state
        next_state = self.get_state()

        # Check if the episode is done
        done = not self.is_alive()

        # Store experience and update policy
        if hasattr(self, 'prev_state') and hasattr(self, 'prev_action'):
            self.agent.store_experience(self.prev_state, self.prev_action, reward, next_state, done)
            self.agent.update_policy()

        # Update previous state and action
        if not done:
            self.prev_state = next_state
            # The action will be set during the next select_new_target call




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
    

    #RL stuff

    def get_state(self):
        state_features = []
        
        # Health level (normalized)
        health_normalized = self.health / self.max_health
        state_features.append(health_normalized)
        
        # Number of nearby ants (normalized)
        num_nearby_ants = self.count_nearby_ants()
        max_possible_ants = NUM_ANTS  # Assuming this is defined in your constants
        nearby_ants_normalized = num_nearby_ants / max_possible_ants
        state_features.append(nearby_ants_normalized)
        
        # Ant's current position (normalized)
        x_normalized = self.x / GAME_WIDTH
        y_normalized = self.y / HEIGHT
        state_features.extend([x_normalized, y_normalized])
        
        # Communicated targets
        N = 5  # Number of communicated targets to include
        max_distance = math.hypot(GAME_WIDTH, HEIGHT)  # Maximum possible distance in the game
        max_count = 10  # Maximum count for characteristics; adjust as needed
        
        # Get the top N communicated targets
        communicated_targets_list = list(self.communicated_targets.items())[:N]
        for location, counts in communicated_targets_list:
            dx = location[0] - self.x
            dy = location[1] - self.y
            distance = math.hypot(dx, dy)
            
            # Normalize distance
            distance_normalized = distance / max_distance
            
            # Normalize counts
            confirmed_normalized = counts.get('confirmed', 0) / max_count
            accepted_normalized = counts.get('accepted', 0) / max_count
            rejected_normalized = counts.get('rejected', 0) / max_count
            
            # Add to state features
            state_features.extend([
                distance_normalized,
                confirmed_normalized,
                accepted_normalized,
                rejected_normalized,
            ])
        
        # Pad the state if there are fewer than N targets
        num_features_per_target = 4  # Now 4 features per target
        expected_features = N * num_features_per_target
        actual_features = len(communicated_targets_list) * num_features_per_target
        if actual_features < expected_features:
            state_features.extend([0] * (expected_features - actual_features))
        
        # Convert to NumPy array
        state = np.array(state_features, dtype=np.float32)
        
        return state

    
    def calculate_reward(self):
        # Reward for survival
        reward = 1  # Positive reward per time step for being alive

        # Reward or penalty based on health change
        health_change = self.health - self.previous_health
        reward += health_change  # Positive if health increased, negative if decreased

        # Update previous health for the next time step
        self.previous_health = self.health

        # Optional: Remove or adjust the time penalty
        # reward -= 0.1  # If you want to encourage efficiency

        return reward


