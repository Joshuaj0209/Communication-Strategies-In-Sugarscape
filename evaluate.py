# evaluate.py
import pygame
import sys
import time
from constants import *
from sugarscape import SugarScape
import matplotlib.pyplot as plt
from rl_agent import AntRLAgent
import os
import numpy as np
from sklearn.linear_model import LinearRegression
from collections import Counter  # Add this import

def moving_average(data, window_size):
    return np.convolve(data, np.ones(window_size)/window_size, mode='valid')

def main(render=True):
    if render:
        pygame.init()
        screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("SugarScape Simulation with Analytics")
        clock = pygame.time.Clock()
        font = pygame.font.Font(None, 24)

    # Initialize the RL agent
    state_size = 4  # Ant's own state features
    action_feature_size = 4  # Features per action (communicated target)
    input_size = state_size + action_feature_size
    shared_agent = AntRLAgent(input_size)

    # Load the trained model
    trained_model_path = "F_trained_improved_1.pth"  # Replace with your model filename
    shared_agent.load_model(trained_model_path)

    num_episodes = 50  # Define the number of evaluation episodes
    episode_length = 30000  # Define the length of each episode in time steps

    episode_rewards = []
    episode_lifespans = []  # For tracking average lifespans

    action_characteristics_list = []  # Add this line

    for episode in range(num_episodes):
        print(f"Starting Evaluation Episode {episode + 1}/{num_episodes}")

        # Start timing the episode
        episode_start_time = time.time()

        # Initialize the environment for each episode
        sugarscape = SugarScape(shared_agent)
        sim_time = 0  # Initialize simulation time

        # Track the total reward for all ants
        total_rewards = []

        running = True
        while running and sim_time < episode_length:
            if render:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False
                        pygame.quit()
                        sys.exit()

            sim_time += 1

            sugarscape.update(sim_time)

            if render:
                game_surface = pygame.Surface((GAME_WIDTH, HEIGHT))
                sugarscape.draw(game_surface)
                screen.blit(game_surface, (0, 0))

                analytics_surface = pygame.Surface((ANALYTICS_WIDTH, HEIGHT))
                analytics_surface.fill(WHITE)
                pygame.draw.line(analytics_surface, GRAY, (0, 0), (0, HEIGHT), 3)

                analytics_data = sugarscape.get_analytics_data()
                y_offset = 20
                for key, value in analytics_data.items():
                    text = font.render(f"{key}: {value}", True, BLACK)
                    analytics_surface.blit(text, (10, y_offset))
                    y_offset += 30

                screen.blit(analytics_surface, (GAME_WIDTH, 0))

                pygame.display.flip()
                clock.tick(60)  # Limit the frame rate to 60 FPS

            # Early termination condition: End the episode if fewer than 'min_ants_alive' remain
            if len(sugarscape.ants) < 3:
                print("Fewer than 3 ants remaining. Ending episode early.")
                break

        # Collect rewards for all ants after the episode ends
        total_rewards = []
        for ant in sugarscape.all_ants:
            total_rewards.append(ant.total_episode_reward)

        # Collect action characteristics from all ants
        for ant in sugarscape.all_ants:
            action_characteristics_list.extend(ant.selected_action_characteristics)
            ant.selected_action_characteristics = []  # Reset for next episode (optional)

        # No policy update during evaluation

        # End of episode timing
        episode_end_time = time.time()
        episode_duration = episode_end_time - episode_start_time

        # Compute the average reward for the episode
        if total_rewards:
            average_reward = sum(total_rewards) / len(total_rewards)
        else:
            average_reward = 0

        print(f"Episode {episode + 1}; Duration: {episode_duration:.2f} seconds; Average Reward: {average_reward:.2f}")

        # Store the average reward for this episode
        episode_rewards.append(average_reward)

        # Collect and print other metrics
        analytics_data = sugarscape.get_analytics_data()
        average_lifespan = analytics_data.get('Average Lifespan', 0)
        true_positives = analytics_data.get('True Positives', 0)
        print(f"Episode Time: {sim_time}")
        print(f"Average Lifespan: {average_lifespan:.2f}")
        print(f"True Positives: {true_positives}")

        episode_lifespans.append(average_lifespan)

    # Compute and print the overall average reward and lifespan
    total_average_reward = sum(episode_rewards) / len(episode_rewards)
    total_average_lifespan = sum(episode_lifespans) / len(episode_lifespans)
    print(f"\nOverall Average Reward over {num_episodes} episodes: {total_average_reward:.2f}")
    print(f"Overall Average Lifespan over {num_episodes} episodes: {total_average_lifespan:.2f}")

    # Process action characteristics
    # Initialize counters
    characteristic_counts = {
        'explore': 0,
        'confirmed': 0,
        'accepted': 0,
        'rejected': 0,
        'distance_bins': Counter(),
    }

    def get_distance_bin(distance):
        if distance < 100:
            return '0-100'
        elif distance < 200:
            return '100-200'
        elif distance < 300:
            return '200-300'
        elif distance < 400:
            return '300-400'
        else:
            return '400+'

    # Process action_characteristics_list
    for action_char in action_characteristics_list:
        if action_char.get('type') == 'explore':
            characteristic_counts['explore'] += 1
        else:
            # It's a 'target' action
            predominant_characteristic = action_char['predominant_characteristic']
            characteristic_counts[predominant_characteristic] += 1

            # Also process distance
            distance = action_char['distance']
            distance_bin = get_distance_bin(distance)
            characteristic_counts['distance_bins'][distance_bin] += 1

    # Plot the bar graph for action types
    action_types = ['explore', 'confirmed', 'accepted', 'rejected']
    counts = [characteristic_counts.get(atype, 0) for atype in action_types]

    plt.figure(figsize=(8,6))
    plt.bar(action_types, counts, color='skyblue')
    plt.xlabel('Action Type')
    plt.ylabel('Number of Actions')
    plt.title('Number of Actions by Type')
    plt.show()

    # Plot the histogram for distances
    distance_bins = ['0-100', '100-200', '200-300', '300-400', '400+']
    distance_counts = [characteristic_counts['distance_bins'].get(bin_label, 0) for bin_label in distance_bins]

    plt.figure(figsize=(8,6))
    plt.bar(distance_bins, distance_counts, color='salmon')
    plt.xlabel('Distance Bin')
    plt.ylabel('Number of Actions')
    plt.title('Number of Actions by Distance')
    plt.show()

    # After evaluation, plot the results
    plt.figure(figsize=(10, 6))
    plt.plot(range(1, num_episodes + 1), episode_rewards, label='Average Reward')
    plt.xlabel('Episode')
    plt.ylabel('Average Reward')
    plt.title('Average Reward per Evaluation Episode')
    plt.legend()
    plt.show()

    plt.figure(figsize=(10, 6))
    plt.plot(range(1, num_episodes + 1), episode_lifespans, label='Average Lifespan', color='orange')
    plt.xlabel('Episode')
    plt.ylabel('Average Lifespan')
    plt.title('Average Lifespan per Evaluation Episode')
    plt.legend()
    plt.show()

    if render:
        pygame.quit()

if __name__ == "__main__":
    main(render=False)  # Set render=True to visualize the simulation
