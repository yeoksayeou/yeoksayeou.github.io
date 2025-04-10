#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Article Extractor for Korean Historical Database

This script extracts article metadata and content from the Korean Historical Database
(db.history.go.kr) and saves them as text files organized by issue number.

Run this after you have run articlelist.py to get all the links for the articles.

The script:
1. Reads a tab-delimited input file containing issue numbers and URLs
2. For each line, downloads the corresponding web page
3. Extracts specific metadata (잡지명, 발행일, 기사제목, 기사형태, 필자)
4. Extracts the main article content
5. Saves the metadata and content to a text file
6. Organizes files in directories by issue number
7. Creates a full.txt file in each issue directory that concatenates all articles

The input file should have the format:
issue_number[tab]url[tab]other_fields...

Example:
1   https://db.history.go.kr/modern/level.do?levelId=ma_013_0010_0100   금쌀악   ...

The output file will be named using the last 3 digits of the levelId in the URL
(e.g., for ma_013_0010_0100, the file will be named 100.txt)
and saved in a directory named after the issue number.

Usage:
    python3 extract_articles.py [input_file]

If no input file is specified, the script defaults to "output.txt".

Requirements:
    - requests
    - beautifulsoup4
"""

import os
import sys
import requests
from bs4 import BeautifulSoup
import re
import time
import datetime
from collections import defaultdict

def get_timestamp():
    """
    Get the current timestamp in a readable format.
    
    Returns:
        str: Current timestamp in the format [YYYY-MM-DD HH:MM:SS]
    """
    now = datetime.datetime.now()
    return f"[{now.strftime('%Y-%m-%d %H:%M:%S')}]"

def extract_content(url):
    """
    Extract metadata and content from the given URL.
    
    Args:
        url (str): The URL to process
        
    Returns:
        tuple: (metadata_dict, content_text)
    """
    try:
        response = requests.get(url)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract metadata
        metadata = {}
        meta_section = soup.select_one('section.section-meta')
        if meta_section:
            items = meta_section.select('.item')
            for item in items:
                title = item.select_one('.tit')
                content = item.select_one('.cont')
                if title and content:
                    # Clean up the text
                    title_text = title.text.strip()
                    content_text = content.text.strip()
                    metadata[title_text] = content_text
        
        # Extract article content
        content_div = soup.select_one('#cont_view')
        content_text = ""
        if content_div:
            divs = content_div.find_all('div', style=re.compile("text-align:justify"))
            for div in divs:
                content_text += div.text.strip() + "\n"
        
        return metadata, content_text.strip()
    except Exception as e:
        print(f"{get_timestamp()} Error processing {url}: {e}")
        return {}, ""

def create_full_text_file(issue_number, article_files):
    """
    Create a full.txt file that concatenates all articles for an issue with two blank lines between them.
    
    Args:
        issue_number (str): The issue number
        article_files (list): List of article files in the issue directory
    """
    try:
        output_path = os.path.join(issue_number, "full.txt")
        # Sort files naturally (so 1.txt comes before 10.txt)
        sorted_files = sorted(article_files, key=lambda x: int(os.path.basename(x).split('.')[0]))
        
        with open(output_path, 'w', encoding='utf-8') as out_file:
            for i, file_path in enumerate(sorted_files):
                with open(file_path, 'r', encoding='utf-8') as in_file:
                    content = in_file.read()
                    out_file.write(content)
                    # Add two blank lines between articles (except after the last one)
                    if i < len(article_files) - 1:
                        out_file.write("\n\n----------------------------------------------\n\n")
        print(f"{get_timestamp()} Created concatenated file at {output_path}")
    except Exception as e:
        print(f"{get_timestamp()} Error creating full text file: {e}")

def process_file(input_file):
    """
    Process each line of the input file.
    
    Args:
        input_file (str): Path to the input file
    """
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        print(f"{get_timestamp()} Starting to process {len(lines)} entries from {input_file}")
        
        # Dictionary to track files by issue number
        issue_files = defaultdict(list)
        
        for i, line in enumerate(lines, 1):
            parts = line.strip().split('\t')
            if len(parts) < 2:
                continue
                
            issue_number = parts[0]
            url = parts[1]
            
            # Extract levelId from URL
            match = re.search(r'levelId=([^&]+)', url)
            if not match:
                print(f"{get_timestamp()} Could not extract levelId from URL: {url}")
                continue
                
            level_id = match.group(1)
            
            # Extract the last 3 digits for the filename
            # For example, from ma_013_0010_0100, extract 100
            last_part = level_id.split('_')[-1]
            article_number = last_part[-3:] if len(last_part) >= 3 else last_part.zfill(3)
            filename = f"{article_number}.txt"
            
            # Create directory for issue if it doesn't exist
            os.makedirs(issue_number, exist_ok=True)
            
            # Get metadata and content
            print(f"{get_timestamp()} [{i}/{len(lines)}] Downloading {url}...")
            metadata, content = extract_content(url)
            
            # Identify author field
            author = None
            for key, value in metadata.items():
                # Look for any key that might be an author field
                if '필자' in key or '저자' in key or '작가' in key:
                    author = value
                    break
            
            # If we found an author field but it's not called exactly "필자"
            # Add it with the standardized key
            if author and '필자' not in metadata:
                metadata['필자'] = author
            
            # Output article title and date to shell
            article_title = metadata.get('기사제목', 'Unknown Title')
            article_author = metadata.get('필자', 'Unknown Author')
            article_date = metadata.get('발행일', 'Unknown Date')
            print(f"{get_timestamp()} Article: {article_title} | Author: {article_author} | Date: {article_date}")
            
            # Format output - include standard fields plus any author field we found
            output = ""
            for key in ['잡지명', '발행일', '기사제목', '필자', '기사형태']:
                if key in metadata:
                    output += f"{key}\t{metadata[key]}\n"
            
            output += "\n" + content
            
            # Save to file (overwrite if exists)
            output_path = os.path.join(issue_number, filename)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(output)
            
            # Add this file to the list for this issue
            issue_files[issue_number].append(output_path)
                
            print(f"{get_timestamp()} Saved {level_id} to {output_path}")
            
            # Be nice to the server - 1 second delay between requests
            print(f"{get_timestamp()} Waiting 1 second before next request...")
            time.sleep(1)
        
        # Create full.txt for each issue
        for issue_number, file_paths in issue_files.items():
            print(f"{get_timestamp()} Creating full.txt for issue {issue_number}...")
            create_full_text_file(issue_number, file_paths)
            
    except Exception as e:
        print(f"{get_timestamp()} Error processing file: {e}")

if __name__ == "__main__":
    input_file = sys.argv[1] if len(sys.argv) > 1 else "output.txt"
    print(f"{get_timestamp()} Processing file: {input_file}")
    process_file(input_file)
    print(f"{get_timestamp()} Processing complete.")
