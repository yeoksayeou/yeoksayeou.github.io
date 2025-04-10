#!/usr/bin/env python3

import os
import re
import glob
import argparse

# Directories to ignore
IGNORE_DIRS = ["support", "done", "automated-translation"]

def extract_issue_number(line):
    # Extract content between "제" and "호"
    match = re.search(r'제(.*?)호', line)
    if match:
        # Get the content between 제 and 호
        issue_str = match.group(1).strip()
        
        # Replace special separators with hyphen
        issue_str = re.sub(r'[·\s]+', '-', issue_str)
        
        # Try to pad with zero if it's a simple number
        try:
            if issue_str.isdigit():
                return f"{int(issue_str):02d}"
            return issue_str
        except:
            return issue_str
    return None

def extract_date(line):
    # Extract year, month, day from Korean date format
    match = re.search(r'(\d{4})년\s+(\d{1,2})월\s+(\d{1,2})일', line)
    if match:
        year, month, day = match.groups()
        return f"{year}.{int(month):02d}.{int(day):02d}"
    return None

def process_directories(base_path, test_mode=False):
    # Get all numbered directories and sort them
    all_items = sorted(os.listdir(base_path))
    changes = []
    
    for item in all_items:
        dir_path = os.path.join(base_path, item)
        
        # Skip if not a directory or in ignore list
        if not os.path.isdir(dir_path) or item.lower() in [d.lower() for d in IGNORE_DIRS]:
            continue
            
        # Find first text file in the directory
        txt_files = glob.glob(os.path.join(dir_path, "*.txt"))
        if not txt_files:
            print(f"No text files found in {dir_path}, skipping...")
            continue
            
        # Sort files to ensure consistent behavior
        txt_files.sort()
        first_txt = txt_files[0]
        
        try:
            with open(first_txt, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                
            if len(lines) < 2:
                print(f"File {first_txt} doesn't have enough lines, skipping...")
                continue
                
            # Extract issue number and date
            issue_number = extract_issue_number(lines[0].strip())
            date = extract_date(lines[1].strip())
            
            if not issue_number or not date:
                print(f"Couldn't extract required information from {first_txt}, skipping...")
                continue
                
            # Create new directory name
            new_dir_name = f"{item}_{issue_number}_{date}"
            new_dir_path = os.path.join(base_path, new_dir_name)
            
            changes.append((dir_path, new_dir_path))
            
        except Exception as e:
            print(f"Error processing {dir_path}: {e}")
    
    # Process all changes
    if changes:
        print(f"\nFound {len(changes)} directories to rename:")
        for old_path, new_path in changes:
            print(f"  {os.path.basename(old_path)} -> {os.path.basename(new_path)}")
        
        if not test_mode:
            print("\nPerforming renames...")
            for old_path, new_path in changes:
                if os.path.exists(new_path):
                    print(f"Cannot rename {old_path} to {new_path} - target already exists")
                else:
                    print(f"Renaming {old_path} to {new_path}")
                    os.rename(old_path, new_path)
            print("Done!")
        else:
            print("\nTest mode active - no changes were made.")
    else:
        print("No directories to rename.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Rename directories based on text file contents.")
    parser.add_argument("-t", "--test", action="store_true", 
                        help="Test mode: show changes without making them")
    parser.add_argument("-d", "--directory", default=".",
                        help="Base directory to process (default: current directory)")
    
    args = parser.parse_args()
    
    print(f"Processing directories in: {os.path.abspath(args.directory)}")
    if args.test:
        print("Test mode: Changes will be displayed but not applied")
    
    process_directories(args.directory, args.test)
