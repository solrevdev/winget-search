#!/bin/bash
# Force GitHub Pages to update by creating a .nojekyll file and pushing a change

# This script can be run locally to force GitHub Pages to rebuild
# Make sure you're in your repository directory

# Switch to gh-pages branch
git checkout gh-pages

# Pull latest changes
git pull origin gh-pages

# Create or touch .nojekyll file (tells GitHub Pages not to process with Jekyll)
touch .nojekyll

# Add a timestamp to force a change
echo "<!-- Last updated: $(date) -->" >> index.html

# Commit and push
git add .
git commit -m "Force GitHub Pages rebuild - $(date)"
git push origin gh-pages

# Switch back to master
git checkout master

echo "GitHub Pages should rebuild within a few minutes"
