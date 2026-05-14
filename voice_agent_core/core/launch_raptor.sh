#!/bin/bash
# launch_raptor.sh — Helper script for macOS LaunchAgent
# Ensures environment variables and paths are clean

cd "/Users/soumyadebtripathy/Stealth F.R.I.D.A.Y/voice_agent_core"
./.venv/bin/python raptor_launcher.py >> raptor_launcher.log 2>&1
