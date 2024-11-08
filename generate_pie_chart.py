import os
import csv
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

# Define the folder and file paths
folder_name = os.path.join('reports', 'pie_chart')
os.makedirs(folder_name, exist_ok=True)
csv_file_name = 'merged_prs_2024-10-28_to_2024-11-01'
csv_file_path = os.path.join('github', csv_file_name + '.csv')
pdf_file_path = os.path.join(folder_name, 'pie_chart_fast_slow.pdf')

release_data = {'fast': 0, 'slow': 0}

# Read the CSV file and gather data
with open(csv_file_path, mode='r', newline='', encoding='utf-8') as csv_file:
    reader = csv.DictReader(csv_file)
    for row in reader:
        branch = row['Branch']
        release_type = row['Release Type']
        
        if branch == 'master':
            branch = 'prod'
        
        if branch == 'prod':
            if release_type == 'fast':
                release_data['fast'] += 1
            else:
                release_data['slow'] += 1

# Calculate percentages
total_releases = release_data['fast'] + release_data['slow']
fast_percentage = (release_data['fast'] / total_releases) * 100
slow_percentage = (release_data['slow'] / total_releases) * 100

# Plot pie chart
with PdfPages(pdf_file_path) as pdf:
    fig, ax = plt.subplots(figsize=(5, 5))  # Adjust the figure size to fit better in PDF

    labels = ['Fast Releases', 'Slow Releases']
    sizes = [release_data['fast'], release_data['slow']]
    colors = ['#260380', '#fc5f05']  # Updated colors to orange and black
    
    wedges, texts, autotexts = ax.pie(sizes, startangle=90, colors=colors, 
                                      wedgeprops=dict(width=0.3), 
                                      autopct=lambda pct: '',  # No percentages on the chart
                                      pctdistance=0.85)
    
    # Add the exact numbers in white inside each pie slice
    for i, auto_text in enumerate(autotexts):
        auto_text.set_text(f"{sizes[i]}")  # Set the number of releases
        auto_text.set_color("white")
        auto_text.set_fontsize(12)
        auto_text.set_weight('bold')

    # Add a legend with percentages
    ax.legend(wedges, [f"Fast Releases ({fast_percentage:.1f}%)", f"Slow Releases ({slow_percentage:.1f}%)"], 
              title="Release Types", loc="center left", bbox_to_anchor=(1, 0, 0.5, 1), fontsize=10)

    # Add title
    ax.set_title('Fast vs Slow Prod Releases')
    
    # Save the plot to the PDF
    pdf.savefig(bbox_inches='tight')
    plt.close()

print(f"Pie chart saved to {pdf_file_path}")
