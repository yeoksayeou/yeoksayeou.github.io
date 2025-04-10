#!/usr/bin/env python3
"""
TTF to WOFF2 Font Converter using fonttools

This script converts all TTF files in the current directory to WOFF2 format.
It displays progress information and file size comparisons.

Prerequisites:
- Python 3.x
- fonttools (pip install fonttools)
- brotli (pip install brotli)

Usage:
- Save this script as convert_fonts.py
- Run: python convert_fonts.py
"""

import os
import sys
import glob
import time
from pathlib import Path
from fontTools.ttLib import TTFont

def convert_ttf_to_woff2(ttf_path):
    """Convert a TTF file to WOFF2 format and return stats"""
    # Get the source file size
    source_size = os.path.getsize(ttf_path)
    
    # Create the output path with .woff2 extension
    woff2_path = str(ttf_path).replace('.ttf', '.woff2')
    
    # Load the font
    print(f"Loading {ttf_path}...")
    start_time = time.time()
    font = TTFont(ttf_path)
    load_time = time.time() - start_time
    print(f"Font loaded in {load_time:.2f} seconds")
    
    # Save as WOFF2
    print(f"Converting to WOFF2...")
    start_time = time.time()
    font.flavor = "woff2"
    font.save(woff2_path)
    font.close()
    save_time = time.time() - start_time
    
    # Get the output file size
    if os.path.exists(woff2_path):
        output_size = os.path.getsize(woff2_path)
        percentage = ((source_size - output_size) / source_size) * 100
        
        return {
            "source_path": ttf_path,
            "output_path": woff2_path,
            "source_size": source_size,
            "output_size": output_size,
            "reduction_percentage": percentage,
            "conversion_time": save_time,
            "success": True
        }
    else:
        return {"source_path": ttf_path, "success": False}

def format_size(size_in_bytes):
    """Format file size in human-readable format"""
    if size_in_bytes >= 1024 * 1024:
        return f"{size_in_bytes / (1024 * 1024):.2f} MB"
    elif size_in_bytes >= 1024:
        return f"{size_in_bytes / 1024:.2f} KB"
    else:
        return f"{size_in_bytes} bytes"

def main():
    """Find and convert all TTF files in the current directory"""
    # Find all TTF files in the current directory
    current_dir = os.getcwd()
    ttf_files = glob.glob(os.path.join(current_dir, "*.ttf"))
    
    if not ttf_files:
        print("No TTF files found in the current directory.")
        return
    
    print(f"Found {len(ttf_files)} TTF files to convert:\n")
    for i, ttf_path in enumerate(ttf_files, 1):
        filename = os.path.basename(ttf_path)
        print(f"[{i}/{len(ttf_files)}] Converting {filename}")
        
        try:
            result = convert_ttf_to_woff2(ttf_path)
            
            if result["success"]:
                print(f"✓ Conversion successful!")
                print(f"  Original: {format_size(result['source_size'])}")
                print(f"  WOFF2:    {format_size(result['output_size'])}")
                print(f"  Reduced:  {result['reduction_percentage']:.2f}%")
                print(f"  Time:     {result['conversion_time']:.2f} seconds")
                print(f"  Output:   {os.path.basename(result['output_path'])}")
            else:
                print(f"✗ Conversion failed for {filename}")
        except Exception as e:
            print(f"✗ Error converting {filename}: {str(e)}")
        
        print() # Add empty line between files
    
    print("\nConversion process completed!")
    print("You can now update your CSS to use these WOFF2 files.")

if __name__ == "__main__":
    # Check for fonttools and brotli
    try:
        import fontTools
        import brotli
    except ImportError as e:
        missing = "fonttools" if "fontTools" in str(e) else "brotli"
        print(f"Required package {missing} is missing. Please install it with:")
        print(f"pip install {missing}")
        sys.exit(1)
        
    main()
