import pygame
import csv
from constants import *
from sugarscape import SugarScape

# Function to run the simulation
def run_simulation(sim_number):
    pygame.init()
    sim_time = 0  # Initialize simulation time
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption(f"SugarScape Simulation {sim_number + 1}")
    clock = pygame.time.Clock()

    sugarscape = SugarScape()
    running = True

    # Run the simulation until a condition or maximum sim_time is reached
    max_sim_time = 15000  # Example: Limit each simulation to 10,000 steps (you can adjust this)
    
    while running and sim_time < max_sim_time:
        sim_time += 1  # Increment simulation time per frame

        sugarscape.update(sim_time)

        # You can comment out the rendering to speed up the simulation
        # game_surface = pygame.Surface((GAME_WIDTH, HEIGHT))
        # sugarscape.draw(game_surface)
        # screen.blit(game_surface, (0, 0))

        # pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # clock.tick(60)  # Use this to limit FPS if rendering is enabled

    # Quit pygame for this run
    pygame.quit()

    # Return the analytics data at the end of the simulation
    return sugarscape.get_analytics_data()

# Function to save analytics data to a CSV file
def save_analytics_to_csv(analytics_list, filename='broadcast.csv'):
    # Define CSV column headers based on the keys in the analytics dictionary
    headers = [
        'Total Sugar Patches', 'Consumed Sugar', 'Remaining Sugar', 
        'Number of Ants', 'Dead Ants', 'Average Lifespan', 
        'True Positives', 'False Positives', 'Exploits', 'Explores'
    ]

    # Write the data to the CSV file
    with open(filename, mode='w', newline='') as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=headers)
        writer.writeheader()  # Write the headers
        for analytics in analytics_list:
            writer.writerow(analytics)

# Main function to run the simulation multiple times
def main():
    num_simulations = 4  # Number of times to run the simulation
    all_analytics = []  # List to hold analytics data for all simulations

    # Run the simulation multiple times
    for i in range(num_simulations):
        print(f"Running simulation {i + 1}/{num_simulations}")
        analytics_data = run_simulation(i)
        all_analytics.append(analytics_data)

    # Save all collected analytics to a CSV file
    save_analytics_to_csv(all_analytics)

if __name__ == "__main__":
    main()
