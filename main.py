import pygame
import sys
import time  # Add this import for timing
from constants import *
from sugarscape import SugarScape
from rl_agent import AntRLAgent  # Add this import

def main(render=False):
    if render:
        pygame.init()
        screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("SugarScape Simulation with Analytics")
        clock = pygame.time.Clock()
        font = pygame.font.Font(None, 24)

    # Initialize the RL agent once
    state_size = 24  # Based on your state representation
    action_size = 6  # N=5 communicated targets + 1 explore action
    shared_agent = AntRLAgent(state_size, action_size)

    num_episodes = 100  # Define the number of training episodes
    episode_length = 8000  # Define the length of each episode in time steps

    for episode in range(num_episodes):
        print(f"Starting Episode {episode + 1}/{num_episodes}")

        # Start timing the episode
        episode_start_time = time.time()  # Start time of the episode

        # Initialize the environment for each episode
        sugarscape = SugarScape(shared_agent)
        sim_time = 0  # Initialize simulation time

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
                # clock.tick(60)

            # Early termination condition: End the episode if fewer than 'min_ants_alive' remain
            if len(sugarscape.ants) < 3:
                print("Fewer than 3 ants remaining. Ending episode early.")
                break

        # End of episode timing
        episode_end_time = time.time()  # End time of the episode
        episode_duration = episode_end_time - episode_start_time  # Calculate duration
        print(f"Episode {episode + 1} Duration: {episode_duration:.2f} seconds")

        # End of episode processing (optional)
        # You can collect metrics, adjust parameters, etc.
        analytics_data = sugarscape.get_analytics_data()
        average_lifespan = analytics_data.get('Average Lifespan', 0)
        true_positives = analytics_data.get('True Positives', 0)
        print(f"Episode Time: {sim_time}")
        print(f"Average Lifespan: {average_lifespan:.2f}")
        print(f"True Positives: {true_positives}")

    # After training, save the trained agent
    shared_agent.save_model("trained_agent.pth")

    if render:
        pygame.quit()


if __name__ == "__main__":
    main(render=False)  # Run training
