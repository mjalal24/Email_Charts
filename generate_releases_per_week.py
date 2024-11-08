import os
import csv
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from matplotlib.backends.backend_pdf import PdfPages

# Define the folder and file paths
folder_name = os.path.join('reports', 'weekly_report')
os.makedirs(folder_name, exist_ok=True)
csv_file_name = 'merged_prs_2024-10-01_to_2024-10-27'
csv_file_path = os.path.join('github', csv_file_name + '.csv')
pdf_file_path = os.path.join(folder_name, 'releases_per_week.pdf')

release_dates = []

# Function to get the abbreviated date range for a given ISO week
def iso_to_week_range(year, week_num):
    # Calculate the Monday of the given ISO week
    first_day_of_year = datetime(year, 1, 1)
    first_monday = first_day_of_year + timedelta(days=(7 - first_day_of_year.weekday()) % 7)
    start_date = first_monday + timedelta(weeks=week_num - 1)
    
    # Calculate the Sunday of the same week
    end_date = start_date + timedelta(days=6)
    
    # Return the formatted string without year and with abbreviated month
    return start_date.strftime("%b %d"), end_date.strftime("%b %d")

# Read the CSV file and gather data
with open(csv_file_path, mode='r', newline='', encoding='utf-8') as csv_file:
    reader = csv.DictReader(csv_file)
    for row in reader:
        branch = row['Branch']
        merged_at = row['Merged At']
        
        if branch == 'master':
            branch = 'prod'
        
        if branch == 'prod':
            try:
                merged_at_dt = datetime.strptime(merged_at, '%Y-%m-%dT%H:%M:%SZ')
                year, week_num, _ = merged_at_dt.isocalendar()
                # Append the year and week number
                release_dates.append((year, week_num))
            except ValueError as e:
                print(f"Error parsing date: {merged_at} - {e}")

# Count releases by week
if release_dates:
    release_counter = pd.Series(release_dates).value_counts().sort_index()

    # Convert counter to a DataFrame for plotting
    release_df = pd.DataFrame(release_counter).reset_index()
    release_df.columns = ['Year_Week', 'Prod Releases']

    # Convert the 'Year_Week' (tuple) into readable abbreviated date ranges
    release_df['Date Range'] = release_df['Year_Week'].apply(lambda x: f"{iso_to_week_range(x[0], x[1])[0]} to {iso_to_week_range(x[0], x[1])[1]}")

    # Plot weekly releases
    with PdfPages(pdf_file_path) as pdf:
        fig, ax = plt.subplots(figsize=(10, 6))

        # Plot bars with orange color
        bars = ax.bar(release_df['Date Range'], release_df['Prod Releases'], color='#fc5f05')

        # Add the exact number of releases on top of each bar with black text
        for bar, count in zip(bars, release_df['Prod Releases']):
            height = bar.get_height()
            ax.text(
                bar.get_x() + bar.get_width() / 2, 
                height, 
                f'{int(count)}', 
                ha='center', va='bottom', color='black', fontsize=12
            )

        # Set x-tick labels and rotate them for readability
        ax.set_xticklabels(release_df['Date Range'], rotation=45, ha='right')

        # Set labels and title
        ax.set_xlabel('Date Range')
        ax.set_ylabel('Number of Prod Releases')
        ax.set_title('Number of Prod Releases Per Week')

        plt.tight_layout()
        pdf.savefig()
        plt.close()

    print(f"Releases per week chart saved to {pdf_file_path}")
else:
    print("No production releases found in the CSV file.")
