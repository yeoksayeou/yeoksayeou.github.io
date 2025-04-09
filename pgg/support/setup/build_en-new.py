#!/usr/bin/env python3
import os
import json
import re

# VERSION: 2.6

# changed: now saves window.ARTICLES instead of const ARTICLES 
# changed: now handles metadata extraction more flexibly
# changed: includes all content after metadata, including content after divider


"""
Overview of build.py
---------------------

Purpose:
This script scans a structured set of directories containing article text files and PDF files for different issues of a publication. It extracts metadata and content from these text files and compiles them into two JavaScript files: `data.js` for articles and `pdfs.js` for PDF references. It ignores specified directories and handles various naming conventions for issues.

Walkthrough:

1. **Initial Setup:**
   - Imports necessary modules: `os`, `json`, `re`.
   - Defines output file paths:
     - `data.js` will contain metadata and content for articles.
     - `pdfs.js` will store paths to PDF files.
   - Sets `root_dir` as the base folder containing all issue folders.
   - Specifies directories to ignore during processing.

2. **Data Structures:**
   - `articles`: A list to collect dictionaries of parsed article data.
   - `pdfs`: A list to collect dictionaries pointing to PDF file locations.

3. **Metadata Extraction:**
   - Implements a robust function to extract metadata and content that properly handles:
     - The first metadata block in the file
     - All content after the first metadata block (ignoring any subsequent metadata blocks)
     - Metadata fields in both Korean and English formats

4. **Directory Discovery:**
   - Walks through all subdirectories under `root_dir`.
   - Skips:
     - The root directory itself.
     - Any subdirectories listed in `ignore_dirs`.
     - Any directories that do not contain `.txt` article files.
   - Adds eligible directories to `all_dirs`.

5. **Sorting:**
   - Sorts `all_dirs` to ensure consistent processing order.

6. **Directory Processing Loop:**
   - For each eligible directory:
     - Constructs full path.
     - Attempts to extract issue number and date using regex patterns:
       - Matches formats like: "123호 2023.09", "신간 5호 2024", "복간 7호 2023.12".
     - Defaults to the directory name if no match is found.
     - Processes text files and PDF files.

7. **Final Output:**
   - Writes collected `articles` and `pdfs` to `data.js` and `pdfs.js` as JSON-encoded JavaScript variables.

"""

output_file = "data_en.js"
pdfs_output_file = "pdfs.js"  # New output file for PDFs
root_dir = "."  # base folder containing all issue folders

# Directories to ignore
ignore_dirs = ["search-files", "other", "support", "automated-translation"]

# Article metadata structure
# { 'path': str, 'issue': str, 'issue_number': str, 'date': str, 'title': str, 'author': str, 'type': str, 'content': str }
articles = []

# PDF information structure
# { 'issue': str, 'path': str }
pdfs = []

def extract_metadata_and_content(text):
    """
    Extracts metadata and content from an article text.
    Handles inconsistent metadata formats and ensures the content is extracted correctly.
    Focuses only on the first 10 lines for metadata, and ensures content is at least 2/3 of the file.
    
    Args:
        text (str): The full text of the article
        
    Returns:
        dict: Metadata fields and content
    """
    # Initialize metadata variables
    magazine = ""
    date = ""
    title = ""
    author = ""
    article_type = ""
    
    # Get the first 10 lines for metadata examination
    lines = text.split('\n')
    metadata_lines = lines[:10] if len(lines) >= 10 else lines
    metadata_text = '\n'.join(metadata_lines)
    
    # Look for metadata fields in the first 10 lines
    # Magazine name
    magazine_match = re.search(r'(?:잡지명|Magazine Title)?[:\t]?\s*(.*건곤.*|別乾坤.*?)\s*$', metadata_text, re.MULTILINE)
    if magazine_match:
        magazine = magazine_match.group(1).strip()
    
    # Publication date
    date_match = re.search(r'(?:발행일|Publication Date)?[:\t]?\s*(\d{4}[년\.]\s*\d{1,2}[월\.]\s*\d{1,2}[일\.]?|.*\d{4}.*)\s*$', metadata_text, re.MULTILINE)
    if date_match:
        date = date_match.group(1).strip()
    
    # Article title
    title_match = re.search(r'(?:기사제목|Article Title)?[:\t]?\s*(.*?)\s*(?:\(.*?\))?\s*$', metadata_text, re.MULTILINE)
    if title_match and len(title_match.group(1).strip()) > 0:
        title = title_match.group(1).strip()
    
    # Author
    author_match = re.search(r'(?:필자|Author)[:\t]?\s*(.*?)\s*(?:\(.*?\))?\s*$', metadata_text, re.MULTILINE)
    if author_match:
        author = author_match.group(1).strip()
    
    # Article type
    type_match = re.search(r'(?:기사형태|Article Type)[:\t]?\s*(.*?)\s*(?:\(.*?\))?\s*$', metadata_text, re.MULTILINE)
    if type_match:
        article_type = type_match.group(1).strip()
    
    # Find the last line with metadata
    last_metadata_line = -1
    for i, line in enumerate(metadata_lines):
        if any(field in line for field in ['잡지명', 'Magazine Title', '발행일', 'Publication Date', 
                                          '기사제목', 'Article Title', '필자', 'Author', 
                                          '기사형태', 'Article Type']):
            last_metadata_line = i
    
    # Set content start position to the line after the last metadata line
    content_start = 0
    if last_metadata_line >= 0:
        # Calculate position of the end of the last metadata line
        for i in range(last_metadata_line + 1):
            content_start += len(lines[i]) + 1  # +1 for newline
        
        # If there's a blank line right after metadata, skip it
        if last_metadata_line + 1 < len(lines) and not lines[last_metadata_line + 1].strip():
            content_start += len(lines[last_metadata_line + 1]) + 1
    
    # If no metadata was found or content would be too small, reset to beginning
    total_lines = len(lines)
    content_lines = total_lines - (last_metadata_line + 1)
    
    # If content would be less than 2/3 of the file, use the entire file as content
    if content_lines < (total_lines * 2/3):
        content_start = 0
    
    # Include all content after metadata
    content = text[content_start:].strip()
    
    # Return the extracted metadata and content
    return {
        'magazine': magazine,
        'date': date,
        'title': title,
        'author': author,
        'type': article_type,
        'content': content
    }

# Get all subdirectories (excluding ignored ones)
all_dirs = []
for dirpath, dirnames, filenames in os.walk(root_dir):
    # Skip the root directory (current directory)
    if dirpath == root_dir:
        continue
    
    # Skip ignored directories
    rel_dir = os.path.relpath(dirpath, root_dir)
    if any(ignore_dir in rel_dir.split(os.sep) for ignore_dir in ignore_dirs):
        continue
    
    # Skip non-issue directories
    if not any(filename.endswith('.txt') for filename in filenames):
        continue
    
    all_dirs.append(rel_dir)

# Sort all directories
all_dirs.sort()

# Process each directory in sorted order
for rel_dir in all_dirs:
    dirpath = os.path.join(root_dir, rel_dir)
    
    # Get the issue name from directory name
    issue_match = re.search(r'(\d+)호\s+(\d+\.\d+)', rel_dir)
    issue_new_match = re.search(r'신간\s+(\d+)호\s+(\d+)', rel_dir)
    issue_restored_match = re.search(r'복간\s+(\d+)호\s+(\d+\.\d+)', rel_dir)
    
    issue_name = rel_dir
    issue_number = ""
    
    if issue_match:
        issue_number = issue_match.group(1)
    elif issue_new_match:
        issue_number = f"신간 {issue_new_match.group(1)}"
    elif issue_restored_match:
        issue_number = f"복간 {issue_restored_match.group(1)}"
    
    # Get all files in the directory
    filenames = os.listdir(dirpath)
    
    # Check for PDF files and save the info for the first one found (sorted)
    pdf_files = [f for f in filenames if f.lower().endswith('.pdf')]
    if pdf_files:
        pdf_files.sort()  # Sort the PDF files
        pdf_path = os.path.join(rel_dir, pdf_files[0])
        pdfs.append({"issue": issue_name, "path": pdf_path})
        print(f"Adding PDF: {pdf_path}")
    else:
        # If no PDF found, store an empty path
        pdfs.append({"issue": issue_name, "path": ""})
        print(f"No PDF found for issue: {issue_name}")
    
    # Get all text files and sort them
    txt_files = [f for f in filenames if f.endswith('.txt') and f not in ['full.txt', 'index.md', 'word_frequency.tsv', 'word_frequency.txt']]
    txt_files.sort()
    
    # Process each text file in sorted order
    for filename in txt_files:
        try:
            file_path = os.path.join(dirpath, filename)
            with open(file_path, encoding="utf-8") as f:
                text = f.read()
                
                # Check if this is an incomplete file
                is_incomplete = '-incomplete' in filename
                
                article_path = os.path.join(rel_dir, filename)
                
                # Initialize article with basic information
                article = {
                    'path': article_path,
                    'issue': issue_name,
                    'issue_number': issue_number,
                    'magazine': '',
                    'date': '',
                    'title': f'Article {filename}',  # Default title based on filename
                    'author': '',
                    'type': '',
                    'content': text,  # Default content is the entire file
                }
                
                # Extract metadata and content using the robust function
                metadata_info = extract_metadata_and_content(text)
                if metadata_info:
                    article.update(metadata_info)
                
                # Handle incomplete translation files
                if is_incomplete:
                    article['content'] = "Translation failed. Often because the file was too long for the output context limits.\n\n" + article['content']
                
                articles.append(article)
                print(f"Adding article: {article_path}")
                
        except Exception as e:
            print(f"Error reading {file_path}: {e}")

# Write to data.js
with open(output_file, "w", encoding="utf-8") as out:
    out.write("window.ARTICLES = ")
    json.dump(articles, out, indent=2, ensure_ascii=False)
    out.write(";")

# Write to pdfs.js
with open(pdfs_output_file, "w", encoding="utf-8") as out:
    out.write("window.PDFS = ")
    json.dump(pdfs, out, indent=2, ensure_ascii=False)
    out.write(";")

print(f"Successfully processed {len(articles)} articles into {output_file}")
print(f"Successfully processed {len(pdfs)} issue PDF references into {pdfs_output_file}")
