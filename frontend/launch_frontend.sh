#!/bin/bash
# launch_frontend.sh — Helper script for macOS LaunchAgent
# Starts the Next.js development server in the background

# Ensure we have the right path for Node/NPM
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"

cd "/Users/soumyadebtripathy/Stealth F.R.I.D.A.Y/frontend"
npm run dev >> raptor_frontend.log 2>&1
