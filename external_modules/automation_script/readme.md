# Automation Scripts Collection

🚀 **A collection of powerful automation scripts for various tasks including URL opening with IP rotation, system information gathering, network scanning, and GitHub profile statistics.**

## 📋 Table of Contents

- [Scripts Overview](#scripts-overview)
- [GitHub Profile Statistics](#github-profile-statistics) ⭐ NEW
- [URL Opener with IP Rotation](#url-opener-with-ip-rotation)
- [System Information Tool](#system-information-tool)
- [Network Scanner](#network-scanner)
- [Installation Guide](#installation-guide)
- [Files Included](#files-included)

---

## 🎯 Scripts Overview

### 1. GitHub Profile Statistics ⭐ NEW
Comprehensive GitHub profile analyzer that fetches and displays detailed statistics for any public GitHub profile.

**Quick Start:**
```bash
python github_stats.py username
```

**Features:**
- ✅ Complete profile information (followers, repos, gists)
- ✅ Repository statistics (stars, forks, watchers)
- ✅ Programming language analysis with percentages
- ✅ Top repositories by stars and forks
- ✅ License and topics distribution
- ✅ JSON export functionality
- ✅ GitHub API rate limit monitoring

📖 **[Full Documentation](github_stats_README.md)** | 🚀 **[Quick Start Guide](GITHUB_STATS_QUICKSTART.md)**

---

### 2. URL Opener with IP Rotation
Automated URL opener that opens links, rotates IP address through Tor network, and repeats the cycle.

**Features:**
- ✅ Opens customizable URLs per cycle
- 🔄 Routes traffic through Tor for IP rotation
- 🌐 Works with Chrome browser via Selenium
- 🛑 Graceful shutdown with Ctrl+C

---

### 3. System Information Tool
Comprehensive system information gathering script.

---

### 4. Network Scanner
Network scanning automation using nmap.

---

## 📦 GitHub Profile Statistics

### Installation

```bash
# Install dependencies
pip install requests

# Or use the project requirements
pip install -r requirements.txt
```

### Basic Usage

```bash
# Analyze any GitHub profile
python github_stats.py torvalds

# With GitHub token (recommended for higher rate limits)
export GITHUB_TOKEN=your_token_here
python github_stats.py username

# Export to JSON
python github_stats.py username --export
```

### Example Output

```
👤 GITHUB PROFILE: @torvalds
======================================================================

📋 Basic Information:
   Name: Linus Torvalds
   Followers: 185,234
   Public Repos: 6

📊 Overall Stats:
   Total Stars Received: ⭐ 175,432
   Total Forks: 🍴 51,234

🔤 PROGRAMMING LANGUAGES
   1. C                     ████████████████████████████████ 85.34%
   2. Assembly              ████                              8.23%
```

### Files
- `github_stats.py` - Main script
- `github_stats_README.md` - Complete documentation
- `GITHUB_STATS_QUICKSTART.md` - Quick start guide
- `github_stats_example.py` - Usage examples

---

## 🌐 URL Opener with IP Rotation

### Table of Contents

- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation Guide](#installation-guide)
  - [Windows Setup](#windows-setup)
  - [macOS Setup](#macos-setup)
  - [Linux Setup](#linux-setup)
- [Configuration](#configuration)
- [Usage](#usage)
- [Troubleshooting](#troubleshooting)

## 🎯 Features

- ✅ Opens 5 customizable URLs per cycle
- 🔄 Routes all traffic through Tor for IP rotation
- 🌐 Works with Chrome browser via Selenium
- 🛑 Graceful shutdown with Ctrl+C
- 📊 Real-time status updates and progress tracking
- 🔒 Automatic browser cleanup and error recovery
- ⏰ Random wait times between cycles (15-45 seconds)

## 📦 Prerequisites

### Required Software:
- **Python 3.8+** 
- **Google Chrome** browser
- **Tor** service
- **ChromeDriver** (matching your Chrome version)

---

## 🚀 Installation Guide

### Windows Setup

#### 1. Install Python
- Download from [python.org](https://www.python.org/downloads/)
- ✅ Check "Add Python to PATH" during installation
- Verify: `python --version`

#### 2. Install Tor
```cmd
# Download Tor Expert Bundle from https://www.torproject.org/download/
# Extract to C:\Tor\

# Open Command Prompt as Administrator
cd C:\Tor
echo SocksPort 9050 > torrc
echo ControlPort 9051 >> torrc
echo CookieAuthentication 1 >> torrc

# Start Tor service
tor.exe
```

#### 3. Install ChromeDriver
```cmd
# Download ChromeDriver from https://chromedriver.chromium.org/
# Extract chromedriver.exe to C:\chromedriver\
# Add C:\chromedriver to your PATH environment variable
```

#### 4. Install Python Dependencies
```cmd
pip install selenium requests pysocks stem
```

#### 5. Update Script Configuration
Edit `improved_url_opener.py`:
```python
chromedriver_path = "C:\chromedriver\chromedriver.exe"
```

---

### macOS Setup

#### 1. Install Python
```bash
# Install using Homebrew (recommended)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
brew install python

# Verify installation
python3 --version
```

#### 2. Install Tor
```bash
# Install Tor using Homebrew
brew install tor

# Start Tor service
brew services start tor

# Verify Tor is running
brew services list | grep tor
```

#### 3. Install ChromeDriver
```bash
# Option A: Using Homebrew
brew install chromedriver

# Option B: Manual download
# Download from https://chromedriver.chromium.org/
# Extract to desired location (e.g., ~/Desktop/chromedriver-mac-arm64/)
# Make executable:
chmod +x /path/to/chromedriver
xattr -d com.apple.quarantine /path/to/chromedriver
```

#### 4. Install Python Dependencies
```bash
pip3 install selenium requests pysocks stem
```

#### 5. Update Script Configuration
Edit `improved_url_opener.py`:
```python
# If using Homebrew ChromeDriver
chromedriver_path = "/opt/homebrew/bin/chromedriver"

# If using manual download
chromedriver_path = "/Users/yourusername/Desktop/chromedriver-mac-arm64/chromedriver"
```

---

### Linux Setup

#### 1. Install Python
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3 python3-pip

# CentOS/RHEL
sudo yum install python3 python3-pip

# Verify installation
python3 --version
```

#### 2. Install Tor
```bash
# Ubuntu/Debian
sudo apt install tor

# CentOS/RHEL
sudo yum install tor

# Start and enable Tor service
sudo systemctl start tor
sudo systemctl enable tor

# Check status
sudo systemctl status tor
```

#### 3. Configure Tor
```bash
# Edit Tor configuration
sudo nano /etc/tor/torrc

# Add these lines:
SocksPort 9050
ControlPort 9051
CookieAuthentication 1

# Restart Tor
sudo systemctl restart tor
```

#### 4. Install ChromeDriver
```bash
# Ubuntu/Debian
sudo apt install chromium-chromedriver

# Or download manually:
wget https://chromedriver.storage.googleapis.com/LATEST_RELEASE
LATEST=$(cat LATEST_RELEASE)
wget https://chromedriver.storage.googleapis.com/${LATEST}/chromedriver_linux64.zip
unzip chromedriver_linux64.zip
sudo mv chromedriver /usr/local/bin/
sudo chmod +x /usr/local/bin/chromedriver
```

#### 5. Install Python Dependencies
```bash
pip3 install selenium requests pysocks stem
```

#### 6. Update Script Configuration
Edit `improved_url_opener.py`:
```python
# If installed via package manager
chromedriver_path = "/usr/bin/chromedriver"

# If installed manually
chromedriver_path = "/usr/local/bin/chromedriver"
```

---

## ⚙️ Configuration

### 1. Update ChromeDriver Path
Open `improved_url_opener.py` and update line 31:
```python
chromedriver_path = "/path/to/your/chromedriver"
```

**Replace with your actual path:**
- **Windows:** `"C:\chromedriver\chromedriver.exe"`
- **macOS:** `"/opt/homebrew/bin/chromedriver"` or your download path
- **Linux:** `"/usr/bin/chromedriver"` or `"/usr/local/bin/chromedriver"`

### 2. Customize URLs (Optional)
Edit the `urls` list in `improved_url_opener.py` (lines 18-24):
```python
urls = [
    "https://check.torproject.org/",      # Replace with your URLs
    "https://icanhazip.com",
    "https://httpbin.org/ip",
    "https://whatismyipaddress.com/",
    "https://stackoverflow.com"
]
```

### 3. Verify Tor Configuration
Run the diagnostic script:
```bash
python tor_chrome_diagnostic.py
```
Should show: ✅ All tests passed

---

## 🎮 Usage

### Running the Script
```bash
# Windows
python improved_url_opener.py

# macOS/Linux
python3 improved_url_opener.py
```

### Expected Output
```
🔧 URL OPENER WITH TOR INTEGRATION
=============================================
⚠️  REQUIREMENTS:
• Tor service must be running on port 9050
• ChromeDriver must be accessible
• Press Ctrl+C to stop safely
=============================================

🚀 Starting Chrome browser with Tor SOCKS proxy
📋 Make sure Tor service is running on port 9050

🔄 Cycle 1
--------------------
📂 Opening URL 1: https://check.torproject.org/
📂 Opening URL 2: https://icanhazip.com
📂 Opening URL 3: https://httpbin.org/ip
📂 Opening URL 4: https://whatismyipaddress.com/
📂 Opening URL 5: https://stackoverflow.com
✅ Finished opening URLs
⏳ Waiting 32 seconds before next cycle...
   ⏰ 30s remaining...
   ⏰ 20s remaining...
   ⏰ 10s remaining...
```

### Stopping the Script
- Press **Ctrl+C** to stop safely
- Browser will close automatically
- Script will show: `🔒 Browser closed safely`

---

## 🔧 Troubleshooting

### Common Issues & Solutions

#### ❌ "Tor service not running"
```bash
# Windows
# Navigate to Tor directory and run: tor.exe

# macOS
brew services start tor

# Linux
sudo systemctl start tor
```

#### ❌ "ChromeDriver version mismatch"
```bash
# Check Chrome version: chrome://version/
# Download matching ChromeDriver from chromedriver.chromium.org
# Or use webdriver-manager:
pip install webdriver-manager
```

#### ❌ "Sorry. You are not using Tor"
```bash
# Test Tor manually:
curl --socks5-hostname 127.0.0.1:9050 https://icanhazip.com

# If this fails, restart Tor:
brew services restart tor  # macOS
sudo systemctl restart tor # Linux
```

#### ❌ "No such window" error
- The improved script handles this automatically
- Browser will recover and continue

#### ❌ macOS "Cannot verify chromedriver"
```bash
xattr -d com.apple.quarantine /path/to/chromedriver
chmod +x /path/to/chromedriver
```

### Getting Help

1. **Run diagnostic script:** `python tor_chrome_diagnostic.py`
2. **Check Tor status:** Visit `https://check.torproject.org/` manually
3. **Verify Chrome version:** Go to `chrome://version/`
4. **Check ChromeDriver:** Run `chromedriver --version`

---

## 📁 Files Included

| File | Description |
|------|-------------|
| `improved_url_opener.py` | Main script with robust error handling |
| `tor_chrome_diagnostic.py` | Diagnostic tool to check Tor setup |
| `url_opener_ip_rotator.py` | Original basic version |
| `simple_url_opener.py` | Simple version without Tor |
| `README.md` | This setup guide |

---

## ⚠️ Important Notes

### Legal & Ethical Usage
- ✅ Use only for legitimate purposes (testing, research, education)
- ✅ Respect website terms of service and rate limits
- ❌ Do not use for malicious activities or attacks
- ❌ Do not violate any laws or regulations

### Privacy & Security
- 🔐 Tor provides anonymity but websites may still block Tor exit nodes
- 🛡️ Some sites may show CAPTCHAs when detecting Tor traffic
- 📊 Monitor your usage to avoid overwhelming target servers

### Performance
- ⏱️ Tor routing may slow down browsing
- 💾 Running multiple browser tabs consumes system resources
- 🔄 Wait times between cycles help prevent server overload

---

## 🎉 Success Indicators

When everything is working correctly:
1. **Chrome opens** with proxy settings applied
2. **check.torproject.org** shows "Congratulations. This browser is configured to use Tor"
3. **IP checking sites** show different IP addresses from your real one
4. **No error messages** in terminal output
5. **Cycles repeat** automatically with random wait times

---

**Happy Browsing! 🚀**

*For additional help or issues, check the troubleshooting section or run the diagnostic script.*
