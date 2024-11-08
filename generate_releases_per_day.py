import os
import csv
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
from matplotlib.backends.backend_pdf import PdfPages  # Import PdfPages
import matplotlib.dates as mdates

# Define the folder and file paths
folder_name = os.path.join('reports', 'daily_report')  # Renamed to 'daily_report' for clarity
os.makedirs(folder_name, exist_ok=True)
csv_file_name = 'merged_prs_2024-10-13_to_2024-10-27'
csv_file_path = os.path.join('github', csv_file_name + '.csv')
pdf_file_path = os.path.join(folder_name, 'releases_per_day.pdf')  # Output filename

release_dates = []

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
                # Parse the merged_at datetime and extract the date
                merged_at_dt = datetime.strptime(merged_at, '%Y-%m-%dT%H:%M:%SZ')
                release_date = merged_at_dt.date()  # Extract date part only
                release_dates.append(release_date)
            except ValueError as e:
                print(f"Error parsing date: {merged_at} - {e}")

# Count releases by day
if release_dates:
    # Convert the list of dates to a pandas Series
    release_series = pd.Series(release_dates)
    
    # Count occurrences of each date
    release_counter = release_series.value_counts().sort_index()
    
    # Convert counter to a DataFrame for plotting
    release_df = release_counter.reset_index()
    release_df.columns = ['Release Date', 'Prod Releases']
    
    # Ensure the 'Release Date' column is of datetime type for proper plotting
    release_df['Release Date'] = pd.to_datetime(release_df['Release Date'])
    
    # Sort the DataFrame by date
    release_df.sort_values('Release Date', inplace=True)
    
    # Generate a complete date range from the earliest to the latest release date
    min_date = release_df['Release Date'].min()
    max_date = release_df['Release Date'].max()
    
    # Generate date range excluding weekends (Monday to Friday)
    complete_date_range = pd.date_range(start=min_date, end=max_date, freq='B')  # 'B' stands for business days (Mon-Fri)
    
    # Reindex the DataFrame to include all business days in the range, filling missing dates with zero
    release_df.set_index('Release Date', inplace=True)
    release_df = release_df.reindex(complete_date_range, fill_value=0)
    release_df.reset_index(inplace=True)
    release_df.rename(columns={'index': 'Release Date'}, inplace=True)
    
    # Calculate statistics
    avg_releases = release_df['Prod Releases'].mean()
    max_releases_day = release_df.loc[release_df['Prod Releases'].idxmax(), 'Release Date']
    min_releases_day = release_df.loc[release_df['Prod Releases'].idxmin(), 'Release Date']
    max_releases = release_df['Prod Releases'].max()
    min_releases = release_df['Prod Releases'].min()
    
    # Plot daily releases as a bar chart
    with PdfPages(pdf_file_path) as pdf:
        fig, ax = plt.subplots(figsize=(14, 7))  # Increased width for better date label spacing

        # Plot the bar chart
        bars = ax.bar(release_df['Release Date'], release_df['Prod Releases'], color='#260380', alpha=0.7)

        # Add data labels for each bar
        for idx, row in release_df.iterrows():
            ax.text(
                row['Release Date'], 
                row['Prod Releases'], 
                f"{int(row['Prod Releases'])}", 
                ha='center', 
                va='bottom', 
                color='black', 
                fontsize=8,
                rotation=45  # Rotate text if overlapping
            )

        # Highlight the average number of releases with a red dashed line
        ax.axhline(avg_releases, color='red', linestyle='--', linewidth=2, label=f"Avg: {avg_releases:.2f}")
        
        # Add annotations for the max and min release days
        ax.annotate(f'Most: {max_releases_day.date()} ({max_releases} releases)',
                    xy=(max_releases_day, max_releases), 
                    xytext=(max_releases_day, max_releases + 1),
                    arrowprops=dict(facecolor='green', shrink=0.05),
                    ha='center', color='green')

        

        # Ensure all business days are shown on the x-axis
        ax.set_xticks(release_df['Release Date'])
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))  # Format the dates as 'YYYY-MM-DD'

        # Set a minor tick every day to ensure daily display
        ax.xaxis.set_major_locator(mdates.DayLocator())

        # Rotate the date labels for better readability
        plt.xticks(rotation=90, ha='center')

        # Enhance the grid for better readability
        ax.grid(True, which='both', linestyle='--', linewidth=0.5, alpha=0.7)

        # Set labels and title, including the calculated statistics
        ax.set_xlabel('Release Date')
        ax.set_ylabel('Number of Prod Releases')

        plt.tight_layout()
        ax.legend()  # Show the legend for average line
        pdf.savefig()
        plt.close()

    print(f"Releases per day bar chart saved to {pdf_file_path}")
else:
    print("No production releases found in the CSV file.")
