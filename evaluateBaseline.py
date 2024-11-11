import pygame
import sys
import time
from constants import *
from sugarscape import SugarScape
import matplotlib.pyplot as plt
import os
import numpy as np
from sklearn.linear_model import LinearRegression
from collections import Counter
import csv  # Import csv module

def moving_average(data, window_size):
    return np.convolve(data, np.ones(window_size)/window_size, mode='valid')

def plot_histograms(action_characteristics):
    # Initialize lists to hold counts
    confirmed_counts = []
    rejected_counts = []
    accepted_counts = []

    # Iterate through all action characteristics
    for action in action_characteristics:
        if action.get('type') == 'target':
            counts = action.get('counts', {})
            confirmed = counts.get('confirmed', 0)
            rejected = counts.get('rejected', 0)
            accepted = counts.get('accepted', 0)

            confirmed_counts.append(confirmed)
            rejected_counts.append(rejected)
            accepted_counts.append(accepted)

    # Define bin edges with bin size 2
    max_count = max(
        max(confirmed_counts, default=0),
        max(rejected_counts, default=0),
        max(accepted_counts, default=0)
    )
    bins = range(0, max_count + 3, 1)  # +3 to include the last bin

    # Plotting
    plt.figure(figsize=(18, 5))

    # Confirmed Histogram
    plt.subplot(1, 3, 1)
    total_confirmed = len(confirmed_counts)
    if total_confirmed > 0:
        weights_confirmed = np.ones_like(confirmed_counts) / total_confirmed * 100
    else:
        weights_confirmed = None
    plt.hist(confirmed_counts, bins=bins, color='skyblue', edgecolor='black', weights=weights_confirmed)
    plt.title('Confirmed Counts')
    plt.xlabel('Number of Confirmed')
    plt.ylabel('Percentage')
    plt.xticks(bins)
    plt.ylim(0, 100)

    # Rejected Histogram
    plt.subplot(1, 3, 2)
    total_rejected = len(rejected_counts)
    if total_rejected > 0:
        weights_rejected = np.ones_like(rejected_counts) / total_rejected * 100
    else:
        weights_rejected = None
    plt.hist(rejected_counts, bins=bins, color='salmon', edgecolor='black', weights=weights_rejected)
    plt.title('Rejected Counts')
    plt.xlabel('Number of Rejected')
    plt.ylabel('Percentage')
    plt.xticks(bins)
    plt.ylim(0, 100)

    # Accepted Histogram
    plt.subplot(1, 3, 3)
    total_accepted = len(accepted_counts)
    if total_accepted > 0:
        weights_accepted = np.ones_like(accepted_counts) / total_accepted * 100
    else:
        weights_accepted = None
    plt.hist(accepted_counts, bins=bins, color='lightgreen', edgecolor='black', weights=weights_accepted)
    plt.title('Accepted Counts')
    plt.xlabel('Number of Accepted')
    plt.ylabel('Percentage')
    plt.xticks(bins)
    plt.ylim(0, 100)

    plt.tight_layout()
    plt.show()

    # Optionally, save the figure
    plt.savefig('action_characteristics_histograms.png')
    print("Histograms saved as 'action_characteristics_histograms.png'")

def main(render=False):
    if render:
        pygame.init()
        screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("SugarScape Simulation with Analytics")
        clock = pygame.time.Clock()
        font = pygame.font.Font(None, 24)

    num_episodes = 500  # Define the number of evaluation episodes
    episode_length = 30000  # Define the length of each episode in time steps

    episode_lifespans = []  # For tracking average lifespans

    action_characteristics_list = []
    all_action_characteristics = []  # To store all action characteristics across episodes

    # Set the CSV filename based on the model being evaluated
    csv_filename = 'F_baseline_evaluation_2.csv'  # You can change 'Baseline' to reflect your model's name

    # Open the CSV file and write the headers
    with open(csv_filename, mode='w', newline='') as csv_file:
        fieldnames = ['Episode', 'Average Lifespan', 'True Location Selections', 'False Location Selections', 'Explore Actions', 'Target Actions']
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()

    for episode in range(num_episodes):
        print(f"Starting Evaluation Episode {episode + 1}/{num_episodes}")

        # Start timing the episode
        episode_start_time = time.time()

        # Initialize the environment for each episode
        sugarscape = SugarScape()
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
                clock.tick(150)  # Limit the frame rate to 60 FPS

            # Early termination condition: End the episode if fewer than 'min_ants_alive' remain
            if len(sugarscape.ants) == 0:
                print("All ants died. Ending episode early.")
                break

        # Collect action characteristics from all ants
        for ant in sugarscape.all_ants:
            action_characteristics_list.extend(ant.selected_action_characteristics)
            ant.selected_action_characteristics = []  # Reset for next episode

        # Append to all_action_characteristics
        all_action_characteristics.extend(action_characteristics_list)

        # End of episode timing
        episode_end_time = time.time()
        episode_duration = episode_end_time - episode_start_time

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
                'Average Lifespan': average_lifespan,
                'True Location Selections': true_positives,
                'False Location Selections': false_positives,
                'Explore Actions': explore_actions,
                'Target Actions': target_actions
            })

        # Reset action_characteristics_list for the next episode
        action_characteristics_list = []

    # Compute and print the overall average lifespan
    total_average_lifespan = sum(episode_lifespans) / len(episode_lifespans)
    print(f"\nOverall Average Lifespan over {num_episodes} episodes: {total_average_lifespan:.2f}")

    if render:
        pygame.quit()

    # Plot Histograms
    plot_histograms(all_action_characteristics)

if __name__ == "__main__":
    main(render=False)  # Set render=True to visualize the simulation
