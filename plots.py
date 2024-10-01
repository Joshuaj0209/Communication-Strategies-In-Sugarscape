import pandas as pd
import matplotlib.pyplot as plt

# Load the CSV files into pandas DataFrames
broad_df = pd.read_csv("broadcast.csv")
face_df = pd.read_csv("f2f.csv")

# Calculate the average for each metric
broad_averages = broad_df.mean()
face_averages = face_df.mean()

# Create a DataFrame to compare the averages side by side
averages_df = pd.DataFrame({
    "Broad Communication": broad_averages,
    "Face-to-Face Communication": face_averages
})

# Display the average values
print("Average values for Broad Communication:")
print(broad_averages)
print("\nAverage values for Face-to-Face Communication:")
print(face_averages)

# Metrics to plot (updated to include 'Median Lifespan' instead of 'Average Lifespan')
metrics_to_plot = ["Median Lifespan", "Exploits", "Explores", "True Positives", "False Positives"]

# Plot each metric in a bar chart to compare the two approaches
for metric in metrics_to_plot:
    if metric in averages_df.index:  # Check if the metric is present in the DataFrame index (rows)
        plt.figure()
        averages_df.loc[metric].plot(kind='bar', title=f"Comparison of {metric}")
        plt.ylabel(metric)
        plt.xticks(rotation=0)
        plt.legend(["Broad Communication", "Face-to-Face Communication"])
        plt.show()
    else:
        print(f"Metric '{metric}' not found in the data.")

# Additional plot: Compare Total Sugar Patches, Consumed Sugar, Remaining Sugar
plt.figure()
averages_df.loc[['Total Sugar Patches', 'Consumed Sugar', 'Remaining Sugar']].plot(kind='bar', title="Sugar Patch Statistics Comparison")
plt.ylabel("Sugar Metrics")
plt.xticks(rotation=0)
plt.legend(["Broad Communication", "Face-to-Face Communication"])
plt.show()

# Boxplot for the distribution of 'Median Lifespan'
plt.figure(figsize=(8, 6))
plt.boxplot([broad_df['Median Lifespan'], face_df['Median Lifespan']], labels=['Broad Communication', 'Face-to-Face Communication'])
plt.title("Distribution of Median Lifespan")
plt.ylabel("Median Lifespan")
plt.show()
