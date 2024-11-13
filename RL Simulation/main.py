import pygame
import sys
import time  # Add this import for timing
from constants import *
from sugarscape import SugarScape
import matplotlib.pyplot as plt  # Import for plotting
from rl_agent import AntRLAgent  # Add this import
import os  # Import for directory handling
import numpy as np
from sklearn.linear_model import LinearRegression

def moving_average(data, window_size):
    return np.convolve(data, np.ones(window_size)/window_size, mode='valid')


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

    num_episodes = 5000  # Define the number of training episodes
    episode_length = 30000  # Define the length of each episode in time steps

    episode_rewards = []
    episode_lifespans = []  # For tracking average lifespans

    # Create a 'checkpoints' directory if it doesn't exist
    checkpoint_dir = "checkpoints final - B2"
    if not os.path.exists(checkpoint_dir):
        os.makedirs(checkpoint_dir)

    # Create a 'checkpoints' directory if it doesn't exist
    model_checkpoint_dir = "model checkpoints final - B"
    if not os.path.exists(model_checkpoint_dir):
        os.makedirs(model_checkpoint_dir)

    action_characteristics_list = []

    for episode in range(num_episodes):

        print(f"Starting Episode {episode + 1}/{num_episodes}")

        # Start timing the episode
        episode_start_time = time.time()  # Start time of the episode

        # Initialize the environment for each episode
        sugarscape = SugarScape(shared_agent)
        sim_time = 0  # Initialize simulation time

        # Track the total reward for all ants
        total_rewards = []

        running = True
        while running and sim_time < episode_length:
            if render:  # Only check Pygame events when rendering is enabled
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
                clock.tick(1000)

            # Early termination condition: End the episode if fewer than 'min_ants_alive' remain
            if len(sugarscape.ants) < 3:
                print("Fewer than 3 ants remaining. Ending episode early.")
                break


        # Collect rewards for all ants after the episode ends
        total_rewards = []
        for ant in sugarscape.all_ants:
            total_rewards.append(ant.total_episode_reward)

        # Perform policy update after the episode
        shared_agent.update_policy()

        # End of episode timing
        episode_end_time = time.time()  # End time of the episode
        episode_duration = episode_end_time - episode_start_time  # Calculate duration

        # Compute the average reward for the episode
        if total_rewards:
            average_reward = sum(total_rewards) / len(total_rewards)
        else:
            average_reward = 0
        
        # Collect action characteristics from all ants
        for ant in sugarscape.all_ants:
            action_characteristics_list.extend(ant.selected_action_characteristics)
            ant.selected_action_characteristics = []  # Reset for next episode

        # Count true vs false locations
        true_location_count = sum(1 for action in action_characteristics_list if action.get('is_false_location') == False)
        false_location_count = sum(1 for action in action_characteristics_list if action.get('is_false_location') == True)

        # Count explore and target actions
        total_actions = len(action_characteristics_list)
        explore_actions = sum(1 for action in action_characteristics_list if action.get('type') == 'explore')
        target_actions = total_actions - explore_actions

        print(f"Episode {episode + 1}; Duration: {episode_duration:.2f} seconds; Average Reward: {average_reward:.2f}")

        # Store the average reward for this episode
        episode_rewards.append(average_reward)

        # End of episode processing (optional)
        # You can collect metrics, adjust parameters, etc.
        analytics_data = sugarscape.get_analytics_data()
        average_lifespan = analytics_data.get('Average Lifespan', 0)
        print(f"Episode Time: {sim_time}")
        print(f"Average Lifespan: {average_lifespan:.2f}")
        print(f"True Positives: {true_location_count}")

        # Reset action_characteristics_list for the next episode
        action_characteristics_list = []

        episode_lifespans.append(average_lifespan)

        # **Add Checkpoint Saving Here**
        # Save checkpoint every 500 episodes
        if (episode + 1) % 500 == 0:
            checkpoint_episode = episode + 1
            plt.figure(figsize=(10, 6))
            
            # Plot the average reward with transparency
            plt.plot(range(1, checkpoint_episode + 1), episode_rewards, label='Average Reward', alpha=0.6)
            
            # Compute and plot the moving average
            window_size = 50  # You can adjust the window size as needed
            if len(episode_rewards) >= window_size:
                moving_avg = moving_average(episode_rewards, window_size)
                # Adjust the x-axis for the moving average
                ma_x = range(window_size, checkpoint_episode + 1)
                plt.plot(ma_x, moving_avg, color='red', label=f'{window_size}-Episode Moving Average')
            
            plt.xlabel('Episode')
            plt.ylabel('Average Reward')
            plt.title(f'Average Reward per Episode up to Episode {checkpoint_episode}')
            plt.legend()
            checkpoint_path = os.path.join(checkpoint_dir, f'average_reward_{checkpoint_episode}.png')
            plt.savefig(checkpoint_path)
            plt.close()
            print(f"Checkpoint saved: {checkpoint_path}")

        # Save the model every 1000 episodes
        if (episode + 1) % 1000 == 0:
            model_path = os.path.join(model_checkpoint_dir, f"model_episode_{episode + 1}.pth")
            shared_agent.save_model(model_path)
            print(f"Model checkpoint saved: {model_path}")


    # After training, save the trained agent
    shared_agent.save_model("B_trained_improved_2.pth")
    print("Trained agent saved as 'trained_agent.pth'.")

    # Plot the final rewards
    plt.figure(figsize=(10, 6))
    plt.plot(range(1, num_episodes + 1), episode_rewards, label='Average Reward')
    plt.xlabel('Episode')
    plt.ylabel('Average Reward')
    plt.title('Average Reward per Episode')
    plt.legend()
    final_reward_plot = os.path.join(checkpoint_dir, f'average_reward_final.png')
    plt.savefig(final_reward_plot)
    plt.show()
    print(f"Final reward plot saved: {final_reward_plot}")

    # Plot the average lifespan
    plt.figure(figsize=(10, 6))
    plt.plot(range(1, num_episodes + 1), episode_lifespans, label='Average Lifespan', color='orange')
    plt.xlabel('Episode')
    plt.ylabel('Average Lifespan')
    plt.title('Average Lifespan per Episode')
    plt.legend()
    lifespan_plot = os.path.join(checkpoint_dir, f'average_lifespan_final.png')
    plt.savefig(lifespan_plot)
    plt.show()
    print(f"Final lifespan plot saved: {lifespan_plot}")

    # **Create Scatter Plot: Average Lifespan vs Average Reward**
    plt.figure(figsize=(10, 6))
    plt.scatter(episode_rewards, episode_lifespans, alpha=0.6, edgecolors='w', s=100)
    plt.xlabel('Average Reward')
    plt.ylabel('Average Lifespan')
    plt.title('Average Lifespan vs Average Reward per Episode')
    plt.grid(True)
    scatter_plot_path = os.path.join(checkpoint_dir, 'average_lifespan_vs_average_reward.png')
    plt.savefig(scatter_plot_path)
    plt.show()
    print(f"Scatter plot saved: {scatter_plot_path}")

     # Optional: Plot a trend line (e.g., linear regression) on the scatter plot
    if len(episode_rewards) > 1:
        # Compute linear regression
        X = np.array(episode_rewards).reshape(-1, 1)
        y = np.array(episode_lifespans)
        reg = LinearRegression().fit(X, y)
        slope = reg.coef_[0]
        intercept = reg.intercept_
        print(f"Linear Regression Model: Lifespan = {slope:.4f} * Reward + {intercept:.4f}")

        trendline = reg.predict(X)

        plt.figure(figsize=(10, 6))
        plt.scatter(episode_rewards, episode_lifespans, alpha=0.6, edgecolors='w', s=100, label='Data Points')
        plt.plot(episode_rewards, trendline, color='red', label='Trend Line')
        plt.xlabel('Average Reward')
        plt.ylabel('Average Lifespan')
        plt.title('Average Lifespan vs Average Reward per Episode with Trend Line')
        plt.legend()
        plt.grid(True)
        scatter_trend_plot_path = os.path.join(checkpoint_dir, 'average_lifespan_vs_average_reward_trend.png')
        plt.savefig(scatter_trend_plot_path)
        plt.show()
        print(f"Scatter plot with trend line saved: {scatter_trend_plot_path}")

    if render:
        pygame.quit()

if __name__ == "__main__":
    main(render=True)  # Run training
