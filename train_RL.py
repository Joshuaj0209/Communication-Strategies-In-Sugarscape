import pygame
import sys
import time  # For timing
from constants import *
from sugarscape import SugarScape
from rl_agent import AntRLAgent  # RL Agent
import os  # For directory handling
import csv  # For CSV operations

def main(render=False):
    if render:
        pygame.init()
        screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("SugarScape Simulation with Analytics")
        clock = pygame.time.Clock()
        font = pygame.font.Font(None, 24)

    # Initialize the RL agent once
    state_size = 4  # Ant's own state features
    action_feature_size = 5  # Features per action (communicated target)
    input_size = state_size + action_feature_size
    shared_agent = AntRLAgent(input_size)

    num_episodes = 5000  # Total number of training episodes
    episode_length = 30000  # Length of each episode in time steps

    episode_rewards = []
    episode_lifespans = []  # For tracking average lifespans

    # Create necessary directories if they don't exist
    checkpoint_dir = "checkpoints 2 hidden - F"
    os.makedirs(checkpoint_dir, exist_ok=True)

    model_checkpoint_dir = "model checkpoints 2 hidden - F"
    os.makedirs(model_checkpoint_dir, exist_ok=True)

    action_characteristics_list = []

    # Initialize a list to store training data per episode
    training_data = []

    # Define CSV file path
    csv_file = "RL_Training_F_2_hidden.csv"
    csv_columns = ['Episode', 'Average Reward', 'Average Lifespan',
                   'True Location Count', 'False Location Count',
                   'Explore Actions', 'Target Actions']

    # Check if CSV file exists to determine if header needs to be written
    file_exists = os.path.isfile(csv_file)

    # Open CSV file once outside the loop to improve performance
    with open(csv_file, 'a', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=csv_columns)

        # Write header only if file does not exist
        if not file_exists:
            writer.writeheader()

        for episode in range(num_episodes):

            # print(f"Starting Episode {episode + 1}/{num_episodes}")

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
                    clock.tick(500)

                # Early termination condition: End the episode if fewer than 3 ants remain
                if len(sugarscape.ants) == 0:
                    print("All ants have died. Ending episode early.")
                    break

            # Collect rewards for all ants after the episode ends
            total_rewards = [ant.total_episode_reward for ant in sugarscape.all_ants]

            # Perform policy update after the episode
            shared_agent.update_policy()

            # End of episode timing
            episode_end_time = time.time()
            episode_duration = episode_end_time - episode_start_time

            # Compute the average reward for the episode
            average_reward = sum(total_rewards) / len(total_rewards) if total_rewards else 0

            # Collect action characteristics from all ants
            for ant in sugarscape.all_ants:
                action_characteristics_list.extend(ant.selected_action_characteristics)
                ant.selected_action_characteristics = []  # Reset for next episode

            # Count explore and target actions
            total_actions = len(action_characteristics_list)
            explore_actions = sum(
                1 for action in action_characteristics_list if action.get('type') == 'explore')
            target_actions = total_actions - explore_actions

            print(f"Episode {episode + 1}; Duration: {episode_duration:.2f} seconds; Average Reward: {average_reward:.2f}")

            # Store the average reward for this episode
            episode_rewards.append(average_reward)

            # End of episode processing
            analytics_data = sugarscape.get_analytics_data()
            average_lifespan = analytics_data.get('Average Lifespan', 0)
            true_positives = analytics_data.get('True Positives',0)
            false_positives = analytics_data.get('False Positives',0)
            # print(f"Episode Time: {sim_time}")
            print(f"Average Lifespan: {average_lifespan:.2f}")
            # print(f"True Positives: {true_positives}")
            # print(f"False Positives: {false_positives}")
            # print(f"explore actions: {explore_actions}")
            # print(f"target actions: {target_actions}")

            # Reset action_characteristics_list for the next episode
            action_characteristics_list = []

            episode_lifespans.append(average_lifespan)

            # Collect data for CSV
            training_data.append({
                'Episode': episode + 1,
                'Average Reward': average_reward,
                'Average Lifespan': average_lifespan,
                'True Location Count': true_positives,
                'False Location Count': false_positives,
                'Explore Actions': explore_actions,
                'Target Actions': target_actions
            })

            # Every 500 episodes, write collected data to CSV and clear the list
            if (episode + 1) % 100 == 0:
                print(f"Saving data for episodes {episode + 1 - 999} to {episode + 1} to CSV.")
                for data in training_data:
                    writer.writerow(data)
                csvfile.flush()  # Ensure data is written to disk
                print(f"Data for episodes {episode + 1 - 999} to {episode + 1} saved to '{csv_file}'.")
                training_data = []  # Clear the list for the next batch

            if (episode + 1) % 500 == 0:
                # save model checkpoints every 500 episodes
                model_path = os.path.join(model_checkpoint_dir, f"model_episode_{episode + 1}.pth")
                shared_agent.save_model(model_path)
                print(f"Model checkpoint saved: {model_path}")

        # After training, save any remaining data that didn't reach the 500-episode batch
        if training_data:
            print(f"Saving remaining data for episodes {num_episodes - len(training_data) + 1} to {num_episodes} to CSV.")
            for data in training_data:
                writer.writerow(data)
            csvfile.flush()
            print(f"Remaining data saved to '{csv_file}'.")

    # After training, save the trained agent
    shared_agent.save_model("F_trained_2_hidden.pth")
    print("Trained agent saved as 'F_trained_2_hidden.pth'.")

    if render:
        pygame.quit()

if __name__ == "__main__":
    main(render=True)  # Run training
