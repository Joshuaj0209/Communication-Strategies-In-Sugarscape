import pygame
import sys
from constants import *
from sugarscape import SugarScape
from rl_agent import AntRLAgent  # Add this import

def main(render=False):
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("SugarScape Simulation with Analytics")
    clock = pygame.time.Clock()

    # Initialize the RL agent once
    state_size = 24  # Based on your state representation
    action_size = 6  # N=5 communicated targets + 1 explore action
    shared_agent = AntRLAgent(state_size, action_size)

    font = pygame.font.Font(None, 24)

    num_episodes = 1000  # Define the number of training episodes
    episode_length = 20000  # Define the length of each episode in time steps

    for episode in range(num_episodes):
        print(f"Starting Episode {episode + 1}/{num_episodes}")

        # Initialize the environment for each episode
        sugarscape = SugarScape(shared_agent)

        running = True
        time_step = 0
        while running and time_step < episode_length:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    pygame.quit()
                    sys.exit()

            sugarscape.update()
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

            time_step += 1

        # End of episode processing (optional)
        # You can collect metrics, adjust parameters, etc.

        analytics_data = sugarscape.get_analytics_data()
        average_lifespan = analytics_data.get('Average Lifespan', 0)
        true_positives = analytics_data.get('True Positives', 0)
        print(f"Episode Time: {time_step}")
        print(f"Average Lifespan: {average_lifespan:.2f}")
        print(f"True Positives: {true_positives}")


    # After training, save the trained agent
    shared_agent.save_model("trained_agent.pth")

    pygame.quit()


if __name__ == "__main__":
    main(render=False)  # Run training
    # evaluate_agent()  # Run evaluation after training
