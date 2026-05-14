#!/usr/bin/env python3
"""
Advanced VPN + Browser Fingerprint Rotation Script
Uses Chrome VPN extensions, clears browser data, changes fingerprints, and rotates sessions
"""

import subprocess
import time
import random
import signal
import sys
import requests
import os
from pathlib import Path

def get_current_ip():
    """Get current public IP address"""
    services = [
        'https://api.ipify.org?format=json',
        'https://icanhazip.com',
        'https://ipinfo.io/ip',
        'https://httpbin.org/ip'
    ]
    
    for service in services:
        try:
            response = requests.get(service, timeout=15)
            if 'json' in service or 'httpbin' in service:
                data = response.json()
                ip = data.get('ip') or data.get('origin', '').split(',')[0].strip()
            else:
                ip = response.text.strip()
            
            if ip and len(ip.split('.')) == 4:
                print(f"📍 Current IP: {ip}")
                return ip
        except Exception as e:
            continue
    
    print("❌ Could not determine current IP")
    return None

def get_random_user_agent():
    """Generate random user agent for fingerprint change"""
    user_agents = [
        # Chrome on Windows
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 11.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        
        # Chrome on macOS
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebLib/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        
        # Chrome on Linux
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Ubuntu; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        
        # Safari
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Safari/605.1.15",
        
        # Firefox
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/121.0",
        
        # Edge
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0"
    ]
    
    return random.choice(user_agents)

def get_random_screen_resolution():
    """Generate random screen resolution for fingerprint change"""
    resolutions = [
        "1920,1080",
        "1366,768", 
        "1536,864",
        "1440,900",
        "1280,720",
        "2560,1440",
        "3840,2160",
        "1680,1050",
        "1600,900",
        "2048,1152"
    ]
    return random.choice(resolutions)

def quit_chrome_completely():
    """Quit Chrome completely and wait"""
    try:
        print("🔄 Quitting Chrome completely...")
        subprocess.run(['osascript', '-e', 'quit app "Google Chrome"'], timeout=10)
        time.sleep(5)  # Wait for complete shutdown
        print("✅ Chrome quit successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to quit Chrome: {e}")
        return False

def clear_chrome_data_filesystem():
    """Clear Chrome data from filesystem"""
    try:
        print("🧹 Clearing Chrome data from filesystem...")
        
        chrome_data_paths = [
            "~/Library/Application Support/Google/Chrome/Default/Cookies",
            "~/Library/Application Support/Google/Chrome/Default/Local Storage",
            "~/Library/Application Support/Google/Chrome/Default/Session Storage",
            "~/Library/Application Support/Google/Chrome/Default/IndexedDB",
            "~/Library/Application Support/Google/Chrome/Default/Web Data",
            "~/Library/Application Support/Google/Chrome/Default/History",
            "~/Library/Caches/Google/Chrome/Default/Cache",
            "~/Library/Application Support/Google/Chrome/Default/Service Worker"
        ]
        
        cleared_count = 0
        for path in chrome_data_paths:
            expanded_path = os.path.expanduser(path)
            if os.path.exists(expanded_path):
                try:
                    if os.path.isfile(expanded_path):
                        os.remove(expanded_path)
                        cleared_count += 1
                    elif os.path.isdir(expanded_path):
                        subprocess.run(['rm', '-rf', expanded_path], timeout=10)
                        cleared_count += 1
                except Exception as e:
                    print(f"⚠️ Could not clear {path}: {e}")
        
        print(f"✅ Cleared {cleared_count} Chrome data locations")
        return True
        
    except Exception as e:
        print(f"❌ Filesystem data clear failed: {e}")
        return False

def start_chrome_with_1vpn_and_fingerprint():
    """Start Chrome with 1VPN extension support and modified fingerprint"""
    try:
        print("🚀 Starting Chrome with 1VPN extension and fingerprint changes...")
        
        user_agent = get_random_user_agent()
        screen_res = get_random_screen_resolution()
        
        print(f"🎭 Using user agent: {user_agent[:60]}...")
        print(f"📺 Using screen resolution: {screen_res}")
        
        # Chrome flags optimized for 1VPN extension and fingerprint obfuscation
        chrome_flags = [
            '--new-window',
            f'--user-agent={user_agent}',
            f'--window-size={screen_res.replace(",", "x")}',
            '--disable-web-security',
            '--disable-features=VizDisplayCompositor',
            '--disable-ipc-flooding-protection',
            '--disable-renderer-backgrounding',
            '--disable-backgrounding-occluded-windows',
            '--disable-background-networking',
            '--disable-sync',
            '--metrics-recording-only',
            '--disable-default-apps',
            '--no-first-run',
            '--disable-translate',
            '--disable-background-timer-throttling',
            '--disable-client-side-phishing-detection',
            '--disable-component-extensions-with-background-pages',
            '--disable-extensions-http-throttling',
            '--enable-features=NetworkService,NetworkServiceLogging',
            '--force-webrtc-ip-handling-policy=disable_non_proxied_udp',
            '--disable-webgl',
            '--disable-webgl2',
            '--allow-running-insecure-content',
            '--disable-popup-blocking',
            '--enable-extension-activity-logging'
        ]
        
        # Start Chrome with flags
        cmd = ['open', '-na', 'Google Chrome', '--args'] + chrome_flags
        subprocess.run(cmd, timeout=15)
        
        print("✅ Chrome started with 1VPN-optimized settings")
        time.sleep(8)  # Wait for Chrome to fully load
        
        # Open 1VPN extension page to ensure it's loaded
        time.sleep(2)
        try:
            applescript_load_1vpn = '''
            tell application "Google Chrome"
                activate
                tell front window
                    set newTab to make new tab at end of tabs
                    set URL of newTab to "chrome-extension://akcocjjpkmlniicdeemdceeajlmoabhg/install.html"
                end tell
            end tell
            '''
            subprocess.run(['osascript', '-e', applescript_load_1vpn], timeout=10)
            print("✅ 1VPN extension page loaded")
            time.sleep(3)
        except:
            print("⚠️ Could not load 1VPN extension page")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to start Chrome with 1VPN: {e}")
        return False

def start_chrome_with_extensions_and_fingerprint():
    """Wrapper function for Chrome startup - prioritizes 1VPN setup"""
    return start_chrome_with_1vpn_and_fingerprint()

def activate_1vpn_extension():
    """Activate 1VPN extension specifically"""
    try:
        print("🔐 Attempting to activate 1VPN extension...")
        
        # Method 1: Open 1VPN extension directly
        applescript_1vpn = '''
        tell application "Google Chrome"
            activate
            tell front window
                set newTab to make new tab at end of tabs
                set URL of newTab to "chrome-extension://akcocjjpkmlniicdeemdceeajlmoabhg/install.html"
            end tell
        end tell
        '''
        
        subprocess.run(['osascript', '-e', applescript_1vpn], timeout=15)
        time.sleep(3)
        
        # Method 2: Try to access the popup
        applescript_popup = '''
        tell application "Google Chrome"
            activate
            tell front window
                set newTab to make new tab at end of tabs
                set URL of newTab to "chrome-extension://akcocjjpkmlniicdeemdceeajlmoabhg/popup.html"
            end tell
        end tell
        '''
        
        subprocess.run(['osascript', '-e', applescript_popup], timeout=10)
        time.sleep(2)
        
        # Method 3: Try to click the extension icon
        applescript_click = '''
        tell application "Google Chrome"
            activate
        end tell
        
        delay 2
        
        tell application "System Events"
            tell process "Google Chrome"
                try
                    -- Look for 1VPN extension icon in toolbar
                    click button 1 of group 1 of toolbar 1 of window 1
                    delay 2
                end try
            end tell
        end tell
        '''
        
        subprocess.run(['osascript', '-e', applescript_click], timeout=10)
        
        print("✅ 1VPN extension activation attempted")
        time.sleep(3)
        return True
        
    except Exception as e:
        print(f"❌ 1VPN extension activation failed: {e}")
        return False

def activate_vpn_extension():
    """Main VPN activation function - tries 1VPN first, then others"""
    try:
        print("🔐 Attempting to activate VPN extensions...")
        
        # First try 1VPN specifically
        activate_1vpn_extension()
        
        # Backup: Try other common VPN extensions
        vpn_shortcuts = [
            "chrome-extension://akcocjjpkmlniicdeemdceeajlmoabhg/popup.html",   # 1VPN (primary)
            "chrome-extension://jpfpebmajhhopeonhlcgidhclcccjcik/popup.html",  # NordVPN
            "chrome-extension://fgddmllnllkalaagkghckoinaemmogpe/popup.html",  # ExpressVPN  
            "chrome-extension://ailoabdmgclmfmhdagmlohpjlbpffblp/popup.html",  # Surfshark
            "chrome-extension://bihmplhobchoageeokmgbdihknkjbknd/popup.html",  # ProtonVPN
            "chrome-extension://jplnlifepflhkbkgonidnobkakhmpnmh/popup.html"   # CyberGhost
        ]
        
        # Try to open VPN extension popups
        for vpn_url in vpn_shortcuts:
            try:
                applescript_open_vpn = f'''
                tell application "Google Chrome"
                    tell front window
                        set newTab to make new tab at end of tabs
                        set URL of newTab to "{vpn_url}"
                    end tell
                end tell
                '''
                subprocess.run(['osascript', '-e', applescript_open_vpn], timeout=8)
                time.sleep(1)
            except:
                continue
        
        print("✅ VPN extension activation completed")
        time.sleep(5)
        return True
        
    except Exception as e:
        print(f"❌ VPN extension activation failed: {e}")
        return False

def manual_1vpn_activation_guide():
    """Guide user through manual 1VPN activation"""
    print("\n" + "="*60)
    print("🔐 1VPN (Free VPN Proxy) ACTIVATION GUIDE")
    print("="*60)
    print("Please manually activate/change your 1VPN connection:")
    print()
    print("🎯 1VPN Extension Steps:")
    print("  1. Look for '1' icon in Chrome toolbar (1VPN extension)")
    print("  2. Click the 1VPN extension icon")
    print("  3. Choose a different server location:")
    print("     • United States, United Kingdom, Germany")
    print("     • Canada, Netherlands, Singapore, etc.")
    print("  4. Click 'Connect' or toggle the connection")
    print("  5. Wait for 'Connected' status (green indicator)")
    print()
    print("� To change location:")
    print("  • Disconnect from current server")
    print("  • Select different country/server")
    print("  • Click Connect again")
    print()
    print("💡 If 1VPN not installed:")
    print("  • Chrome Web Store → Search '1VPN' or 'Free VPN Proxy'")
    print("  • Install: chrome-extension://akcocjjpkmlniicdeemdceeajlmoabhg/")
    print("  • Extension ID: akcocjjpkmlniicdeemdceeajlmoabhg")
    print()
    print("🌍 Available Countries (rotate between them):")
    print("  • 🇺🇸 United States  • 🇬🇧 United Kingdom  • 🇩🇪 Germany")
    print("  • 🇨🇦 Canada        • 🇳🇱 Netherlands     • 🇸🇬 Singapore")
    print("  • 🇫🇷 France        • 🇯🇵 Japan          • 🇦🇺 Australia")
    print("="*60)
    
    response = input("Have you connected to/changed 1VPN server? (y/n): ").lower()
    if response == 'y':
        print("✅ 1VPN activation confirmed")
        time.sleep(5)
        return True
    else:
        print("⚠️ Continuing without VPN change...")
        return False

def manual_vpn_activation_guide():
    """Wrapper for manual VPN activation - prioritizes 1VPN"""
    return manual_1vpn_activation_guide()

def inject_fingerprint_randomization():
    """Inject JavaScript to randomize browser fingerprints"""
    try:
        print("🎭 Injecting fingerprint randomization...")
        
        # Create JavaScript injection for fingerprint randomization
        fingerprint_js = '''
        tell application "Google Chrome"
            tell front window
                set newTab to make new tab at end of tabs
                set URL of newTab to "data:text/html,<script>
                    // Randomize screen properties
                    Object.defineProperty(screen, 'width', {get: () => Math.floor(Math.random() * 400) + 1200});
                    Object.defineProperty(screen, 'height', {get: () => Math.floor(Math.random() * 300) + 700});
                    Object.defineProperty(screen, 'availWidth', {get: () => screen.width});
                    Object.defineProperty(screen, 'availHeight', {get: () => screen.height - 40});
                    
                    // Randomize timezone
                    const timezones = ['America/New_York', 'America/Los_Angeles', 'Europe/London', 'Asia/Tokyo'];
                    Object.defineProperty(Intl.DateTimeFormat.prototype, 'resolvedOptions', {
                        value: function() { return {timeZone: timezones[Math.floor(Math.random() * timezones.length)]}; }
                    });
                    
                    // Randomize language
                    const languages = [['en-US'], ['en-GB'], ['de-DE'], ['fr-FR'], ['es-ES']];
                    Object.defineProperty(navigator, 'languages', {get: () => languages[Math.floor(Math.random() * languages.length)]});
                    
                    // Randomize hardware concurrency
                    Object.defineProperty(navigator, 'hardwareConcurrency', {get: () => Math.floor(Math.random() * 8) + 2});
                    
                    // Disable WebRTC
                    navigator.mediaDevices.getUserMedia = undefined;
                    window.RTCPeerConnection = undefined;
                    
                    console.log('Fingerprint randomization injected');
                    setTimeout(() => window.close(), 1000);
                </script>"
                delay 2
                close active tab
            end tell
        end tell
        '''
        
        subprocess.run(['osascript', '-e', fingerprint_js], timeout=15)
        print("✅ Fingerprint randomization injected")
        return True
        
    except Exception as e:
        print(f"❌ Fingerprint injection failed: {e}")
        return False

def open_urls_in_chrome(urls):
    """Open URLs in Chrome"""
    print("🌐 Opening URLs in Chrome...")
    for i, url in enumerate(urls, 1):
        subprocess.run(['open', '-a', 'Google Chrome', url])
        print(f"🌐 [{i}/{len(urls)}] Opening: {url}")
        time.sleep(1)  # Small delay between opens

def close_chrome_tabs():
    """Close all tabs containing aiskillshouse.com while keeping Chrome open"""
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
        subprocess.run(['osascript', '-e', applescript], check=True)
        print("🗂️ Closed aiskillshouse.com tabs")
    except subprocess.CalledProcessError:
        print("⚠️ Could not close tabs - Chrome may not be running")
    time.sleep(2)

def comprehensive_session_rotation():
    """Perform comprehensive session rotation"""
    print("🔄 Starting comprehensive session rotation...")
    
    current_ip = get_current_ip()
    
    # Step 1: Quit Chrome completely
    if not quit_chrome_completely():
        return False
    
    # Step 2: Clear filesystem data
    clear_chrome_data_filesystem()
    
    # Step 3: Start Chrome with new fingerprint
    if not start_chrome_with_extensions_and_fingerprint():
        return False
    
    # Step 4: Try to activate VPN automatically
    activate_vpn_extension()
    
    # Step 5: Manual VPN guide
    manual_vpn_activation_guide()
    
    # Step 6: Inject additional fingerprint randomization
    inject_fingerprint_randomization()
    
    # Step 7: Check for IP change
    time.sleep(10)
    new_ip = get_current_ip()
    
    if new_ip and new_ip != current_ip:
        print(f"✅ Session rotation successful! IP: {current_ip} → {new_ip}")
        return new_ip
    else:
        print(f"⚠️ Session rotated but IP unchanged: {current_ip}")
        return current_ip

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    print("\n🛑 Stopping script...")
    try:
        close_chrome_tabs()
        print("✅ Cleaned up opened tabs")
    except:
        pass
    sys.exit(0)

def check_and_install_1vpn():
    """Check if 1VPN is installed and guide installation if needed"""
    try:
        print("🔍 Checking for 1VPN extension...")
        
        # Try to access 1VPN extension
        applescript_check = '''
        tell application "Google Chrome"
            activate
            tell front window
                set newTab to make new tab at end of tabs
                set URL of newTab to "chrome-extension://akcocjjpkmlniicdeemdceeajlmoabhg/install.html"
            end tell
        end tell
        '''
        
        subprocess.run(['osascript', '-e', applescript_check], timeout=10)
        time.sleep(3)
        
        print("✅ 1VPN extension check completed")
        
        # Guide user for installation if needed
        print("\n" + "="*50)
        print("📦 1VPN EXTENSION INSTALLATION")
        print("="*50)
        print("If 1VPN is not installed, follow these steps:")
        print()
        print("1. 🌐 Open Chrome Web Store")
        print("2. 🔍 Search for 'Free VPN Proxy - 1VPN'")
        print("3. ➕ Click 'Add to Chrome'")
        print("4. ✅ Confirm installation")
        print()
        print("Or install directly:")
        print("https://chromewebstore.google.com/detail/free-vpn-proxy-1vpn/akcocjjpkmlniicdeemdceeajlmoabhg")
        print("="*50)
        
        response = input("Is 1VPN extension installed and ready? (y/n): ").lower()
        return response == 'y'
        
    except Exception as e:
        print(f"❌ 1VPN check failed: {e}")
        return False

def main():
    """Main execution function"""
    signal.signal(signal.SIGINT, signal_handler)

    print("🚀 Advanced VPN + Browser Fingerprint Rotation Script")
    print("🔐 Optimized for 1VPN (Free VPN Proxy) Extension")
    print("🎯 Extension ID: akcocjjpkmlniicdeemdceeajlmoabhg")
    
    # Check for 1VPN extension
    if not check_and_install_1vpn():
        print("⚠️ Please install 1VPN extension first, then restart the script.")
        return
    
    initial_ip = get_current_ip()
    if not initial_ip:
        print("❌ Cannot get initial IP. Check internet connection.")
        return

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

    cycle_count = 0
    
    print(f"🎯 Will open {len(urls)} URLs per cycle")
    print("🔐 VPN + Fingerprint rotation enabled")
    print("🔄 Press Ctrl+C to stop")
    print("-" * 70)

    while True:
        cycle_count += 1
        print(f"\n🔄 Starting cycle #{cycle_count}")

        # Perform comprehensive session rotation (skip on first run for setup)
        if cycle_count > 1:
            comprehensive_session_rotation()
        else:
            print("📍 First cycle - setting up environment")
            # Just clear tabs and start fresh on first run
            try:
                close_chrome_tabs()
                time.sleep(2)
            except:
                pass

        # Open URLs
        open_urls_in_chrome(urls)

        # Wait before next cycle
        wait_time = 45
        print(f"⏳ Waiting {wait_time} seconds before next rotation...")
        time.sleep(wait_time)

if __name__ == "__main__":
    main()