import random
import math
import pygame
from constants import *
import collections  # Import collections module for OrderedDict
import numpy as np 

class Ant:
    def __init__(self, x, y, agent, ant_id, is_false_broadcaster=False):
        self.id = ant_id  # Unique identifier for the ant
        self.is_false_broadcaster = is_false_broadcaster
        self.current_time = 0
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
        # Key: (x, y), Value: {'accepted': count, 'rejected': count, 'confirmed': count, 'time_received': sim_time}

        self.already_communicated = {}  # Key: other_ant, Value: {location: characteristic}
        self.current_broadcast_characteristic = None  # Track current broadcast characteristic

        self.lifespan = 0

        # Set the mean and standard deviation for the target selection interval
        self.mean_interval = 500  # Mean interval of 480 frames (~8000 ms)
        self.std_deviation = 100  # Standard deviation of 120 frames (~2000 ms)

        # Use a normal distribution for the first target selection interval
        self.target_selection_interval = max(
                    300,  # Minimum interval of 30 frames (~500 ms)
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

        self.cumulative_reward = 0
        self.action_in_progress = False

        self.arrived_at_target = False  # Flag to indicate arrival at target (necessary for the delayed reward)
        self.frames_since_arrival = 0   # Counter for frames since arrival
        self.max_arrival_frames = 50    # Number of frames to wait after arrival

        self.total_episode_reward = 0  # Track total reward for the episode

        self.health_at_action_start = None  # Initialize to None

        self.current_action_type = None

        self.selected_action_characteristics = []  # Used for evaluation
        self.action_start_time = 0

        self.start_x = x
        self.start_y = y

        self.last_location = None
        
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

    def select_new_target(self, sugarscape, sim_time):
        self.has_reached_target = False
        self.health_at_action_start = self.health  # Record health at action start
        self.action_start_time = sim_time  # Record action start time

        state = self.get_state()
        # N = 10  # Number of communicated targets to consider
        target_items = list(self.communicated_targets.items())
        random.shuffle(target_items)
        # target_items = target_items[:N]
        possible_actions = []
        for location, counts in target_items:
            if location in self.confirmed_false_locations:
                continue  # Skip this location
            action_features = []
            dx = location[0] - self.x
            dy = location[1] - self.y
            distance = math.hypot(dx, dy)
            max_distance = math.hypot(GAME_WIDTH, HEIGHT)
            distance_normalized = distance / max_distance
            max_count = 10
            # Calculate time difference and apply exponential decay
            time_received = counts.get('time_received', sim_time)
            time_difference = sim_time - time_received
            decay_rate = 0.001  # Adjust as needed
            time_normalized = math.exp(-decay_rate * time_difference)

            confirmed_normalized = counts.get('confirmed', 0) / max_count
            accepted_normalized = counts.get('accepted', 0) / max_count
            rejected_normalized = counts.get('rejected', 0) / max_count
            action_features.extend([
                distance_normalized,
                confirmed_normalized,
                accepted_normalized,
                rejected_normalized,
                time_normalized,
            ])

            # **Determine the predominant characteristic**
            characteristic_counts = {
                'confirmed': counts.get('confirmed', 0),
                'accepted': counts.get('accepted', 0),
                'rejected': counts.get('rejected', 0),
            }
            predominant_characteristic = max(characteristic_counts, key=characteristic_counts.get)
            predominant_count = characteristic_counts[predominant_characteristic]

            is_false_location = location in self.sugarscape.historical_false_locations

            possible_actions.append({
                'type': 'target',
                'location': location,
                'features': np.array(action_features, dtype=np.float32),
                'characteristics': {
                    'distance': distance,
                    'counts': characteristic_counts.copy(),
                    'predominant_characteristic': predominant_characteristic,
                    'predominant_count': predominant_count,
                    'is_false_location': is_false_location,  # Add this line
                }   
            })
        # Conditionally add 'explore' only if no targets are available
        # if not possible_actions:
        explore_action = {
            'type': 'explore',
            'features': np.zeros(5, dtype=np.float32),
            'characteristics': {
                'type': 'explore',
                'is_false_location': None, 
            }
        }
        possible_actions.append(explore_action)

        action_index, log_prob = self.agent.select_action(self.id, state, possible_actions)
        self.prev_state = state
        self.prev_action = action_index
        self.prev_log_prob = log_prob
        self.cumulative_reward = 0
        self.action_in_progress = True
        selected_action = possible_actions[action_index]

        self.selected_action_characteristics.append(selected_action['characteristics'])

        if selected_action['type'] == 'target':
            self.target = selected_action['location']
            self.is_exploring_target = False
            self.broadcast_sugar_location('accepted')

            if selected_action['location'] in [(patch['x'], patch['y']) for patch in sugarscape.sugar_patches]:
                sugarscape.true_positives += 1
            elif selected_action['location'] in sugarscape.historical_false_locations:
                sugarscape.false_positives +=1 

            sugarscape.exploit_count +=1

        elif selected_action['type'] == 'explore':
            self.explore()
            # print(f"Ant {self.id} is exploring as per selected action")
            sugarscape.explore_count += 1
        
        self.current_action_type = selected_action['type']
        self.start_x = self.x
        self.start_y = self.y
        # print(f"ant {self.id} selected new action (type: {self.current_action_type})")

        self.next_target_selection_time = sim_time + self.target_selection_interval


    def explore(self):
        # Exploration logic: move randomly within the environment
        # self.target = (random.randint(0, GAME_WIDTH), random.randint(0, HEIGHT))
        self.target = None  # Ensure no target is set

        self.is_exploring_target = True  # Mark this target as an exploration target

    def end_current_action(self, sim_time, interrupted=False):
        action_duration = sim_time - self.action_start_time
        self.action_duration = action_duration  # Store for reward calculation
        # Calculate and store the reward
        self.cumulative_reward = self.calculate_reward()
        # if self.current_action_type == 'explore':
        # print(f"Reward for ant {self.id} is {self.cumulative_reward} (type: {self.current_action_type})")
        # print(f"Reward for ant {self.id} is {self.cumulative_reward} (Interrupted: {interrupted})")
        self.agent.store_reward(self.id,self.cumulative_reward)
        # Also accumulate to total_episode_reward
        self.total_episode_reward += self.cumulative_reward
        self.action_in_progress = False
        self.health_at_action_start = None  # Reset health at action start
        self.cumulative_reward = 0
        self.arrived_at_target = False  # Reset arrival flags
        self.frames_since_arrival = 0



        # if not interrupted:
        #     # Only update state if the action wasn't interrupted
        #     if not self.is_alive():
        #         self.prev_state = None
        #     else:
        #         self.prev_state = self.get_state()

        # Always update the state based on the current environment
        if not self.is_alive():
            self.prev_state = None
        else:
            self.prev_state = self.get_state()



    def broadcast_sugar_location(self, characteristic, false_location=False):
        # if characteristic=='confirmed':
        #     print(self.id, " is confirming location ", self.target_patch_center )
        
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
                            other_ant.communicated_targets[location] = {characteristic: 1, 'time_received': self.current_time}
                            # Ensure communicated_targets remains within size limit
                            # if len(other_ant.communicated_targets) > 10:
                            #     # Remove the oldest item
                            #     other_ant.communicated_targets.popitem(last=False)
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
            self.end_current_action(sim_time, interrupted=True)
            self.next_target_selection_time = self.current_time + self.target_selection_interval

            # Check if the current action should be ended (for 'explore' actions)
        if self.action_in_progress and self.current_time >= self.next_target_selection_time and self.current_action_type == 'explore' and not self.arrived_at_target:
            # End the current action
            self.end_current_action(sim_time)
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
        if not sugar_detected and not self.target and self.needs_to_eat() and not self.action_in_progress:
            if self.current_time >= self.next_target_selection_time:
                # if self.communicated_targets:
                self.select_new_target(sugarscape, sim_time)
                # else:
                    # No viable targets; explore
                    # self.explore()
                    # sugarscape.explore_count += 1
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
                        # print("Ant ", self.id, "arrived at a True location")


                        if not self.is_exploring_target and not self.has_reached_target:
                            self.just_reached_true_target = True

                        if self.needs_to_eat():
                            sugar['count'] -= 1
                            if sugar['count'] <= 0:
                                # Optionally remove or mark the sugar patch as depleted
                                pass
                            self.eat_sugar()
                            self.just_ate_sugar = True
                        break

                if not found_sugar:
                    # print("Ant ", self.id, "arrived at a false location")
                    self.confirmed_false_locations.add(self.target)
                    if not self.is_exploring_target and not self.has_reached_target:
                        self.just_reached_false_target = True
                    self.just_visited_false_location = True

                # Set has_reached_target to prevent repeated rewards
                self.has_reached_target = True
                self.last_location = self.target

                # **Modified Logic:**
                if found_sugar:
                    if self.health >= self.initial_health or sugar['count'] <= 0:
                        # Ant's health is replenished or sugar is depleted
                        self.last_location = self.target
                        self.target = None
                        self.is_exploring_target = None
                        self.has_reached_target = False  # Reset for the next action
                    else:
                        # Ant needs to keep consuming sugar, so stay at the location
                        self.target = (self.x, self.y)
                        # Continue to consume sugar in subsequent moves
                else:
                    # No sugar found at the location, so move on
                    self.last_location = self.target
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


        if self.arrived_at_target:     # used for rewarding after reaching a target
            # Increment frames since arrival
            self.frames_since_arrival += 1

            # Continue accumulating rewards
            if self.frames_since_arrival < self.max_arrival_frames:
                pass  # Keep accumulating rewards for 15 frames after arrival

            # Check if waiting period is over (i.e., 15 frames have passed)
            if self.frames_since_arrival >= self.max_arrival_frames:
                self.arrived_at_target = False  # Reset flag

                # End the action after the reward accumulation window is over
                if self.action_in_progress:
                    self.end_current_action(sim_time)

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
          
        # Check if the ant is dead
        # done = not self.is_alive()
        # if done:
        #     if self.action_in_progress:
        #         self.end_current_action()
        #     else:
        #         # Assign a default reward for the last action
        #         self.agent.store_reward(self.id, 0)

        #         self.next_target_selection_time = current_time + self.target_selection_interval

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
        health_normalized = self.health / self.max_health
        state_features.append(health_normalized)
        num_nearby_ants = self.count_nearby_ants()
        max_possible_ants = NUM_ANTS
        nearby_ants_normalized = num_nearby_ants / max_possible_ants
        state_features.append(nearby_ants_normalized)
        x_normalized = self.x / GAME_WIDTH
        y_normalized = self.y / HEIGHT
        state_features.extend([x_normalized, y_normalized])
        state = np.array(state_features, dtype=np.float32)
        return state

    def calculate_reward(self):
        # Ensure health_at_action_start is set
        if self.health_at_action_start is not None:
            health_change = self.health - self.health_at_action_start
        else:
            health_change = 0  # No health change if health_at_action_start is None

        # Base reward can be adjusted as needed
        base_reward = 0

        # Time penalty based on action duration
        if hasattr(self, 'action_duration'):
            time_penalty = -self.action_duration * 0.02  # Adjust as needed
        else:
            time_penalty = 0

        # Total reward before distance adjustment
        total_reward = base_reward + health_change + time_penalty

        # Calculate distance traveled
        # dx = self.x - self.start_x
        # dy = self.y - self.start_y
        # distance_traveled = math.hypot(dx, dy)

        # # Normalize the distance
        # max_distance = math.hypot(GAME_WIDTH, HEIGHT)
        # distance_normalized = distance_traveled / max_distance

        # # Adjust reward based on sign using normalized distance
        # if total_reward > 0:
        #     # For positive rewards, decrease reward with distance
        #     adjusted_reward = total_reward * (1 - distance_normalized)
        # elif total_reward < 0:
        #     # For negative rewards, increase penalty with distance
        #     adjusted_reward = total_reward * (1 + distance_normalized)
        # else:
        #     adjusted_reward = 0  # No adjustment needed for zero reward

        return total_reward
