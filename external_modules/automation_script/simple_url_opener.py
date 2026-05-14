#!/usr/bin/env python3
"""
Simple Human-like URL Opener
Opens URLs in a natural pattern to avoid CAPTCHA and "unusual traffic" detection
"""

import subprocess
import time
import random
import signal
import sys

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    print("\n🛑 Stopping URL opener...")
    print("✅ Script terminated by user")
    sys.exit(0)

def open_url_naturally(url):
    """Open a single URL in Chrome with natural timing"""
    try:
        subprocess.run(['open', '-a', 'Google Chrome', url], timeout=10)
        print(f"🌐 Opened: {url}")
        return True
    except Exception as e:
        print(f"❌ Failed to open {url}: {e}")
        return False

def natural_delay(base_seconds=5, variance=3):
    """Create natural human-like delays with randomness"""
    delay = base_seconds + random.uniform(-variance, variance)
    delay = max(1, delay)  # Ensure minimum 1 second delay
    
    print(f"⏳ Waiting {delay:.1f} seconds (human-like delay)...")
    time.sleep(delay)

def random_page_dwell_time():
    """Simulate time a human would spend on a page"""
    # Humans typically spend 15-45 seconds reading/interacting with a page
    dwell_time = random.uniform(15, 45)
    print(f"📖 Page dwell time: {dwell_time:.1f} seconds")
    time.sleep(dwell_time)

def close_specific_tabs():
    """Close tabs containing aiskillshouse.com while keeping Chrome open"""
    applescript = '''
    tell application "Google Chrome"
        set tabsToClose to {}
        repeat with w in windows
            repeat with t in tabs of w
                if URL of t contains "aiskillshouse.com" then
                    set end of tabsToClose to t
                end if
            end repeat
        end repeat
        repeat with t in tabsToClose
            close t
        end repeat
    end tell
    '''
    try:
        subprocess.run(['osascript', '-e', applescript], check=True, timeout=10)
        print("🗂️ Closed previous aiskillshouse.com tabs")
    except subprocess.CalledProcessError:
        print("⚠️ Could not close tabs (Chrome may not be running)")
    except subprocess.TimeoutExpired:
        print("⚠️ Tab closing timed out")

def simulate_human_browsing_session(urls):
    """Simulate a natural human browsing session"""
    print(f"\n👤 Starting human-like browsing session ({len(urls)} URLs)")
    
    # Close any existing tabs first
    close_specific_tabs()
    natural_delay(2, 1)  # Brief pause after closing tabs
    
    # Randomize URL order to appear more natural
    shuffled_urls = urls.copy()
    random.shuffle(shuffled_urls)
    
    for i, url in enumerate(shuffled_urls, 1):
        print(f"\n📄 [{i}/{len(shuffled_urls)}] Processing URL...")
        
        # Open URL
        if open_url_naturally(url):
            # Simulate reading/interaction time
            random_page_dwell_time()
            
            # Natural delay before next URL (if not the last one)
            if i < len(shuffled_urls):
                natural_delay(base_seconds=8, variance=5)
        else:
            print("⚠️ Skipping to next URL due to error")
            natural_delay(3, 1)  # Short delay on error

def main():
    """Main execution function"""
    signal.signal(signal.SIGINT, signal_handler)
    
    print("🚀 Simple Human-like URL Opener")
    print("🤖 Designed to avoid CAPTCHA and unusual traffic detection")
    print("🔄 Press Ctrl+C to stop")
    
    # URLs to open
    urls = [
        "https://aiskillshouse.com/student/qr-mediator.html?uid=10809&promptId=17",
        "https://aiskillshouse.com/student/qr-mediator.html?uid=10809&promptId=16",
        "https://aiskillshouse.com/student/qr-mediator.html?uid=10809&promptId=15",
        "https://aiskillshouse.com/student/qr-mediator.html?uid=10809&promptId=14",
        "https://aiskillshouse.com/student/qr-mediator.html?uid=10809&promptId=13",
        "https://aiskillshouse.com/student/qr-mediator.html?uid=10807&promptId=17",
        "https://aiskillshouse.com/student/qr-mediator.html?uid=10807&promptId=16",
        "https://aiskillshouse.com/student/qr-mediator.html?uid=10807&promptId=15",
        "https://aiskillshouse.com/student/qr-mediator.html?uid=10807&promptId=14",
        "https://aiskillshouse.com/student/qr-mediator.html?uid=10807&promptId=13"
    ]
    
    print(f"📋 Loaded {len(urls)} URLs for rotation")
    print("-" * 60)
    
    cycle_count = 0
    
    try:
        while True:
            cycle_count += 1
            print(f"\n🔄 Starting browsing cycle #{cycle_count}")
            print(f"⏰ Time: {time.strftime('%H:%M:%S')}")
            
            # Simulate human browsing session
            simulate_human_browsing_session(urls)
            
            # Longer break between cycles to appear natural
            break_time = random.uniform(60, 120)  # 1-2 minutes between cycles
            print(f"\n☕ Taking natural break: {break_time:.1f} seconds")
            print("   (Simulating human break between browsing sessions)")
            
            # Show countdown for longer breaks
            if break_time > 30:
                remaining = int(break_time)
                while remaining > 0:
                    if remaining % 15 == 0:  # Update every 15 seconds
                        print(f"⏰ Break time remaining: {remaining} seconds")
                    time.sleep(1)
                    remaining -= 1
            else:
                time.sleep(break_time)
            
    except KeyboardInterrupt:
        # This should be caught by signal_handler, but just in case
        print("\n🛑 Script interrupted")
        sys.exit(0)

if __name__ == "__main__":
    main()
