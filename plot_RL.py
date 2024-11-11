import csv
import matplotlib.pyplot as plt
import numpy as np
import os

def moving_average(data, window_size):
    """Calculate the moving average of the data with the specified window size."""
    return np.convolve(data, np.ones(window_size)/window_size, mode='valid')

def read_csv_data(csv_file):
    """
    Read data from a CSV file and return lists of episodes, average rewards,
    average lifespans, and percentage of true locations.
    """
    episodes = []
    average_rewards = []
    average_lifespans = []
    true_location_percentages = []

    if not os.path.exists(csv_file):
        print(f"CSV file '{csv_file}' not found.")
        return episodes, average_rewards, average_lifespans, true_location_percentages

    with open(csv_file, 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            episode = int(row['Episode'])
            avg_reward = float(row['Average Reward'])
            avg_lifespan = float(row['Average Lifespan'])
            true_count = int(row['True Location Count'])
            false_count = int(row['False Location Count'])
            total_locations = true_count + false_count
            if total_locations > 0:
                true_percentage = (true_count / total_locations) * 100
            else:
                true_percentage = 0  # Avoid division by zero

            episodes.append(episode)
            average_rewards.append(avg_reward)
            average_lifespans.append(avg_lifespan)
            true_location_percentages.append(true_percentage)

    return episodes, average_rewards, average_lifespans, true_location_percentages

def plot_moving_average(datasets, window_size, xlabel, ylabel, title, filename):
    """
    Plot the moving average of multiple datasets over episodes and save the plot to a file.
    
    Parameters:
    - datasets: List of dictionaries with keys 'x', 'y', 'label', 'color', and optionally 'linestyle'.
    - window_size: Window size for moving average.
    - xlabel: Label for the x-axis.
    - ylabel: Label for the y-axis.
    - title: Title of the plot.
    - filename: Filename to save the plot.
    """
    plt.figure(figsize=(12, 8))  # Increased figure size for better clarity

    for data in datasets:
        ma_y = moving_average(data['y'], window_size)
        ma_x = data['x'][window_size - 1:]  # Adjust x-axis to match the length of ma_y
        plt.plot(ma_x, ma_y, label=data['label'], color=data['color'],
                 linestyle=data.get('linestyle', '-'), linewidth=3, alpha=0.9)

    plt.xlabel(xlabel, fontsize=14)
    plt.ylabel(ylabel, fontsize=14)
    plt.title(title, fontsize=16)
    plt.legend(fontsize=12)
    plt.grid(True, which='both', linestyle='--', linewidth=0.5, alpha=0.7)
    plt.tight_layout()  # Adjust layout to prevent clipping
    plt.savefig(filename)
    plt.close()
    print(f"Plot saved: {filename}")

def main():
    # File paths
    training_file = "RL_Training_B_fixed_10.csv"      # Face-To-Face
    complete_file = "RL_Training_B_fixed_4.csv"     # Widespread Broadcasting

    # Flag to include the second CSV file
    include_complete = True  # Set to True to include the second CSV

    # Read data from Face-To-Face CSV
    train_episodes, train_rewards, train_lifespans, train_true_percentages = read_csv_data(training_file)

    if not train_episodes:
        print(f"No data found in '{training_file}'. Exiting.")
        return

    # Define colorblind-friendly colors
    face_to_face_color = '#377eb8'             # Blue
    widespread_broadcasting_color = '#e41a1c'  # Red

    # Initialize datasets with updated labels
    datasets_reward = [
        {
            'x': train_episodes,
            'y': train_rewards,
            'label': 'Face-To-Face',
            'color': face_to_face_color,
            'linestyle': '-'  # Solid line
        }
    ]

    datasets_lifespan = [
        {
            'x': train_episodes,
            'y': train_lifespans,
            'label': 'Face-To-Face',
            'color': face_to_face_color,
            'linestyle': '-'  # Solid line
        }
    ]

    datasets_true_percentage = [
        {
            'x': train_episodes,
            'y': train_true_percentages,
            'label': 'Face-To-Face',
            'color': face_to_face_color,
            'linestyle': '-'  # Solid line
        }
    ]

    if include_complete:
        complete_episodes, complete_rewards, complete_lifespans, complete_true_percentages = read_csv_data(complete_file)
        
        if not complete_episodes:
            print(f"No data found in '{complete_file}'. Continuing with only the Face-To-Face data.")
        else:
            # Append Widespread Broadcasting data with distinct styles
            datasets_reward.append({
                'x': complete_episodes,
                'y': complete_rewards,
                'label': 'Widespread Broadcasting',
                'color': widespread_broadcasting_color,
                'linestyle': '-'  # Solid line
            })
            datasets_lifespan.append({
                'x': complete_episodes,
                'y': complete_lifespans,
                'label': 'Widespread Broadcasting',
                'color': widespread_broadcasting_color,
                'linestyle': '-'  # Dashed line
            })
            datasets_true_percentage.append({
                'x': complete_episodes,
                'y': complete_true_percentages,
                'label': 'Widespread Broadcasting',
                'color': widespread_broadcasting_color,
                'linestyle': '-'  # Solid line
            })

    window_size = 100  # Window size for moving average

    # Plot 1: Moving average of average reward over episodes
    plot_moving_average(
        datasets=datasets_reward,
        window_size=window_size,
        xlabel='Episode',
        ylabel='Average Reward',
        title='Moving Average of Average Reward over Episodes',
        filename='average_reward_moving_average.png'
    )

    # Plot 2: Moving average of average lifespan over episodes
    plot_moving_average(
        datasets=datasets_lifespan,
        window_size=window_size,
        xlabel='Episode',
        ylabel='Average Lifespan',
        title='Moving Average of Average Lifespan over Episodes',
        filename='average_lifespan_moving_average.png'
    )

    # Plot 3: Moving average of percentage of true location counts over episodes
    plot_moving_average(
        datasets=datasets_true_percentage,
        window_size=window_size,
        xlabel='Episode',
        ylabel='Percentage of True Locations (%)',
        title='Moving Average of Percentage of True Locations over Episodes',
        filename='true_location_percentage_moving_average.png'
    )

if __name__ == "__main__":
    main()
