#!/bin/bash
# Script to push ELAOMS to GitHub

echo "Pushing Eleven Labs Agents Open Memory System to GitHub..."

# Check if GitHub CLI is authenticated
if ! gh auth status &>/dev/null; then
    echo "GitHub CLI is not authenticated."
    echo "Please run: gh auth login"
    echo "Then run this script again."
    exit 1
fi

# Get GitHub username
GITHUB_USER=$(gh api user --jq .login)

if [ -z "$GITHUB_USER" ]; then
    echo "Could not get GitHub username. Please authenticate first."
    exit 1
fi

echo "GitHub username: $GITHUB_USER"

# Check if remote exists
if git remote get-url origin &>/dev/null; then
    echo "Remote 'origin' already exists."
    REMOTE_URL=$(git remote get-url origin)
    echo "Current remote: $REMOTE_URL"
    
    # Check if it's the correct repository
    if [[ "$REMOTE_URL" == *"cursor_elaoms"* ]]; then
        echo "Remote is already set to cursor_elaoms"
    else
        echo "Updating remote to cursor_elaoms..."
        git remote set-url origin "https://github.com/$GITHUB_USER/cursor_elaoms.git"
    fi
else
    echo "Adding remote 'origin'..."
    git remote add origin "https://github.com/$GITHUB_USER/cursor_elaoms.git"
fi

# Create repository on GitHub if it doesn't exist
if ! gh repo view "$GITHUB_USER/cursor_elaoms" &>/dev/null; then
    echo "Creating repository on GitHub..."
    gh repo create cursor_elaoms --public --description "Eleven Labs Agents Open Memory System" --source=. --remote=origin
else
    echo "Repository already exists on GitHub."
fi

# Push to GitHub
echo "Pushing to GitHub..."
git push -u origin main

echo "Done! Repository is available at: https://github.com/$GITHUB_USER/cursor_elaoms"

