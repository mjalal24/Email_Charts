import requests
import json
from datetime import datetime, timedelta
import os
import csv
import urllib3
import time
import sys

# Replace these with your values or use environment variables for security
GITHUB_TOKEN = "YOUR GITHUB TOKEN"
REPO_OWNER = ""
REPO_NAME = ""

# GitHub A2024 URL for pull requests
BASE_URL = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/pulls"

# Suppress InsecureRequestWarning
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Function to handle pagination and retrieve all PRs with loading message
def get_all_prs(branch_name):
    all_prs = []
    url = BASE_URL
    params = {
        "state": "closed",
        "base": branch_name,
        "per_page": 100  # Get up to 100 PRs per page
    }
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    loading_message = f"Fetching data from {branch_name}"
    animation = "|/-\\"
    idx = 0

    while url:
        # Display the loading message with animation
        sys.stdout.write(f"\r{loading_message} {animation[idx % len(animation)]}")
        sys.stdout.flush()
        idx += 1
        time.sleep(0.1)  # Small delay for the loading animation

        response = requests.get(url, headers=headers, params=params, verify=False)
        if response.status_code == 200:
            all_prs.extend(response.json())
            # Check if there is a 'next' page in the response headers
            if 'Link' in response.headers:
                links = response.headers['Link'].split(',')
                next_url = None
                for link in links:
                    if 'rel="next"' in link:
                        # Extract URL without angle brackets
                        next_url = link.split(';')[0].strip().strip('<>')
                        break
                if next_url:
                    url = next_url  # Update URL to next page
                    params = {}  # Clear params for subsequent pages
                else:
                    url = None
            else:
                url = None
        else:
            print(f"\nFailed to fetch PRs: {response.status_code} - {response.text}")
            return []
    
    # Once fetching is done, clear the loading message
    sys.stdout.write(f"\rFetching data from {branch_name}... Done!\n")
    sys.stdout.flush()

    return all_prs

# Function to extract team name and release type based on branch
def extract_team_name_and_release_type(pr_title, branch_name):
    if branch_name == "master":
        # Extraction logic for master branch
        try:
            team_and_code = pr_title.split('_', 2)[1]  # Extract the second part (team name and task ID)
            team_name = team_and_code.split('_')[0]  # Extract the team name
        except IndexError:
            team_name = 'Unknown'
        
        release_type = 'fast' if 'release/fast/' in pr_title else 'slow'
    elif branch_name == "develop_uat":
        # Extraction logic for develop_uat branch
        try:
            team_name = pr_title.split('Release/rc ')[1].split(' ')[0]  # Extract the word after 'Release/rc'
        except IndexError:
            team_name = 'Unknown'
        
        release_type = 'slow'  # All develop_uat releases are slow
    
    return team_name, release_type

# Function to filter PRs based on a custom date range
def filter_prs_by_date_range(prs, start_date, end_date):
    filtered_prs = []
    start_date = datetime.strptime(start_date, '%Y-%m-%d')
    end_date = datetime.strptime(end_date, '%Y-%m-%d').replace(hour=23, minute=59, second=59)

    for pr in prs:
        if pr['merged_at'] is not None:
            merged_at = datetime.strptime(pr['merged_at'], '%Y-%m-%dT%H:%M:%SZ')
            if start_date <= merged_at <= end_date:
                filtered_prs.append(pr)
    return filtered_prs

# Allow user to input date range for filtering
start_date = input("Enter the start date (YYYY-MM-DD): ")
end_date = input("Enter the end date (YYYY-MM-DD): ")

# Fetch all PRs from both master and develop_uat branches
master_pr_data = get_all_prs("master")
uat_pr_data = get_all_prs("develop_uat")

# Filter PRs based on the input date range
merged_prs_master = filter_prs_by_date_range(master_pr_data, start_date, end_date)
merged_prs_uat = filter_prs_by_date_range(uat_pr_data, start_date, end_date)

# Output the filtered PRs count
print(f"Total merged PRs between {start_date} and {end_date} from master: {len(merged_prs_master)}")
print(f"Total merged PRs between {start_date} and {end_date} from develop_uat: {len(merged_prs_uat)}")

# Combine the PRs from both branches
all_merged_prs = merged_prs_master + merged_prs_uat

# Create 'github' folder if it doesn't exist
folder_name = 'github'
if not os.path.exists(folder_name):
    os.makedirs(folder_name)
    print(f"Folder '{folder_name}' created.")
else:
    print(f"Folder '{folder_name}' already exists.")

# Write filtered PR data to a CSV file and print PR numbers on screen
csv_file_path = os.path.join(folder_name, f'merged_prs_{start_date}_to_{end_date}.csv')

with open(csv_file_path, mode='w', newline='', encoding='utf-8') as csv_file:
    fieldnames = ['PR Number', 'Title', 'Merged At', 'Team Name', 'Release Type', 'Branch']
    writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
    writer.writeheader()

    for pr in all_merged_prs:
        branch_name = "master" if pr in merged_prs_master else "develop_uat"
        team_name, release_type = extract_team_name_and_release_type(pr['title'], branch_name)
        # Skip writing rows where the team name is 'Unknown'
        if team_name != 'Unknown':
            writer.writerow({
                'PR Number': pr['number'],
                'Title': pr['title'],
                'Merged At': pr['merged_at'],
                'Team Name': team_name,
                'Release Type': release_type,
                'Branch': branch_name
            })

print(f"Filtered PR details saved to {csv_file_path}")
