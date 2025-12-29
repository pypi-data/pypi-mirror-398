#!/bin/bash

# Example script to test file upload

# Set your server address
export SFT_SERVICE=localhost:12345

# Create a test file
echo "This is a test file for Simple File Transfer" > test-file.txt

# Upload the file with 1 hour expiry
sft upload test-file.txt 1h

# Clean up
rm test-file.txt
