import pygame
import sys
from constants import *
from sugarscape import SugarScape

def run_simulation():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("SugarScape Simulation Visualization")
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 24)

    # Initialize the environment
    sugarscape = SugarScape()
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
        clock.tick(120)  # Increase this value to make the simulation run faster

if __name__ == "__main__":
    run_simulation()