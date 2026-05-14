#!/usr/bin/env python3
"""
Quick Network Scanner Examples
Simple examples demonstrating the network scanner capabilities.
"""

import subprocess
import sys
import os

def run_scanner(command, description):
    """Run a scanner command and display results."""
    print(f"\n{'='*60}")
    print(f"🔍 {description}")
    print('='*60)
    
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=120)
        print(f"Command: {command}")
        print(f"\nOutput:")
        print(result.stdout)
        
        if result.stderr:
            print(f"\nErrors:")
            print(result.stderr)
            
    except subprocess.TimeoutExpired:
        print("⏱️ Command timed out")
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    # Get the path to our scanner
    script_dir = os.path.dirname(os.path.abspath(__file__))
    python_path = f"{script_dir}/venv/bin/python"
    scanner_path = f"{script_dir}/nmap_network_scanner.py"
    
    print("🛡️ Network Scanner Examples")
    print("=" * 60)
    print("These examples demonstrate various scanning capabilities.")
    print("⚠️  Make sure you have permission to scan these targets!")
    
    # Example 1: Scan localhost (always safe)
    run_scanner(
        f"{python_path} {scanner_path} 127.0.0.1 --port-scan --scan-type quick",
        "Quick Port Scan of Localhost"
    )
    
    # Example 2: Host discovery on local network (if user approves)
    response = input("\n🤔 Do you want to scan your local network for live hosts? (y/N): ").lower()
    if response == 'y':
        run_scanner(
            f"{python_path} {scanner_path} --host-discovery",
            "Local Network Host Discovery"
        )
    
    # Example 3: Service detection on localhost
    response = input("\n🤔 Do you want to perform service detection on localhost? (y/N): ").lower()
    if response == 'y':
        run_scanner(
            f"{python_path} {scanner_path} 127.0.0.1 --service-detection",
            "Service Detection on Localhost"
        )
    
    # Example 4: Scan a popular website (if user approves)
    response = input("\n🤔 Do you want to scan google.com (public target)? (y/N): ").lower()
    if response == 'y':
        run_scanner(
            f"{python_path} {scanner_path} google.com --port-scan --scan-type quick",
            "Quick Scan of Google.com"
        )
    
    print(f"\n{'='*60}")
    print("✅ Examples completed!")
    print("📚 Check nmap_scanner_README.md for more advanced usage")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()