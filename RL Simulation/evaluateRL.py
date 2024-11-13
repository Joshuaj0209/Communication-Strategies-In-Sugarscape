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
from collections import Counter
import csv  # Import csv module

def moving_average(data, window_size):
    return np.convolve(data, np.ones(window_size)/window_size, mode='valid')

def main(render=False):
    if render:
        pygame.init()
        screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("SugarScape Simulation with Analytics")
        clock = pygame.time.Clock()
        font = pygame.font.Font(None, 24)

    # Initialize the RL agent
    state_size = 4  # Ant's own state features
    action_feature_size = 5  # Features per action (communicated target)
    input_size = state_size + action_feature_size
    shared_agent = AntRLAgent(input_size)

    # Load the trained model
    trained_model_path = "F_trained_fixed_4.pth"  # Replace with your model filename
    shared_agent.load_model(trained_model_path)

    num_episodes = 500  # Define the number of evaluation episodes
    episode_length = 30000  # Define the length of each episode in time steps

    episode_rewards = []
    episode_lifespans = []  # For tracking average lifespans

    action_characteristics_list = []

    # Set the CSV filename based on the model being evaluated
    csv_filename = 'F_RL_evaluation_fixed_4.csv'  # You can change 'model1' to reflect your model's name

    # Open the CSV file and write the headers
    with open(csv_filename, mode='w', newline='') as csv_file:
        fieldnames = ['Episode', 'Average Reward', 'Average Lifespan', 'True Location Selections', 'False Location Selections', 'Explore Actions', 'Target Actions']
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()

    for episode in range(num_episodes):
        print(f"Starting Evaluation Episode {episode + 1}/{num_episodes}")

        # Start timing the episode
        episode_start_time = time.time()

        # Initialize the environment for each episode
        sugarscape = SugarScape(shared_agent)
        sim_time = 0  # Initialize simulation time

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
                clock.tick(500)  # Limit the frame rate to 60 FPS

            # Early termination condition: End the episode if fewer than 'min_ants_alive' remain
            if len(sugarscape.ants) == 0:
                print("All ants have died. Ending episode early.")
                break

        # Collect rewards for all ants after the episode ends
        total_rewards = []
        for ant in sugarscape.all_ants:
            total_rewards.append(ant.total_episode_reward)

        # Collect action characteristics from all ants
        for ant in sugarscape.all_ants:
            action_characteristics_list.extend(ant.selected_action_characteristics)
            ant.selected_action_characteristics = []  # Reset for next episode

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
        false_positives = analytics_data.get('False Positives', 0)

        print(f"Episode Time: {sim_time}")
        print(f"Average Lifespan: {average_lifespan:.2f}")

        episode_lifespans.append(average_lifespan)


        # Count explore and target actions
        total_actions = len(action_characteristics_list)
        explore_actions = sum(1 for action in action_characteristics_list if action.get('type') == 'explore')
        target_actions = total_actions - explore_actions

        # Append the data to the CSV file
        with open(csv_filename, mode='a', newline='') as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            writer.writerow({
                'Episode': episode + 1,
                'Average Reward': average_reward,
                'Average Lifespan': average_lifespan,
                'True Location Selections': true_positives,
                'False Location Selections': false_positives,
                'Explore Actions': explore_actions,
                'Target Actions': target_actions
            })

        # Reset action_characteristics_list for the next episode
        action_characteristics_list = []

    # Compute and print the overall average reward and lifespan
    total_average_reward = sum(episode_rewards) / len(episode_rewards)
    total_average_lifespan = sum(episode_lifespans) / len(episode_lifespans)
    print(f"\nOverall Average Reward over {num_episodes} episodes: {total_average_reward:.2f}")
    print(f"Overall Average Lifespan over {num_episodes} episodes: {total_average_lifespan:.2f}")

    if render:
        pygame.quit()

if __name__ == "__main__":
    main(render=False)  # Set render=True to visualize the simulation
