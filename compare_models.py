import csv
import matplotlib.pyplot as plt
import numpy as np

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
    explore_actions = []
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
            explore_actions.append(int(row['Explore Actions']))
            target_actions.append(int(row['Target Actions']))

    data = {
        'episodes': episodes,
        'average_lifespans': average_lifespans,
        'true_locations': true_locations,
        'false_locations': false_locations,
        'explore_actions': explore_actions,
        'target_actions': target_actions
    }
    return data

def main():
    """
    Main function to read data from CSV files and generate the required plots.
    """
    # Replace with your actual CSV filenames
    model1_csv = 'B_baseline_evaluation.csv'  # Baseline model (Broadcasting)
    model2_csv = 'F_baseline_evaluation.csv'  # RL model (Face-To-Face)

    # Read data from CSV files
    model1_data = read_csv_data(model1_csv)
    model2_data = read_csv_data(model2_csv)

    ### 1. Replace Average Lifespan Line Plot with a Box Plot ###
    plt.figure(figsize=(10, 6))
    data_to_plot = [model1_data['average_lifespans'], model2_data['average_lifespans']]
    
    # Create box plot
    plt.boxplot(data_to_plot, labels=['Broadcasting', 'Face-To-Face'], patch_artist=True,
                boxprops=dict(facecolor='lightblue', color='blue'),
                medianprops=dict(color='red'),
                whiskerprops=dict(color='blue'),
                capprops=dict(color='blue'),
                flierprops=dict(color='blue', markeredgecolor='blue'))
    
    plt.ylabel('Average Lifespan')
    plt.title('Average Lifespan Distribution per Communication Strategy')
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.show()

    ### 2. Add a Bar Chart Comparing Model1 and Model2's Average Lifespan ###
    # Calculate the mean of average lifespans, ignoring NaN values
    mean_lifespan_model1 = np.nanmean(model1_data['average_lifespans'])
    mean_lifespan_model2 = np.nanmean(model2_data['average_lifespans'])

    plt.figure(figsize=(8, 6))
    models = ['Broadcasting', 'Face-To-Face']
    means = [mean_lifespan_model1, mean_lifespan_model2]
    colors = ['lightblue', 'lightgrey']
    
    bars = plt.bar(models, means, color=colors, edgecolor='black')

    # Add numerical labels on top of the bars
    for bar in bars:
        height = bar.get_height()
        plt.annotate(f'{height:.2f}',
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3),  # 3 points vertical offset
                    textcoords="offset points",
                    ha='center', va='bottom',
                    fontsize=12, fontweight='bold')

    plt.ylabel('Average Lifespan')
    plt.title('Comparison of Average Lifespan Between Models')
    plt.ylim(0, max(means)*1.2)  # Add some space on top for labels
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.show()

    ### 3. Plot Average True vs False Location Selections as Grouped Bar Chart ###
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
    ax.set_title('Average True vs False Location Selections per Communication Strategy')
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.legend()

    # Add numerical labels on top of the bars
    def autolabel(rects):
        """Attach a text label above each bar in *rects*, displaying its height."""
        for rect in rects:
            height = rect.get_height()
            ax.annotate(f'{height:.2f}',
                        xy=(rect.get_x() + rect.get_width() / 2, height),
                        xytext=(0, 3),  # 3 points vertical offset
                        textcoords="offset points",
                        ha='center', va='bottom',
                        fontsize=10, fontweight='bold')

    autolabel(rects1)
    autolabel(rects2)

    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.show()

    ### 4. Plot Average Explore vs Target Actions as Grouped Bar Chart ###
    plt.figure(figsize=(10, 6))
    width = 0.35  # Width of the bars

    # Calculate average explore and target actions per episode for each model
    average_explore_model1 = np.nanmean(model1_data['explore_actions'])
    average_target_model1 = np.nanmean(model1_data['target_actions'])
    average_explore_model2 = np.nanmean(model2_data['explore_actions'])
    average_target_model2 = np.nanmean(model2_data['target_actions'])

    # Data for grouped bar chart
    explore_averages = [average_explore_model1, average_explore_model2]
    target_averages = [average_target_model1, average_target_model2]

    x = np.arange(len(labels))  # Label locations

    fig, ax = plt.subplots(figsize=(10, 6))
    rects1 = ax.bar(x - width/2, explore_averages, width, label='Explore Actions', color='lightgrey', edgecolor='black')
    rects2 = ax.bar(x + width/2, target_averages, width, label='Target Actions', color='lightblue', edgecolor='black')

    # Add some text for labels, title and custom x-axis tick labels, etc.
    ax.set_ylabel('Average Actions per Episode')
    ax.set_title('Average Explore vs Target Actions per Communication Strategy')
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.legend()

    # Add numerical labels on top of the bars
    autolabel(rects1)
    autolabel(rects2)

    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.show()

if __name__ == '__main__':
    main()
