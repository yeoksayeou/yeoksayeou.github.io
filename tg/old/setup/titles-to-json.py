#!/usr/bin/env python3
"""
Tab-Delimited Text to JSON Converter

This script converts a tab-delimited text file with article data into a JSON array format.

Input file format:
- Each line contains tab-separated fields
- First field: issue number (e.g., "01")
- Second field: article ID (e.g., "001")
- Third field: article title (e.g., "Company Announcement = Part 1 =")
- Fourth field (optional): article author
- Fifth field (optional): article type

Output JSON format:
- Array of objects, each with the following properties:
  - "issue": The issue number exactly as it appears in the input
  - "article-id": The article ID field
  - "article-title": The article title field
  - "author" (optional): The author field if it exists
  - "type" (optional): The type field if it exists

Usage:
  python tab_to_json.py <input_file> <output_file>

Arguments:
  <input_file>        Path to the tab-delimited input file
  <output_file>       Path where the JSON output will be saved

Example:
  python tab_to_json.py articles.txt articles.json
"""

import argparse
import json
import sys

def convert_tab_to_json(input_file, output_file):
    """
    Convert tab-delimited text file to JSON format.
    
    Args:
        input_file (str): Path to input tab-delimited file
        output_file (str): Path to output JSON file
    """
    articles = []
    
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            for line in f:
                # Skip empty lines
                if line.strip() == "":
                    continue
                
                # Split the line by tabs
                fields = line.strip().split('\t')
                
                # Ensure we have at least 3 fields
                if len(fields) < 3:
                    print(f"Warning: Skipping malformed line: {line.strip()}")
                    continue
                
                issue_num = fields[0]
                article_id = fields[1]
                article_title = fields[2]
                
                # Create the article object with the required fields
                article = {
                    "issue": issue_num,
                    "article-id": article_id,
                    "article-title": article_title
                }
                
                # Add author field if it exists (4th column)
                if len(fields) > 3 and fields[3].strip():
                    article["author"] = fields[3]
                
                # Add type field if it exists (5th column)
                if len(fields) > 4 and fields[4].strip():
                    article["type"] = fields[4]
                
                articles.append(article)
        
        # Write the JSON output
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(articles, f, ensure_ascii=False, indent=2)
        
        print(f"Successfully converted {len(articles)} articles to JSON format.")
        print(f"Output saved to {output_file}")
        
    except FileNotFoundError:
        print(f"Error: Input file '{input_file}' not found.")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)

def main():
    # Set up command line argument parsing
    parser = argparse.ArgumentParser(description='Convert tab-delimited text file to JSON format.')
    parser.add_argument('input_file', help='Path to the input tab-delimited file')
    parser.add_argument('output_file', help='Path where the JSON output will be saved')
    
    # Parse arguments
    args = parser.parse_args()
    
    # Convert the file
    convert_tab_to_json(args.input_file, args.output_file)

if __name__ == "__main__":
    main()
