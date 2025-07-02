#!/bin/bash

# Upload Backend Files to GitHub Repository
# This script uploads the backend Python files to the workflow-repo

# Configuration
REPO_OWNER="leanabarbion"
REPO_NAME="workflow-repo"
BRANCH="main"
BACKEND_FOLDER="backend"
GITHUB_TOKEN="${GITHUB_TOKEN}"

# Check if GitHub token is set
if [ -z "$GITHUB_TOKEN" ]; then
    echo "Error: GITHUB_TOKEN environment variable is not set"
    echo "Please set your GitHub token: export GITHUB_TOKEN=your_token_here"
    exit 1
fi

# Create temporary directory for backend files
TEMP_DIR=$(mktemp -d)
echo "Created temporary directory: $TEMP_DIR"

# Copy backend files to temp directory (excluding test folder and unnecessary files)
echo "Copying backend files..."
cp backend/*.py "$TEMP_DIR/"
cp backend/requirements.txt "$TEMP_DIR/"
cp backend/*.md "$TEMP_DIR/"

# Remove any unnecessary files that might have been copied
cd "$TEMP_DIR"
rm -f trash.py 2>/dev/null
rm -f output.json 2>/dev/null
rm -f package*.json 2>/dev/null

# List files to be uploaded
echo "Files to be uploaded:"
ls -la

# Create backend folder in repository
BACKEND_REPO_PATH="backend"

# Upload each file to GitHub
for file in *.py *.txt *.md; do
    if [ -f "$file" ]; then
        echo "Uploading $file..."
        
        # Read file content
        content=$(cat "$file")
        
        # Encode content to base64
        encoded_content=$(echo "$content" | base64 -w 0)
        
        # Create JSON payload
        json_payload=$(cat <<EOF
{
    "message": "Add backend file: $file",
    "content": "$encoded_content",
    "branch": "$BRANCH"
}
EOF
)
        
        # Upload file to GitHub
        response=$(curl -s -w "%{http_code}" -X PUT \
            -H "Authorization: token $GITHUB_TOKEN" \
            -H "Content-Type: application/json" \
            -d "$json_payload" \
            "https://api.github.com/repos/$REPO_OWNER/$REPO_NAME/contents/$BACKEND_REPO_PATH/$file")
        
        # Extract HTTP status code
        http_code="${response: -3}"
        response_body="${response%???}"
        
        if [ "$http_code" = "200" ] || [ "$http_code" = "201" ]; then
            echo "✅ Successfully uploaded $file"
        else
            echo "❌ Failed to upload $file (HTTP $http_code)"
            echo "Response: $response_body"
        fi
    fi
done

# Clean up temporary directory
cd /
rm -rf "$TEMP_DIR"
echo "Cleaned up temporary directory"

echo "Backend files upload completed!"
echo "Repository: https://github.com/$REPO_OWNER/$REPO_NAME"
echo "Backend files location: $BACKEND_REPO_PATH/" 