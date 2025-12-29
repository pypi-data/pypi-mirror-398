#!/bin/bash

# Example script to test file download

# Set your server address
export SFT_SERVICE=localhost:12345

# Download file by ID (replace with actual file ID)
if [ -z "$1" ]; then
    echo "Usage: $0 <file-id>"
    echo "Example: $0 763298"
    exit 1
fi

sft download $1
