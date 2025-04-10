#!/bin/bash

# Store the prompt in a variable to avoid reading it multiple times
PROMPT=$(cat prompt.txt)

# Count total number of files to process
total_files=$(find . -maxdepth 1 -name "out_*" -type f | wc -l)
processed_files=0
total_time=0
start_time_all=$(date +%s)
error_log="errors.txt"

timestamp=$(get_timestamp)
echo "[$timestamp] Found $total_files files to process"
echo "[$timestamp] Errors will be logged to $error_log"

# Function to format seconds into HH:MM:SS
format_time() {
    local seconds=$1
    local hours=$((seconds / 3600))
    local minutes=$(((seconds % 3600) / 60))
    local secs=$((seconds % 60))
    printf "%02d:%02d:%02d" $hours $minutes $secs
}

# Function to format seconds into MM:SS
format_time_short() {
    local seconds=$1
    local minutes=$((seconds / 60))
    local secs=$((seconds % 60))
    printf "%02d:%02d" $minutes $secs
}

# Get current time as formatted string
get_timestamp() {
    date "+%Y-%m-%d %H:%M:%S"
}

# Function to process a file with timeout and retries
process_file() {
    local input_file=$1
    local output_file=$2
    local max_attempts=3
    local timeout_seconds=600  # 10 minutes in seconds
    local attempt=1
    local success=false
    local timestamp=$(get_timestamp)

    while [ $attempt -le $max_attempts ] && [ "$success" = false ]; do
        echo "[$timestamp] Attempt $attempt/$max_attempts for $input_file (timeout: 10 minutes)"
        
        # Use macOS-specific approach for timeout
        (
            # Start the command in background
            cat "$input_file" | llm "$PROMPT" > "$output_file" &
            cmd_pid=$!
            
            # Wait for the process to complete or timeout
            elapsed=0
            while kill -0 $cmd_pid 2>/dev/null && [ $elapsed -lt $timeout_seconds ]; do
                sleep 2
                elapsed=$((elapsed + 2))
            done
            
            # If process is still running after timeout, kill it
            if kill -0 $cmd_pid 2>/dev/null; then
                # Process is still running, kill it
                kill $cmd_pid 2>/dev/null
                wait $cmd_pid 2>/dev/null
                exit 1  # Signal timeout
            else
                # Process completed, wait for its exit code
                wait $cmd_pid
                exit $?  # Pass through the exit code
            fi
        )
        
        exit_code=$?
        timestamp=$(get_timestamp)
        if [ $exit_code -eq 0 ]; then
            echo "[$timestamp] Successfully processed $input_file on attempt $attempt"
            success=true
        else
            if [ $exit_code -eq 1 ]; then
                echo "[$timestamp] Process timed out after 10 minutes for $input_file" | tee -a "$error_log"
            else
                echo "[$timestamp] Process failed with exit code $exit_code for $input_file" | tee -a "$error_log"
            fi
            
            if [ $attempt -lt $max_attempts ]; then
                echo "[$timestamp] Retrying..." | tee -a "$error_log"
            else
                echo "[$timestamp] All attempts failed for $input_file" | tee -a "$error_log"
                echo "[$timestamp] Failed to process $input_file after $max_attempts attempts" >> "$error_log"
            fi
            attempt=$((attempt + 1))
        fi
    done

    return $([ "$success" = true ] && echo 0 || echo 1)
}

# Loop over all files starting with "out_" in the current directory
for file in out_*; do
    # Skip if not a file
    [ -f "$file" ] || continue
    
    # Generate output filename by adding "-en.txt" to the input filename
    output_file="${file}-en.txt"
    
    # Increment processed files counter
    ((processed_files++))
    
    timestamp=$(get_timestamp)
    echo "[$timestamp] Processing file $processed_files/$total_files: $file -> $output_file"
    
    # Start timing for this file
    start_time=$(date +%s)
    
    # Process the file with timeout and retries
    process_file "$file" "$output_file"
    process_result=$?
    
    # End timing for this file
    end_time=$(date +%s)
    file_time=$((end_time - start_time))
    total_time=$((total_time + file_time))
    
    # Calculate average time per file
    if command -v bc > /dev/null; then
        avg_time=$(echo "scale=2; $total_time / $processed_files" | bc)
    else
        avg_time=$((total_time / processed_files))
    fi
    
    # Calculate estimated time remaining
    remaining_files=$((total_files - processed_files))
    if command -v bc > /dev/null; then
        est_remaining_time=$(echo "scale=0; $avg_time * $remaining_files" | bc)
    else
        est_remaining_time=$((avg_time * remaining_files))
    fi
    
    # Format times for display
    file_time_fmt=$(format_time_short $file_time)
    avg_time_fmt=$(format_time_short ${avg_time%.*})
    est_remaining_fmt=$(format_time $est_remaining_time)
    
    timestamp=$(get_timestamp)
    echo "[$timestamp] File completed in: ${file_time_fmt}"
    echo "[$timestamp] Average time per file: ${avg_time_fmt}"
    
    if [ $remaining_files -gt 0 ]; then
        echo "[$timestamp] Estimated remaining time: ${est_remaining_fmt} (${remaining_files} files left)"
        echo "[$timestamp] ------------------------------------"
    fi
done

# Calculate total elapsed time
end_time_all=$(date +%s)
total_elapsed=$((end_time_all - start_time_all))
total_elapsed_fmt=$(format_time $total_elapsed)

timestamp=$(get_timestamp)
echo "[$timestamp] All files processed successfully in ${total_elapsed_fmt}."
echo "[$timestamp] Check $error_log for any errors that occurred during processing."
