# main.py

import pygame
from constants import *
from sugarscape import SugarScape

def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("SugarScape Simulation with Analytics")
    clock = pygame.time.Clock()

    sugarscape = SugarScape()

    font = pygame.font.Font(None, 24)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        sugarscape.update()

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
        clock.tick(60)

    pygame.quit()

if __name__ == "__main__":
    main()
