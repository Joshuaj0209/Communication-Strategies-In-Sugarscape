import csv
import matplotlib.pyplot as plt
import numpy as np
import os

def read_csv_data(filename):
    """
    Reads the CSV file and extracts relevant data.

    Parameters:
        filename (str): Path to the CSV file.

    Returns:
        dict: A dictionary containing lists of extracted data.
    """
    episodes = []
    average_lifespans = []
    true_locations = []
    false_locations = []
    wander_actions = []  # Changed from 'explore_actions' to 'wander_actions'
    target_actions = []

    with open(filename, mode='r', newline='') as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            episodes.append(int(row['Episode']))
            
            # Handle 'Average Lifespan' which should exist for both models
            average_lifespan = row.get('Average Lifespan', None)
            if average_lifespan is not None and average_lifespan != '':
                average_lifespans.append(float(average_lifespan))
            else:
                average_lifespans.append(np.nan)  # Assign NaN if missing

            true_locations.append(int(row['True Location Selections']))
            false_locations.append(int(row['False Location Selections']))
            wander_actions.append(int(row['Explore Actions']))  # Changed to 'wander_actions'
            target_actions.append(int(row['Target Actions']))

    data = {
        'episodes': episodes,
        'average_lifespans': average_lifespans,
        'true_locations': true_locations,
        'false_locations': false_locations,
        'wander_actions': wander_actions,  # Changed key
        'target_actions': target_actions
    }
    return data

def main():
    """
    Main function to read data from CSV files and generate the required plots.
    """
    # Define the Evaluation folder path
    evaluation_folder = 'Evaluation_baseline_2'

    # Create the Evaluation folder if it doesn't exist
    if not os.path.exists(evaluation_folder):
        os.makedirs(evaluation_folder)
        print(f"Created folder: {evaluation_folder}")
    else:
        print(f"Folder already exists: {evaluation_folder}")

    # Replace with your actual CSV filenames
    model1_csv = 'B_baseline_evaluation_2.csv'  # Broadcasting
    model2_csv = 'F_baseline_evaluation_2.csv'  # Face-To-Face

    # Read data from CSV files
    model1_data = read_csv_data(model1_csv)
    model2_data = read_csv_data(model2_csv)

    ### 1. Box Plot for Average Lifespan ###
    plt.figure(figsize=(10, 6))
    data_to_plot = [model1_data['average_lifespans'], model2_data['average_lifespans']]
    
    # Create box plot
    box = plt.boxplot(data_to_plot, labels=['Broadcasting', 'Face-To-Face'], patch_artist=True,
                boxprops=dict(facecolor='lightblue', color='blue'),
                medianprops=dict(color='red'),
                whiskerprops=dict(color='blue'),
                capprops=dict(color='blue'),
                flierprops=dict(color='blue', markeredgecolor='blue'))

    plt.ylabel('Average Lifespan')
    plt.title('Average Lifespan Distribution per Communication Strategy')
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    
    # Save the box plot to the Evaluation folder
    box_plot_path = os.path.join(evaluation_folder, 'average_lifespan_boxplot.png')
    plt.savefig(box_plot_path)
    plt.close()
    print(f"Box plot saved to: {box_plot_path}")

    ### 2. Bar Chart Comparing Average Lifespan ###
    # Calculate the mean of average lifespans, ignoring NaN values
    mean_lifespan_model1 = np.nanmean(model1_data['average_lifespans'])
    mean_lifespan_model2 = np.nanmean(model2_data['average_lifespans'])

    plt.figure(figsize=(8, 6))
    models = ['Broadcasting', 'Face-To-Face']
    means = [mean_lifespan_model1, mean_lifespan_model2]
    colors = ['lightblue', 'lightgrey']
    
    bars = plt.bar(models, means, color=colors, edgecolor='black')

    # Add numerical count labels above the bars
    for bar in bars:
        height = bar.get_height()
        plt.annotate(f'{height:.2f}',  # Numerical count
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 5),  # 5 points vertical offset
                    textcoords="offset points",
                    ha='center', va='bottom',
                    fontsize=12, fontweight='bold')

    plt.ylabel('Average Lifespan')
    plt.title('Average Lifespan per Communication Strategies (RL)')
    plt.ylim(0, max(means)*1.3)  # Add some space on top for labels
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    
    # Save the bar chart to the Evaluation folder
    bar_chart_path = os.path.join(evaluation_folder, 'average_lifespan_comparison.png')
    plt.savefig(bar_chart_path)
    plt.close()
    print(f"Bar chart saved to: {bar_chart_path}")

    ### 3. Grouped Bar Chart for True vs False Location Selections ###
    plt.figure(figsize=(10, 6))
    width = 0.35  # Width of the bars

    # Calculate average true and false location selections per episode for each model
    average_true_model1 = np.nanmean(model1_data['true_locations'])
    average_false_model1 = np.nanmean(model1_data['false_locations'])
    average_true_model2 = np.nanmean(model2_data['true_locations'])
    average_false_model2 = np.nanmean(model2_data['false_locations'])

    # Data for grouped bar chart
    labels = ['Broadcasting', 'Face-To-Face']
    true_averages = [average_true_model1, average_true_model2]
    false_averages = [average_false_model1, average_false_model2]

    x = np.arange(len(labels))  # Label locations

    fig, ax = plt.subplots(figsize=(10, 6))
    rects1 = ax.bar(x - width/2, true_averages, width, label='True Location Selections', color='lightblue', edgecolor='black')
    rects2 = ax.bar(x + width/2, false_averages, width, label='False Location Selections', color='lightgrey', edgecolor='black')

    # Add some text for labels, title and custom x-axis tick labels, etc.
    ax.set_ylabel('Average Location Selections per Episode')
    ax.set_title('Average True vs False Location Selections per Communication Strategy (RL)')
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.legend()

    # Calculate and annotate percentages above the bars
    for i in range(len(labels)):
        # Calculate total for the group
        total = true_averages[i] + false_averages[i]
        if total > 0:
            true_pct = (true_averages[i] / total) * 100
            false_pct = (false_averages[i] / total) * 100
            
            # Annotate True Location Selections
            ax.text(x[i] - width/2, true_averages[i] + (max(true_averages + false_averages) * 0.01),
                    f'{true_pct:.1f}%', ha='center', va='bottom', fontsize=10, color='blue', fontweight='bold')
            
            # Annotate False Location Selections
            ax.text(x[i] + width/2, false_averages[i] + (max(true_averages + false_averages) * 0.01),
                    f'{false_pct:.1f}%', ha='center', va='bottom', fontsize=10, color='grey', fontweight='bold')
        else:
            ax.text(x[i] - width/2, 1, '0%', ha='center', va='bottom', fontsize=10, color='blue')
            ax.text(x[i] + width/2, 1, '0%', ha='center', va='bottom', fontsize=10, color='grey')

    plt.grid(axis='y', linestyle='--', alpha=0.7)
    
    # Save the grouped bar chart to the Evaluation folder
    grouped_bar_chart_path = os.path.join(evaluation_folder, 'true_false_location_selections.png')
    plt.savefig(grouped_bar_chart_path)
    plt.close()
    print(f"Grouped bar chart (True vs False Locations) saved to: {grouped_bar_chart_path}")

    ### 4. Grouped Bar Chart for Wander vs Target Actions ###
    plt.figure(figsize=(10, 6))
    width = 0.35  # Width of the bars

    # Calculate average wander and target actions per episode for each model
    average_wander_model1 = np.nanmean(model1_data['wander_actions'])  # Changed from 'explore_actions'
    average_target_model1 = np.nanmean(model1_data['target_actions'])
    average_wander_model2 = np.nanmean(model2_data['wander_actions'])  # Changed from 'explore_actions'
    average_target_model2 = np.nanmean(model2_data['target_actions'])

    # Data for grouped bar chart
    wander_averages = [average_wander_model1, average_wander_model2]  # Changed variable name
    target_averages = [average_target_model1, average_target_model2]

    x = np.arange(len(labels))  # Label locations

    fig, ax = plt.subplots(figsize=(10, 6))
    rects1 = ax.bar(x - width/2, wander_averages, width, label='Wander Actions', color='lightgrey', edgecolor='black')  # Changed label
    rects2 = ax.bar(x + width/2, target_averages, width, label='Target Actions', color='lightblue', edgecolor='black')

    # Add some text for labels, title and custom x-axis tick labels, etc.
    ax.set_ylabel('Average Actions per Episode')
    ax.set_title('Average Wander vs Target Actions per Communication Strategy (RL)')
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.legend()

    # Calculate and annotate percentages above the bars
    for i in range(len(labels)):
        # Calculate total for the group
        total = wander_averages[i] + target_averages[i]
        if total > 0:
            wander_pct = (wander_averages[i] / total) * 100
            target_pct = (target_averages[i] / total) * 100
            
            # Annotate Wander Actions
            ax.text(x[i] - width/2, wander_averages[i] + (max(wander_averages + target_averages) * 0.01),
                    f'{wander_pct:.1f}%', ha='center', va='bottom', fontsize=10, color='grey', fontweight='bold')
            
            # Annotate Target Actions
            ax.text(x[i] + width/2, target_averages[i] + (max(wander_averages + target_averages) * 0.01),
                    f'{target_pct:.1f}%', ha='center', va='bottom', fontsize=10, color='blue', fontweight='bold')
        else:
            ax.text(x[i] - width/2, 1, '0%', ha='center', va='bottom', fontsize=10, color='grey')
            ax.text(x[i] + width/2, 1, '0%', ha='center', va='bottom', fontsize=10, color='blue')

    plt.grid(axis='y', linestyle='--', alpha=0.7)
    
    # Save the grouped bar chart to the Evaluation folder
    explore_target_bar_chart_path = os.path.join(evaluation_folder, 'wander_target_actions.png')  # Changed filename
    plt.savefig(explore_target_bar_chart_path)
    plt.close()
    print(f"Grouped bar chart (Wander vs Target Actions) saved to: {explore_target_bar_chart_path}")

if __name__ == '__main__':
    main()
