#!/usr/bin/env python3

# ---------------------------------------------------------------------------------
# Article Index Extractor for 동광  Magazine
# ---------------------------------------------------------------------------------
#  Works with the list of issues on this page: https://db.history.go.kr/modern/level.do?levelId=ma_014&amp;isLeaf=0
# If you have the ma_014 or whatever the publication number is, and the number of issues, you can
# use this to extract a list of all the articles and their links.
# After this script you can run getarticles-ful.sh on the output.txt
#
# This script moves across a series of issues of 동광  online and extracts data
# about the articles in each of them, including:
#  - The issue ID number
#  - A link to the full text of the original article
#  - The article title
#  - The author (if present)
#  - The article category
# 
# The script processes issues from ID 0010 through 0390 and
# outputs the data as tab-separated values to "output.txt".
#
# This will make it easier to cycle through and scrape the full text
# of these articles in subsequent processing.
# ---------------------------------------------------------------------------------

import requests
from bs4 import BeautifulSoup
import re

journalnum = "17"
issuesnum = 40
# Function to extract data from a single page
def extract_data(url,issue_number):
    try:
        # Extract issue number from URL
        match = re.search(r'parentId=ma_0{journalnum}_(\d{4})', url)
        # if match:
            # issue_number = int(match.group(1)) // 10
            # issue_number = int(match.group(1)) 
        # else:
            # issue_number = ""
        print(f"URL: {url}")
        print(f"Issue Number: {issue_number}")
        # Get the HTML content
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise an exception for HTTP errors
        
        # Parse the HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find all list items with level3 class
        items = soup.select('li.level3')
        
        results = []
        for item in items:
            # Extract title and URL
            title_element = item.select_one('div.txt a')
            if title_element:
                title = title_element.get('title', '')
                rel_url = title_element.get('href', '')
                full_url = f"https://db.history.go.kr{rel_url}"
            else:
                title = ""
                full_url = ""
            
            # Extract noDpMob values
            nodpmob_divs = item.select('div.date.noDpMob')
            
            # Format based on number of nodpmob divs found
            if len(nodpmob_divs) == 0:
                # No nodpmob divs - two empty columns
                line = f"{issue_number}\t{full_url}\t{title}\t\t"
            elif len(nodpmob_divs) == 1:
                # One nodpmob div - value in first column, second empty
                span = nodpmob_divs[0].select_one('span')
                nodpmob1 = span.text.strip() if span else ""
                line = f"{issue_number}\t{full_url}\t{title}\t\t{nodpmob1}"
            else:
                # Two or more nodpmob divs - use first two
                span1 = nodpmob_divs[0].select_one('span')
                span2 = nodpmob_divs[1].select_one('span')
                nodpmob1 = span1.text.strip() if span1 else ""
                nodpmob2 = span2.text.strip() if span2 else ""
                line = f"{issue_number}\t{full_url}\t{title}\t{nodpmob1}\t{nodpmob2}"
            
            results.append(line)
        
        return results
    
    except Exception as e:
        print(f"Error processing {url}: {e}")
        return []

# Main script
def main():
    with open("output.txt", "w", encoding="utf-8") as output_file:
        # Loop through all issues from 0010 to 0390 in increments of 10
        for i in range(10, issuesnum, 10):
            issue_id = f"{i:04d}"  # Format as 4 digits with leading zeros
            url = f"https://db.history.go.kr/modern/getChildItemLevelListAjax.do?parentId=ma_0{journalnum}_{issue_id}&level=3"
            
            print(f"Processing issue {i//10}...")
            
            # Extract data from the current URL
            results = extract_data(url,i//10)
            
            # Write results to file
            for result in results:
                output_file.write(result + "\n")
    
    print("Extraction complete. Results saved to output.txt")

if __name__ == "__main__":
    main()
