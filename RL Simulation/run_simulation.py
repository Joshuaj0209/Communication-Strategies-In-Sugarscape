import pygame
import sys
import os 
from constants import *
from sugarscape import SugarScape
from rl_agent import AntRLAgent

def run_simulation_with_rl():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("SugarScape Simulation with RL Visualization")
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 24)

    base_dir = os.path.dirname(os.path.abspath(__file__))  
    trained_model_path = os.path.join(base_dir, "RL_Models", "Broadcast_trained.pth")  # Change this Face_trained.pth for the face-to-face simulation
    

    # Initialize the RL agent
    state_size = 4  # Ant's own state features
    action_feature_size = 5  # Features per action (communicated target)
    input_size = state_size + action_feature_size
    shared_agent = AntRLAgent(input_size)

    # Load the trained model
    shared_agent.load_model(trained_model_path)

    # Initialize the environment
    sugarscape = SugarScape(shared_agent)
    sim_time = 0

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                pygame.quit()
                sys.exit()

        sim_time += 1

        # Update the simulation
        sugarscape.update(sim_time)

         # Check if all ants have died and end the simulation
        if len(sugarscape.ants) == 0:
            print("All ants have died. Ending simulation.")
            running = False
            break

        # Render the game surface
        game_surface = pygame.Surface((GAME_WIDTH, HEIGHT))
        sugarscape.draw(game_surface)
        screen.blit(game_surface, (0, 0))

        # Render the analytics surface
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

        # Update the display
        pygame.display.flip()
        clock.tick(120)  # Set to 60 frames per second

if __name__ == "__main__":
    run_simulation_with_rl()
