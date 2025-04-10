#!/bin/bash

VERSION="0.3"
TEST_MODE=false
DOWNLOAD_TIMEOUT=200  # 5 minutes in seconds
MAX_CONSECUTIVE_FAILURES=3
MAX_CONCURRENT_DOWNLOADS=3
SLEEP_BETWEEN_DOWNLOADS=2  # Wait 2 seconds between starting new downloads
SERVER_OUTAGE_WAIT=120     # Wait 2 minutes after suspected server outage

# Function to display help information
show_help() {
  echo "Usage: $0 [OPTIONS] <filename>"
  echo
  echo "Downloads sequentially numbered files from URLs listed in the input file."
  echo
  echo "Options:"
  echo "  -t, --test     Test mode: process the file without downloading anything"
  echo "  -h, --help     Display this help message and exit"
  echo "  -v, --version  Display version information and exit"
  echo
  echo "Input file format:"
  echo "  Each line should contain three tab-separated fields:"
  echo "  1. Directory name for saving files"
  echo "  2. Base URL ending with '1.jpg'"
  echo "  3. Maximum number of files to download"
  echo
  echo "Features:"
  echo "  - Downloads up to $MAX_CONCURRENT_DOWNLOADS files concurrently"
  echo "  - Skips existing files larger than 10KB"
  echo "  - Removes and redownloads files smaller than 10KB"
  echo "  - Times out downloads after 5 minutes"
  echo "  - Stops after 3 consecutive failures"
  echo "  - Handles server outages with automatic retry"
  echo
  echo "Example:"
  echo "  $0 list.txt"
  echo "  $0 --test list.txt"
}

# Function to display version information
show_version() {
  echo "Download Script v$VERSION"
}

# Function to check file size in KB
# Returns 1 if file exists and is >= 10KB, 0 otherwise
check_file_size() {
  local file="$1"
  local min_size=10  # 10KB
  
  if [ -f "$file" ]; then
    # Get file size in KB (rounded down)
    local size=$(du -k "$file" | cut -f1)
    if [ "$size" -ge "$min_size" ]; then
      return 1  # File exists and is large enough
    else
      return 0  # File exists but is too small
    fi
  else
    return 0  # File does not exist
  fi
}

# Function to safely increment a counter in a file with locking
increment_counter() {
  local file="$1"
  local lockfile="${file}.lock"
  
  # Create lock file (atomic operation in most file systems)
  if ! (set -o noclobber; echo "$$" > "$lockfile") 2>/dev/null; then
    # If we can't get the lock, wait briefly and try again
    sleep 0.5
    increment_counter "$file"
    return
  fi
  
  # Ensure lock file is removed when we exit this function
  trap 'rm -f "$lockfile"' EXIT
  
  # Read, increment, and write back
  local count=$(cat "$file" 2>/dev/null || echo "0")
  echo $((count + 1)) > "$file"
  
  # Remove lock file
  rm -f "$lockfile"
}

# Function to safely reset a counter in a file with locking
reset_counter() {
  local file="$1"
  local lockfile="${file}.lock"
  
  # Create lock file
  if ! (set -o noclobber; echo "$$" > "$lockfile") 2>/dev/null; then
    # If we can't get the lock, wait briefly and try again
    sleep 0.5
    reset_counter "$file"
    return
  fi
  
  # Ensure lock file is removed when we exit this function
  trap 'rm -f "$lockfile"' EXIT
  
  # Reset counter
  echo "0" > "$file"
  
  # Remove lock file
  rm -f "$lockfile"
}

# Function to safely read a counter from a file with locking
read_counter() {
  local file="$1"
  local lockfile="${file}.lock"
  
  # Create lock file
  if ! (set -o noclobber; echo "$$" > "$lockfile") 2>/dev/null; then
    # If we can't get the lock, wait briefly and try again
    sleep 0.5
    read_counter "$file"
    return
  fi
  
  # Ensure lock file is removed when we exit this function
  trap 'rm -f "$lockfile"' EXIT
  
  # Read counter
  local count=$(cat "$file" 2>/dev/null || echo "0")
  
  # Remove lock file
  rm -f "$lockfile"
  
  echo "$count"
}

# Function to safely update the global outage status
update_outage_status() {
  local file="$1"
  local status="$2"
  local lockfile="${file}.lock"
  
  # Create lock file
  if ! (set -o noclobber; echo "$$" > "$lockfile") 2>/dev/null; then
    # If we can't get the lock, wait briefly and try again
    sleep 0.5
    update_outage_status "$file" "$status"
    return
  fi
  
  # Ensure lock file is removed when we exit this function
  trap 'rm -f "$lockfile"' EXIT
  
  # Update status
  echo "$status" > "$file"
  
  # Remove lock file
  rm -f "$lockfile"
}

# Function to read the outage status
check_outage_status() {
  local file="$1"
  local lockfile="${file}.lock"
  
  # Create lock file
  if ! (set -o noclobber; echo "$$" > "$lockfile") 2>/dev/null; then
    # If we can't get the lock, wait briefly and try again
    sleep 0.5
    check_outage_status "$file"
    return
  fi
  
  # Ensure lock file is removed when we exit this function
  trap 'rm -f "$lockfile"' EXIT
  
  # Read status
  local status=$(cat "$file" 2>/dev/null || echo "0")
  
  # Remove lock file
  rm -f "$lockfile"
  
  echo "$status"
}

# Function to download a single file with retries
# Returns 0 on success, 1 on failure
download_file() {
  local url="$1"
  local output_file="$2"
  local item_number="$3"
  local max_items="$4"
  local log_prefix="$5"
  local failure_tracker="$6"
  local outage_tracker="$7"
  local job_id="$8"
  
  local download_success=false

  # Create a temp file to log to (prevents output interleaving)
  local temp_log_file="$(mktemp)"
  
  # Create a status file to track this job's status
  local job_status_file="$tmp_dir/job_${job_id}_status"
  echo "running" > "$job_status_file"
  
  echo "${log_prefix}Downloading: $url -> $output_file" >> "$temp_log_file"
  
  for attempt in {1..3}; do
    # Check if there's a server outage in progress
    local outage_status=$(check_outage_status "$outage_tracker")
    if [ "$outage_status" = "1" ]; then
      echo "${log_prefix}⚠️ Server outage detected, waiting for $SERVER_OUTAGE_WAIT seconds before retry..." >> "$temp_log_file"
      sleep $SERVER_OUTAGE_WAIT
      
      # Now check again if we should continue
      outage_status=$(check_outage_status "$outage_tracker")
      if [ "$outage_status" = "1" ]; then
        # Still in outage mode, wait more
        echo "${log_prefix}⚠️ Server still appears to be down, continuing to wait..." >> "$temp_log_file"
        sleep $SERVER_OUTAGE_WAIT
      else
        echo "${log_prefix}✅ Server appears to be back online, resuming download" >> "$temp_log_file"
      fi
    fi
    
    if [ $attempt -gt 1 ]; then
      echo "${log_prefix}🔄 Retry attempt $attempt for: $output_file" >> "$temp_log_file"
    fi
    
    # Download with timeout
    curl -s -m $DOWNLOAD_TIMEOUT "$url" -o "$output_file" 2>> "$temp_log_file"
    curl_status=$?
    
    # Check if download was successful
    if [ $curl_status -eq 0 ] && [ -f "$output_file" ]; then
      # Verify file size
      check_file_size "$output_file"
      file_status=$?
      
      if [ $file_status -eq 1 ]; then
        echo "${log_prefix}✅ Successfully downloaded image $item_number of $max_items $(date +"%H:%M:%S")" >> "$temp_log_file"
        # Reset failure counter on success
        reset_counter "$failure_tracker"
        # Reset outage status on success
        update_outage_status "$outage_tracker" "0"
        download_success=true
        break
      else
        echo "${log_prefix}⚠️ Downloaded file is too small (< 10KB), may be corrupt" >> "$temp_log_file"
        rm -f "$output_file"
        
        # Check multiple failures - could indicate server outage
        local current_failures=$(read_counter "$failure_tracker")
        if [ $current_failures -ge 2 ]; then
          echo "${log_prefix}🔴 Multiple failures detected - possible server outage" >> "$temp_log_file"
          update_outage_status "$outage_tracker" "1"
          echo "${log_prefix}Waiting for $SERVER_OUTAGE_WAIT seconds due to possible server outage..." >> "$temp_log_file"
          sleep $SERVER_OUTAGE_WAIT
        else
          echo "${log_prefix}Waiting for 2 minutes..." >> "$temp_log_file"
          sleep 2m
        fi
      fi
    elif [ $curl_status -eq 28 ]; then
      echo "${log_prefix}⏱️ Download timed out after $DOWNLOAD_TIMEOUT seconds" >> "$temp_log_file"
      rm -f "$output_file"
      
      # A timeout is a strong indicator of server issues
      echo "${log_prefix}🔴 Download timeout detected - possible server outage" >> "$temp_log_file"
      update_outage_status "$outage_tracker" "1"
      echo "${log_prefix}Waiting for $SERVER_OUTAGE_WAIT seconds due to possible server outage..." >> "$temp_log_file"
      sleep $SERVER_OUTAGE_WAIT
    else
      echo "${log_prefix}❌ Download failed with curl error code: $curl_status" >> "$temp_log_file"
      rm -f "$output_file"
      
      # Check if this is a connection error, which might indicate server issues
      if [ $curl_status -eq 7 ] || [ $curl_status -eq 6 ]; then
        echo "${log_prefix}🔴 Connection failure detected - possible server outage" >> "$temp_log_file"
        update_outage_status "$outage_tracker" "1"
        echo "${log_prefix}Waiting for $SERVER_OUTAGE_WAIT seconds due to possible server outage..." >> "$temp_log_file"
        sleep $SERVER_OUTAGE_WAIT
      else
        echo "${log_prefix}Waiting for 2 minutes..." >> "$temp_log_file"
        sleep 2m
      fi
    fi
  done
  
  # Output the logs in one go to prevent interleaving
  cat "$temp_log_file"
  rm -f "$temp_log_file"
  
  if [ "$download_success" = true ]; then
    echo "success" > "$job_status_file"
    return 0  # Success
  else
    echo "${log_prefix}❌ Failed to download image $item_number of $max_items after 3 attempts"
    # Increment failure counter
    increment_counter "$failure_tracker"
    echo "failed" > "$job_status_file"
    return 1  # Failure
  fi
}

# Parse command line arguments
INPUT_FILE=""
while [[ $# -gt 0 ]]; do
  case $1 in
    -t|--test)
      TEST_MODE=true
      shift
      ;;
    -h|--help)
      show_help
      exit 0
      ;;
    -v|--version)
      show_version
      exit 0
      ;;
    -*)
      echo "Error: Unknown option $1"
      echo "Try '$0 --help' for more information."
      exit 1
      ;;
    *)
      if [ -z "$INPUT_FILE" ]; then
        INPUT_FILE="$1"
      else
        echo "Error: Too many arguments"
        echo "Try '$0 --help' for more information."
        exit 1
      fi
      shift
      ;;
  esac
done

# Check if an input file was provided
if [ -z "$INPUT_FILE" ]; then
  echo "Error: No input file specified"
  echo "Try '$0 --help' for more information."
  exit 1
fi

# Check if gsed is installed
if ! command -v gsed &> /dev/null; then
  echo "Error: gsed (GNU sed) is not installed. Install it with: brew install gnu-sed"
  exit 1
fi

# Check if the file exists
if [ ! -f "$INPUT_FILE" ]; then
  echo "Error: File '$INPUT_FILE' not found"
  exit 1
fi

# Create a temporary directory for tracking job status
tmp_dir=$(mktemp -d)
trap 'rm -rf "$tmp_dir"; pkill -P $$ 2>/dev/null' EXIT INT TERM

echo "======================================"
if [ "$TEST_MODE" = true ]; then
  echo "RUNNING IN TEST MODE - No files will be downloaded"
  echo "Concurrent downloads: $MAX_CONCURRENT_DOWNLOADS (simulated)"
else
  echo "Concurrent downloads: $MAX_CONCURRENT_DOWNLOADS"
  echo "Server outage detection: Enabled (wait time: $SERVER_OUTAGE_WAIT seconds)"
fi
echo "Starting processing of file: $INPUT_FILE"
echo "======================================"

# Create a parent directory for all downloads if it doesn't exist
parent_dir="downloads"
if [ "$TEST_MODE" = false ]; then
  mkdir -p "$parent_dir"
  echo "Created parent directory: $parent_dir"
else
  echo "[TEST] Would create parent directory: $parent_dir"
fi

# Process each line in the input file
while IFS=$'\t' read -r dir_name base_url max_images || [ -n "$dir_name" ]; do
  # Skip empty lines
  if [ -z "$dir_name" ]; then
    continue
  fi

  echo "======================================"
  echo "Processing entry: $dir_name"
  echo "Base URL: $base_url"
  echo "Number of images: $max_images"
  start_time=$(date +%s)
  
  # Create directory for this entry
  folder_path="$parent_dir/$dir_name"
  if [ "$TEST_MODE" = false ]; then
    mkdir -p "$folder_path"
    echo "Created directory: $folder_path"
  else
    echo "[TEST] Would create directory: $folder_path"
  fi

  # Determine zero-padding width based on max number
  padding_width=${#max_images}
  echo "Using padding width: $padding_width digits"

  # Replace 1.jpg in base URL with [1-MAX].jpg for display purposes
  display_url=$(echo "$base_url" | gsed "s/1.jpg/[1-$max_images].jpg/")
  echo "Full URL pattern: $display_url"
  
  if [ "$TEST_MODE" = false ]; then
    # Create a status file to track consecutive failures
    failure_tracker="$tmp_dir/failures_$dir_name"
    echo "0" > "$failure_tracker"
    
    # Create a status file to track server outages
    outage_tracker="$tmp_dir/outage_$dir_name"
    echo "0" > "$outage_tracker"
    
    # Track jobs using files instead of associative arrays
    active_jobs=0
    next_job_id=1
    
    # Track overall progress
    total_processed=0
    total_to_process=$max_images
    last_progress_update=0
    progress_update_interval=10  # Update progress every 10%
    
    # Loop through all images
    for i in $(seq 1 "$max_images"); do
      # Progress tracking
      percent_done=$((total_processed * 100 / total_to_process))
      if (( percent_done / progress_update_interval > last_progress_update )); then
        last_progress_update=$((percent_done / progress_update_interval))
        echo "Progress: $percent_done% complete ($total_processed/$total_to_process)"
      fi
      
      # Create padded filename
      padded_filename=$(printf "%0${padding_width}d.jpg" "$i")
      
      # Create actual URL by replacing "1.jpg" with current number
      actual_url=$(echo "$base_url" | gsed "s/1.jpg/$i.jpg/")
      
      # Output file path
      output_file="$folder_path/$padded_filename"
      
      # Check if file already exists and is large enough
      check_file_size "$output_file"
      file_status=$?
      
      if [ $file_status -eq 1 ]; then
        echo "⏭️  Skipping: $output_file already exists and is larger than 10KB"
        # Reset failure counter on skip
        reset_counter "$failure_tracker"
        total_processed=$((total_processed + 1))
        continue
      elif [ -f "$output_file" ]; then
        echo "🗑️  Removing small/corrupt file: $output_file"
        rm -f "$output_file"
      fi
      
      # Check if we're in an outage state - if so, wait before starting new downloads
      outage_status=$(check_outage_status "$outage_tracker")
      if [ "$outage_status" = "1" ]; then
        echo "⚠️ Server outage detected, waiting for $SERVER_OUTAGE_WAIT seconds before continuing..."
        sleep $SERVER_OUTAGE_WAIT
        # Reset outage status and try again
        update_outage_status "$outage_tracker" "0"
        echo "Resuming after wait period"
      fi
      
      # Check MAX_CONSECUTIVE_FAILURES threshold before starting new download
      failure_count=$(read_counter "$failure_tracker")
      if [ $failure_count -ge $MAX_CONSECUTIVE_FAILURES ]; then
        echo "⛔ ERROR: $MAX_CONSECUTIVE_FAILURES consecutive download failures detected"
        echo "⛔ Stopping script execution to prevent further errors"
        # Clean up
        pkill -P $$ 2>/dev/null
        exit 2
      fi
      
      # Wait if we've reached the maximum number of concurrent downloads
      while [ $active_jobs -ge $MAX_CONCURRENT_DOWNLOADS ]; do
        # Check for completed jobs - loop through possible job IDs
        for job_id in $(seq 1 $((next_job_id - 1))); do
          job_pid_file="$tmp_dir/job_${job_id}_pid"
          job_status_file="$tmp_dir/job_${job_id}_status"
          
          # Skip if we've already processed this job
          [ ! -f "$job_pid_file" ] && continue
          
          # Get the PID
          pid=$(cat "$job_pid_file")
          
          # Check if the process is still running
          if ! kill -0 $pid 2>/dev/null; then
            # Process is done, look at its status
            if [ -f "$job_status_file" ]; then
              job_status=$(cat "$job_status_file")
              
              # Mark as processed regardless of outcome
              total_processed=$((total_processed + 1))
              
              if [ "$job_status" = "failed" ]; then
                # If a job failed and we've reached max consecutive failures, exit
                failure_count=$(read_counter "$failure_tracker")
                if [ $failure_count -ge $MAX_CONSECUTIVE_FAILURES ]; then
                  echo "⛔ ERROR: $MAX_CONSECUTIVE_FAILURES consecutive download failures detected"
                  echo "⛔ Stopping script execution to prevent further errors"
                  # Clean up
                  pkill -P $$ 2>/dev/null
                  exit 2
                fi
                
                # Check if we've entered an outage state
                outage_status=$(check_outage_status "$outage_tracker")
                if [ "$outage_status" = "1" ]; then
                  echo "⚠️ Server outage detected, waiting before starting new downloads..."
                  sleep $SERVER_OUTAGE_WAIT
                fi
              fi
            fi
            
            # Remove job tracking files
            rm -f "$job_pid_file" "$job_status_file"
            
            # Decrement active job counter
            active_jobs=$((active_jobs - 1))
          fi
        done
        
        # Small sleep to prevent CPU spinning
        sleep 0.5
      done
      
      # Wait between starting new downloads to avoid overwhelming server
      sleep $SLEEP_BETWEEN_DOWNLOADS
      
      # Start a new download in the background
      job_id=$next_job_id
      next_job_id=$((next_job_id + 1))
      log_prefix="[Image $i] "
      
      download_file "$actual_url" "$output_file" "$i" "$max_images" "$log_prefix" "$failure_tracker" "$outage_tracker" "$job_id" &
      
      # Store the PID of the background job
      pid=$!
      echo $pid > "$tmp_dir/job_${job_id}_pid"
      echo $i > "$tmp_dir/job_${job_id}_item"
      active_jobs=$((active_jobs + 1))
    done
    
    # Wait for all remaining jobs to complete
    echo "Waiting for remaining downloads to complete..."
    for job_id in $(seq 1 $((next_job_id - 1))); do
      job_pid_file="$tmp_dir/job_${job_id}_pid"
      
      # Skip if we've already processed this job
      [ ! -f "$job_pid_file" ] && continue
      
      # Get the PID
      pid=$(cat "$job_pid_file")
      
      # Wait for it to complete
      if kill -0 $pid 2>/dev/null; then
        wait $pid
      fi
      
      # Remove job tracking files
      rm -f "$tmp_dir/job_${job_id}_pid" "$tmp_dir/job_${job_id}_status" "$tmp_dir/job_${job_id}_item"
    done
    
    # Show final progress
    echo "Progress: 100% complete ($total_processed/$total_to_process)"
    
  else
    # Test mode - simulate processing
    for i in $(seq 1 "$max_images"); do
      # Create padded filename
      padded_filename=$(printf "%0${padding_width}d.jpg" "$i")
      
      # Output file path
      output_file="$folder_path/$padded_filename"
      
      # Create actual URL by replacing "1.jpg" with current number
      actual_url=$(echo "$base_url" | gsed "s/1.jpg/$i.jpg/")
      
      if [ -f "$output_file" ]; then
        # Get file size if it exists
        file_size=$(du -k "$output_file" 2>/dev/null | cut -f1)
        if [ -n "$file_size" ] && [ "$file_size" -ge 10 ]; then
          echo "[TEST] Would skip: $output_file (already exists, size: ${file_size}KB)"
        else
          echo "[TEST] Would remove small file: $output_file (size: ${file_size:-0}KB)"
          echo "[TEST] Would download: $actual_url -> $output_file"
        fi
      else
        echo "[TEST] Would download: $actual_url -> $output_file"
      fi
      
      # Only show every 10th item in test mode to reduce output
      if (( i % 10 == 0 )) || (( i == 1 )) || (( i == max_images )); then
        echo "[TEST] Would process image $i of $max_images (concurrent with other downloads)"
      fi
      
      # Simulate concurrency in test mode by displaying groups
      if (( i % MAX_CONCURRENT_DOWNLOADS == 0 )); then
        echo "[TEST] Would download files $(( i - MAX_CONCURRENT_DOWNLOADS + 1 ))-$i concurrently"
      fi
      
      # Simulate server outage detection
      if (( i % 100 == 0 )); then
        echo "[TEST] Would detect potential server outage at item $i and wait $SERVER_OUTAGE_WAIT seconds"
      fi
    done
  fi
  
  echo "Completed processing for: $dir_name"
  end_time=$(date +%s)
  duration=$((end_time - start_time))
  echo "Time taken: $((duration / 60)) minutes and $((duration % 60)) seconds"

  if [ "$TEST_MODE" = false ]; then
    echo "Total expected files: $max_images"
    echo "Total actual files: $(ls -1 "$folder_path" 2>/dev/null | wc -l | tr -d ' ')"
  else
    echo "[TEST] Would download total of $max_images files"
  fi
  echo "======================================"
  
done < "$INPUT_FILE"

if [ "$TEST_MODE" = false ]; then
  echo "Download process complete!"
  echo "All files have been saved in the '$parent_dir' directory"
else
  echo "Test run complete! No files were downloaded."
  echo "In normal mode, files would be saved in the '$parent_dir' directory"
fi
echo "======================================"
