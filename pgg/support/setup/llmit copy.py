#!/usr/bin/env python3
import os
import subprocess
import time
import signal
import sys
import datetime

# Configuration
PROMPT_FILE = "prompt.txt"
EXCLUDED_DIRS = ["automated-translation", "search-files"]
EXCLUDED_FILES = ["full.txt", "index.html", "index.md"]
EXCLUDED_PATTERNS = ["word_frequency.txt", "word_frequency.txv"]
MAX_RETRIES = 3
TIMEOUT_SECONDS = 6 * 60  # 6 minutes
ERROR_LOG_FILE = "errors.txt"  # New: File to log errors

# Logging configuration
def log(message, level="INFO"):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{level}] {message}")
    
    # Log errors to error file
    if level == "ERROR" and message.startswith("  All attempts failed"):
        with open(ERROR_LOG_FILE, 'a', encoding='utf-8') as error_file:
            error_file.write(f"[{timestamp}] {message}\n")

class TimeoutError(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutError("Command timed out")

def run_command_with_timeout(cmd, timeout=TIMEOUT_SECONDS):
    """Run a command with a timeout."""
    # Set the timeout handler
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(timeout)
    
    process = None
    try:
        process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8')
        stdout, stderr = process.communicate()
        signal.alarm(0)  # Reset the alarm
        return process.returncode, stdout, stderr
    except TimeoutError:
        if process:
            process.kill()
        return -1, "", "Command timed out after {} seconds".format(timeout)
    except UnicodeDecodeError:
        if process:
            process.kill()
        return -2, "", "Unicode decode error occurred"
    finally:
        signal.alarm(0)  # Reset the alarm

def format_time_estimate(seconds):
    """Format seconds into a human-readable time string."""
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    if hours > 0:
        return f"{int(hours)}h {int(minutes)}m {int(seconds)}s"
    elif minutes > 0:
        return f"{int(minutes)}m {int(seconds)}s"
    else:
        return f"{int(seconds)}s"

def process_file(input_path, output_path, current_file, total_files, total_processing_time, processed_count, remaining_files):
    """Process a single file with retries."""
    dir_name = os.path.basename(os.path.dirname(input_path))
    file_name = os.path.basename(input_path)
    log(f"Processing file {current_file}/{total_files} ({(current_file/total_files*100):.1f}%): [{dir_name}] {file_name}")
    
    # Check if the output file already exists
    if os.path.exists(output_path):
        log(f"  Output file already exists, skipping: {os.path.basename(output_path)}")
        return True
    
    # Check if the file was previously marked as incomplete
    incomplete_path = output_path.replace(".txt", "-incomplete.txt")
    if os.path.exists(incomplete_path):
        log(f"  File previously marked as incomplete, skipping: {os.path.basename(input_path)}")
        return False
    
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            input_content = f.read()
    except UnicodeDecodeError:
        # Try with a different encoding if utf-8 fails
        try:
            with open(input_path, 'r', encoding='cp949') as f:  # Common Korean encoding
                input_content = f.read()
        except Exception as e:
            log(f"  Error reading file: {str(e)}", "ERROR")
            # Log failed file to errors.txt
            with open(ERROR_LOG_FILE, 'a', encoding='utf-8') as error_file:
                error_file.write(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Failed to read file: [{dir_name}] {file_name} - {str(e)}\n")
            with open(incomplete_path, 'w', encoding='utf-8') as f:
                f.write(f"Failed to read file: {str(e)}\n")
            return False
    
    # Escape quotes in paths for shell safety
    safe_input_path = input_path.replace('"', '\\"')
    safe_output_path = output_path.replace('"', '\\"')
    
    retries = 0
    start_time = time.time()
    
    log(f"  Processing: [{dir_name}] {file_name} → {os.path.basename(output_path)}")
    
    while retries < MAX_RETRIES:
        # Construct the command using double quotes around the prompt file
        cmd = f'(cat "{safe_input_path}" | llm "$(cat {PROMPT_FILE})"; echo "\\n\\n---------------------------\\n\\n"; cat "{safe_input_path}") > "{safe_output_path}"'
        
        # Run the command with timeout
        log(f"  Attempt {retries + 1}/{MAX_RETRIES}...")
        return_code, stdout, stderr = run_command_with_timeout(cmd)
        
        if return_code == 0:
            elapsed_time = time.time() - start_time
            log(f"  Successfully processed in {elapsed_time:.2f} seconds", "SUCCESS")
            
            # Calculate and display cumulative average if we have processed files
            if processed_count > 0:
                cum_avg = (total_processing_time + elapsed_time) / (processed_count + 1)
                log(f"  Current file: {elapsed_time:.2f}s, Cumulative average: {cum_avg:.2f}s")
                
                # Calculate and display estimated time remaining
                estimated_seconds = cum_avg * remaining_files
                time_estimate = format_time_estimate(estimated_seconds)
                log(f"  Estimated time remaining: {time_estimate} for {remaining_files} files")
            
            return True
        else:
            log(f"  Failed: {stderr}", "ERROR")
            retries += 1
            
            # Delete the output file if it exists but is incomplete
            if os.path.exists(output_path):
                os.remove(output_path)
            
            if retries < MAX_RETRIES:
                log(f"  Retrying in 5 seconds...")
                time.sleep(5)
    
    # If we get here, all retries failed
    log(f"  All attempts failed. Marking as incomplete for [{dir_name}] {file_name}", "ERROR")
    # Log the failed file to errors.txt
    with open(ERROR_LOG_FILE, 'a', encoding='utf-8') as error_file:
        error_file.write(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] All attempts failed for file: [{dir_name}] {file_name}\n")
    with open(incomplete_path, 'w', encoding='utf-8') as f:
        f.write(f"Processing failed after {MAX_RETRIES} attempts.\n\n")
        f.write(input_content)
    return False

def main():
    script_start_time = time.time()
    total_processing_time = 0  # Track cumulative processing time
    processed_count = 0  # Track number of successfully processed files
    log("Starting LLMit processing script")
    
    # Initialize/clear the error log file
    with open(ERROR_LOG_FILE, 'w', encoding='utf-8') as error_file:
        error_file.write(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Error log started\n")
        error_file.write("===============================================================\n")
    
    # Get the current directory
    current_dir = os.getcwd()
    parent_dir = os.path.dirname(current_dir)
    
    # Check that prompt file exists
    if not os.path.exists(PROMPT_FILE):
        log(f"Error: Prompt file '{PROMPT_FILE}' not found in the current directory.", "ERROR")
        sys.exit(1)
    
    # Get all directories in the parent directory
    dirs = [d for d in os.listdir(parent_dir) 
            if os.path.isdir(os.path.join(parent_dir, d)) 
            and d not in EXCLUDED_DIRS]
    
    log(f"Found {len(dirs)} directories to process")
    
    # First pass - count total files to process
    total_files = 0
    all_txt_files = []
    
    for dir_name in sorted(dirs):
        dir_path = os.path.join(parent_dir, dir_name)
        output_dir = os.path.join(current_dir, dir_name)
        
        # Get all text files in the directory, excluding files based on name or pattern
        for f in os.listdir(dir_path):
            # Skip if not a text file
            if not f.endswith('.txt'):
                continue
                
            # Skip if in excluded files list
            if f in EXCLUDED_FILES:
                continue
                
            # Skip if contains any excluded pattern
            if any(pattern in f for pattern in EXCLUDED_PATTERNS):
                continue
            
            input_path = os.path.join(dir_path, f)
            output_path = os.path.join(output_dir, f)
            incomplete_path = output_path.replace(".txt", "-incomplete.txt")
            
            # Check if already processed or marked incomplete
            if os.path.exists(output_path) or os.path.exists(incomplete_path):
                continue
                
            # Add to processing list
            all_txt_files.append((dir_name, f, input_path, output_path))
            total_files += 1
    
    processed_files = 0
    skipped_files = 0
    failed_files = 0
    current_file = 0
    
    log(f"Total files to process: {total_files}")
    
    # Process each directory
    for dir_name in sorted(dirs):
        dir_path = os.path.join(parent_dir, dir_name)
        output_dir = os.path.join(current_dir, dir_name)
        
        # Check if output directory already exists
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            log(f"Created output directory: {output_dir}")
        else:
            log(f"Output directory exists: {output_dir}")
        
        # Get all text files in the directory, excluding files based on name or pattern
        txt_files = []
        for f in os.listdir(dir_path):
            # Skip if not a text file
            if not f.endswith('.txt'):
                continue
                
            # Skip if in excluded files list
            if f in EXCLUDED_FILES:
                continue
                
            # Skip if contains any excluded pattern
            if any(pattern in f for pattern in EXCLUDED_PATTERNS):
                continue
                
            txt_files.append(f)
        
        dir_start_time = time.time()
        log(f"Processing directory: {dir_name} ({len(txt_files)} files)")
        
        dir_processed = 0
        dir_skipped = 0
        dir_failed = 0
        
        # Process each file
        for file_name in sorted(txt_files):
            input_path = os.path.join(dir_path, file_name)
            output_path = os.path.join(output_dir, file_name)
            
            # Check if output already exists
            if os.path.exists(output_path):
                log(f"Skipping {file_name} (already exists)")
                skipped_files += 1
                dir_skipped += 1
                continue
                
            # Check if marked incomplete
            incomplete_path = output_path.replace(".txt", "-incomplete.txt")
            if os.path.exists(incomplete_path):
                log(f"Skipping {file_name} (previously marked incomplete)")
                skipped_files += 1
                dir_skipped += 1
                continue
            
            # Process the file
            current_file += 1
            remaining_files = total_files - current_file + 1
            file_start_time = time.time()
            success = process_file(input_path, output_path, current_file, total_files, 
                                  total_processing_time, processed_count, remaining_files)
            file_elapsed_time = time.time() - file_start_time
            
            if success:
                processed_files += 1
                dir_processed += 1
                processed_count += 1
                total_processing_time += file_elapsed_time
                cum_avg_time = total_processing_time / processed_count
                log(f"  Cumulative average processing time: {cum_avg_time:.2f} seconds (total: {processed_count} files)")
                
                # Calculate and display estimated time remaining for all remaining files
                remaining_files = total_files - processed_files - skipped_files - failed_files
                if remaining_files > 0:
                    estimated_seconds = cum_avg_time * remaining_files
                    time_estimate = format_time_estimate(estimated_seconds)
                    log(f"  Overall estimated time remaining: {time_estimate} for {remaining_files} files")
            else:
                failed_files += 1
                dir_failed += 1
            
            # Short pause between files to avoid overwhelming the system
            time.sleep(2)
        
        dir_elapsed_time = time.time() - dir_start_time
        log(f"Directory {dir_name} completed in {dir_elapsed_time:.2f} seconds: {dir_processed} processed, {dir_skipped} skipped, {dir_failed} failed")
    
    total_elapsed_time = time.time() - script_start_time
    hours, remainder = divmod(total_elapsed_time, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    # Create a summary in the error log file
    with open(ERROR_LOG_FILE, 'a', encoding='utf-8') as error_file:
        error_file.write("\n===============================================================\n")
        error_file.write(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Processing completed\n")
        error_file.write(f"Total time: {int(hours)}h {int(minutes)}m {seconds:.2f}s\n")
        error_file.write(f"Files processed: {processed_files}/{total_files} ({processed_files/total_files*100:.1f}%)\n")
        error_file.write(f"Files skipped: {skipped_files}\n")
        error_file.write(f"Files failed: {failed_files}\n")
    
    log(f"Processing complete! Total time: {int(hours)}h {int(minutes)}m {seconds:.2f}s", "SUCCESS")
    log(f"Files processed: {processed_files}/{total_files} ({processed_files/total_files*100:.1f}%)")
    log(f"Files skipped: {skipped_files}")
    log(f"Files failed: {failed_files}")
    
    average_time = total_elapsed_time / (processed_files if processed_files > 0 else 1)
    log(f"Average processing time per file: {average_time:.2f} seconds")
    log(f"See {ERROR_LOG_FILE} for a list of all failed files")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log("\nScript interrupted by user. Exiting gracefully.", "WARNING")
        with open(ERROR_LOG_FILE, 'a', encoding='utf-8') as error_file:
            error_file.write(f"\n[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Script interrupted by user\n")
        sys.exit(1)
    except Exception as e:
        log(f"\nError: {str(e)}", "ERROR")
        with open(ERROR_LOG_FILE, 'a', encoding='utf-8') as error_file:
            error_file.write(f"\n[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Script error: {str(e)}\n")
        sys.exit(1)
