#!/usr/bin/env python3
"""
Test Data Generator Script

This script creates a specified number of test files with a given size
in the ./data/test directory for testing purposes.
"""

import os
import random
import string
import shutil
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import time

# Configuration Constants
NUMBER_OF_FILES = 5000  # Number of test files to create
FILE_SIZE_MB = 8    # Size of each file in megabytes
MAX_THREADS = 8       # Number of threads to use for parallel processing
USE_COPY_METHOD = True  # Use fast copy method instead of generating content

# Thread-local random generator for thread safety
thread_local = threading.local()

def create_test_directory():
    """Create the test directory if it doesn't exist."""
    test_dir = os.path.join("data", "test")
    if not os.path.exists(test_dir):
        os.makedirs(test_dir)
        print(f"Created directory: {test_dir}")
    return test_dir

def get_thread_local_random():
    """Get a thread-local random generator for thread safety."""
    if not hasattr(thread_local, 'random'):
        thread_local.random = random.Random()
    return thread_local.random

def generate_random_content(size_bytes):
    """Generate random content for the test file."""
    # Generate random text content using thread-local random generator
    rng = get_thread_local_random()
    chars = string.ascii_letters + string.digits + string.punctuation + " \n"
    content = ''.join(rng.choices(chars, k=size_bytes))
    return content

def create_template_file(template_path, size_mb):
    """Create a single template file with random content."""
    print(f"Creating template file: {template_path} ({size_mb} MB)")
    start_time = time.time()
    
    size_bytes = size_mb * 1024 * 1024  # Convert MB to bytes
    
    with open(template_path, 'w', encoding='utf-8') as f:
        # Write content in chunks to avoid memory issues with large files
        chunk_size = 1024 * 1024  # 1 MB chunks
        bytes_written = 0
        
        while bytes_written < size_bytes:
            remaining = size_bytes - bytes_written
            current_chunk_size = min(chunk_size, remaining)
            
            chunk_content = generate_random_content(current_chunk_size)
            f.write(chunk_content)
            bytes_written += current_chunk_size
            
            # Progress indicator for large files
            if size_mb > 50:
                progress = (bytes_written / size_bytes) * 100
                print(f"  Template progress: {progress:.1f}%", end='\r')
    
    if size_mb > 50:
        print()  # New line after progress indicator
    
    elapsed = time.time() - start_time
    print(f"  ✓ Template created in {elapsed:.2f} seconds")
    return template_path

def copy_file_wrapper(args):
    """Wrapper function for copying files to work with ThreadPoolExecutor."""
    file_index, test_dir, template_path = args
    file_name = f"test_file_{file_index:03d}.txt"
    file_path = os.path.join(test_dir, file_name)
    
    try:
        shutil.copy2(template_path, file_path)
        return f"✓ Copied: {file_path}"
    except Exception as e:
        return f"❌ Error copying {file_path}: {e}"
    """Wrapper function for create_test_file to work with ThreadPoolExecutor."""
    file_index, test_dir, file_size_mb = args
    file_name = f"test_file_{file_index:03d}.txt"
    file_path = os.path.join(test_dir, file_name)
    
    try:
        create_test_file(file_path, file_size_mb)
        return f"✓ Created: {file_path}"
    except Exception as e:
        return f"❌ Error creating {file_path}: {e}"

def create_test_file(file_path, size_mb):
    """Create a single test file with the specified size."""
    size_bytes = size_mb * 1024 * 1024  # Convert MB to bytes
    
    print(f"Creating file: {file_path} ({size_mb} MB)")
    
    with open(file_path, 'w', encoding='utf-8') as f:
        # Write content in chunks to avoid memory issues with large files
        chunk_size = 1024 * 1024  # 1 MB chunks
        bytes_written = 0
        
        while bytes_written < size_bytes:
            remaining = size_bytes - bytes_written
            current_chunk_size = min(chunk_size, remaining)
            
            chunk_content = generate_random_content(current_chunk_size)
            f.write(chunk_content)
            bytes_written += current_chunk_size
            
            # Progress indicator for large files
            if size_mb > 50:
                progress = (bytes_written / size_bytes) * 100
                print(f"  Progress: {progress:.1f}%", end='\r')
    
    if size_mb > 50:
        print()  # New line after progress indicator
    print(f"  ✓ Created: {file_path}")

def main():
    """Main function to create all test files."""
    method_name = "Copy Method" if USE_COPY_METHOD else "Generation Method"
    print("=" * 60)
    print(f"TEST DATA GENERATOR ({method_name})")
    print("=" * 60)
    print(f"Configuration:")
    print(f"  Number of files: {NUMBER_OF_FILES}")
    print(f"  File size: {FILE_SIZE_MB} MB each")
    print(f"  Total data: {NUMBER_OF_FILES * FILE_SIZE_MB} MB")
    print(f"  Threads: {MAX_THREADS}")
    print(f"  Method: {method_name}")
    print("=" * 60)
    
    total_start_time = time.time()
    
    # Create test directory
    test_dir = create_test_directory()
    
    if USE_COPY_METHOD:
        # Fast copy method
        print("Phase 1: Creating template file...")
        template_path = os.path.join(test_dir, "template_file.txt")
        create_template_file(template_path, FILE_SIZE_MB)
        
        print("\nPhase 2: Copying files in parallel...")
        copy_start_time = time.time()
        
        # Prepare arguments for parallel copying
        file_args = [(i, test_dir, template_path) for i in range(1, NUMBER_OF_FILES + 1)]
        
        # Copy files using ThreadPoolExecutor
        completed_files = 0
        with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
            # Submit all copy tasks
            future_to_args = {executor.submit(copy_file_wrapper, args): args for args in file_args}
            
            # Process completed tasks
            for future in as_completed(future_to_args):
                result = future.result()
                completed_files += 1
                
                # Progress indicator (less verbose for copying)
                if completed_files % 50 == 0 or completed_files == NUMBER_OF_FILES:
                    progress = (completed_files / NUMBER_OF_FILES) * 100
                    elapsed = time.time() - copy_start_time
                    rate = completed_files / elapsed if elapsed > 0 else 0
                    print(f"Copying progress: {progress:.1f}% ({completed_files}/{NUMBER_OF_FILES}) - {rate:.1f} files/sec")
        
        # Clean up template file
        if os.path.exists(template_path):
            os.remove(template_path)
            print("Template file removed")
    
    else:
        # Original generation method
        # Prepare arguments for parallel execution
        file_args = [(i, test_dir, FILE_SIZE_MB) for i in range(1, NUMBER_OF_FILES + 1)]
        
        # Create test files using ThreadPoolExecutor
        completed_files = 0
        with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
            # Submit all tasks
            future_to_args = {executor.submit(create_test_file_wrapper, args): args for args in file_args}
            
            # Process completed tasks
            for future in as_completed(future_to_args):
                result = future.result()
                print(result)
                completed_files += 1
                
                # Progress indicator
                progress = (completed_files / NUMBER_OF_FILES) * 100
                print(f"Overall progress: {progress:.1f}% ({completed_files}/{NUMBER_OF_FILES})")
    
    total_elapsed = time.time() - total_start_time
    
    print("=" * 60)
    print("✅ Test data generation completed!")
    print(f"Total time: {total_elapsed:.2f} seconds")
    print(f"Average rate: {NUMBER_OF_FILES / total_elapsed:.1f} files/second")
    print(f"Files created in: {os.path.abspath(test_dir)}")
    
    # Display directory contents (sample)
    if os.path.exists(test_dir):
        files = [f for f in os.listdir(test_dir) if f.startswith('test_file_')]
        print(f"Test files created: {len(files)}")
        
        # Show first few and last few files
        if len(files) > 10:
            sample_files = sorted(files)[:5] + ["..."] + sorted(files)[-5:]
        else:
            sample_files = sorted(files)
            
        for file in sample_files:
            if file == "...":
                print(f"  {file}")
            else:
                file_path = os.path.join(test_dir, file)
                if os.path.isfile(file_path):
                    size_mb = os.path.getsize(file_path) / (1024 * 1024)
                    print(f"  - {file} ({size_mb:.2f} MB)")

# Legacy function for the generation method
def create_test_file_wrapper(args):
    """Wrapper function for create_test_file to work with ThreadPoolExecutor."""
    file_index, test_dir, file_size_mb = args
    file_name = f"test_file_{file_index:03d}.txt"
    file_path = os.path.join(test_dir, file_name)
    
    try:
        create_test_file(file_path, file_size_mb)
        return f"✓ Created: {file_path}"
    except Exception as e:
        return f"❌ Error creating {file_path}: {e}"

if __name__ == "__main__":
    main()
