#!/bin/bash

# Script to clear all existing folders in the jobs directory
# from the GitHub repository: https://github.com/leanabarbion/workflow-repo

echo "Clearing jobs folder from workflow-repo..."

# Clone the repository if it doesn't exist
if [ ! -d "workflow-repo" ]; then
    echo "Cloning repository..."
    git clone https://github.com/leanabarbion/workflow-repo.git
fi

# Navigate to the repository
cd workflow-repo

# Check if jobs directory exists
if [ -d "jobs" ]; then
    echo "Removing all contents from jobs directory..."
    
    # Remove all files and folders in the jobs directory
    rm -rf jobs/*
    
    # Create a .gitkeep file to maintain the directory structure
    touch jobs/.gitkeep
    
    # Add the changes
    git add jobs/
    
    # Commit the changes
    git commit -m "Clear all existing folders in jobs directory"
    
    # Push the changes
    git push origin main
    
    echo "Successfully cleared jobs folder and pushed changes to GitHub!"
else
    echo "Jobs directory not found. Creating it..."
    mkdir -p jobs
    touch jobs/.gitkeep
    git add jobs/
    git commit -m "Create empty jobs directory"
    git push origin main
    echo "Created empty jobs directory and pushed to GitHub!"
fi

echo "Done!" 