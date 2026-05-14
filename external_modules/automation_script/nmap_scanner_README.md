# Comprehensive Network Scanner using Nmap

A powerful Python wrapper for Nmap that provides detailed network reconnaissance and security assessment capabilities with comprehensive reporting.

## 🚀 Features

### 🔍 **Scan Types**
- **Host Discovery**: Find live hosts on networks
- **Port Scanning**: Detect open ports with various scan techniques
- **Service Detection**: Identify services and versions running on ports
- **OS Detection**: Fingerprint operating systems (requires root)
- **Vulnerability Scanning**: Basic vulnerability assessment using NSE scripts

### 📊 **Scan Modes**
- **Quick**: Fast scan of top 1000 ports
- **Common**: Scan top 2000 ports
- **Comprehensive**: Full port scan (all 65535 ports)
- **Stealth**: Slow, stealthy SYN scan
- **UDP**: UDP port scanning

### 📋 **Output Features**
- Real-time results display
- Structured JSON output
- Comprehensive scan summaries
- Detailed timing information
- Error handling and logging

## 🛡️ **Legal Notice**

**⚠️ IMPORTANT**: Only use this tool on:
- Networks you own
- Systems you have explicit written permission to test
- Lab environments and testing infrastructure

Unauthorized network scanning may be illegal and violate terms of service.

## 📦 **Prerequisites**

### Install Nmap
```bash
# macOS (Homebrew)
brew install nmap

# macOS (MacPorts)
sudo port install nmap

# Ubuntu/Debian
sudo apt-get install nmap

# CentOS/RHEL/Fedora
sudo yum install nmap
# or
sudo dnf install nmap

# Windows
# Download from https://nmap.org/download.html
```

### Python Dependencies
```bash
# Already included in standard library:
# - subprocess, json, xml, os, sys, argparse, datetime, socket, ipaddress
```

## 🚀 **Usage Examples**

### Basic Usage
```bash
# Quick scan of localhost
python nmap_network_scanner.py 127.0.0.1 --port-scan

# Scan local network (auto-detected)
python nmap_network_scanner.py

# Scan specific target with all features
python nmap_network_scanner.py 192.168.1.1 --all
```

### Host Discovery
```bash
# Find live hosts on network
python nmap_network_scanner.py 192.168.1.0/24 --host-discovery

# Scan multiple hosts
python nmap_network_scanner.py "192.168.1.1-10" --host-discovery
```

### Port Scanning
```bash
# Quick port scan
python nmap_network_scanner.py 192.168.1.1 --port-scan --scan-type quick

# Comprehensive port scan
python nmap_network_scanner.py 192.168.1.1 --port-scan --scan-type comprehensive

# Stealth scan
python nmap_network_scanner.py 192.168.1.1 --port-scan --scan-type stealth

# UDP scan
python nmap_network_scanner.py 192.168.1.1 --port-scan --scan-type udp
```

### Service Detection
```bash
# Detect services and versions
python nmap_network_scanner.py 192.168.1.1 --service-detection

# Combined port and service scan
python nmap_network_scanner.py 192.168.1.1 --port-scan --service-detection
```

### OS Detection
```bash
# Requires root privileges
sudo python nmap_network_scanner.py 192.168.1.1 --os-detection

# Combined with other scans
sudo python nmap_network_scanner.py 192.168.1.1 --all
```

### Vulnerability Assessment
```bash
# Basic vulnerability scan
python nmap_network_scanner.py 192.168.1.1 --vulnerability-scan

# Full security assessment
python nmap_network_scanner.py 192.168.1.1 --all --output security_report.json
```

### Advanced Examples
```bash
# Scan web servers
python nmap_network_scanner.py "google.com,github.com" --port-scan

# Scan with custom output
python nmap_network_scanner.py 192.168.1.0/24 --all --output network_audit.json

# Domain scanning
python nmap_network_scanner.py example.com --service-detection
```

## 📋 **Command Line Options**

### Positional Arguments
- `target`: IP address, hostname, or network range (CIDR notation)

### Optional Arguments
- `--scan-type {quick,common,comprehensive,stealth,udp}`: Port scan type
- `--host-discovery`: Perform host discovery scan
- `--port-scan`: Perform port scanning
- `--service-detection`: Detect service versions
- `--os-detection`: Perform OS fingerprinting (requires root)
- `--vulnerability-scan`: Run vulnerability assessment
- `--all`: Perform all available scans
- `--output OUTPUT`: Save results to specified file

## 🎯 **Target Formats**

### Single Targets
```bash
192.168.1.1          # Single IP
example.com          # Hostname
localhost            # Local system
```

### Network Ranges
```bash
192.168.1.0/24       # CIDR notation
192.168.1.1-10       # IP range
192.168.1.*          # Wildcard (use quotes)
```

### Multiple Targets
```bash
"192.168.1.1,192.168.1.10"     # Multiple IPs
"google.com,github.com"        # Multiple domains
```

## 📊 **Sample Output**

```
============================================================
🛡️  COMPREHENSIVE NETWORK SCANNER
============================================================
⚠️  IMPORTANT LEGAL NOTICE:
   Only use this tool on networks you own or have explicit permission to scan.
============================================================
✅ Nmap found: Nmap version 7.98

🎯 Target: 192.168.1.1

🔍 HOST DISCOVERY
----------------------------------------
Found 12 live hosts

🔍 PORT SCANNING
----------------------------------------
Target: 192.168.1.1
Scan Type: quick
✅ Found 5 open ports

🔍 SERVICE VERSION DETECTION
----------------------------------------
22/tcp   open  ssh     OpenSSH 8.2p1
80/tcp   open  http    Apache httpd 2.4.41
443/tcp  open  https   Apache httpd 2.4.41
3306/tcp open  mysql   MySQL 8.0.25

============================================================
SCAN SUMMARY
============================================================
Scan Duration: 0:02:15.123456
Live Hosts Found: 12
Open Ports Found: 5
Scans Performed:
  ✅ Host Discovery
  ✅ Port Scan
  ✅ Service Detection

💾 Results saved to: nmap_scan_results_20241011_001234.json
```

## 🔧 **Configuration**

### Scan Timing
The script uses different timing templates:
- **Quick/Common**: `-T4` (Aggressive timing)
- **Comprehensive**: `-T4` (Aggressive timing)
- **Stealth**: `-T2` (Polite timing)

### Port Ranges
- **Quick**: Top 1000 most common ports
- **Common**: Top 2000 ports
- **Comprehensive**: All 65535 ports
- **UDP**: Top 100 UDP ports

### Script Categories
The vulnerability scan uses the `vuln` NSE script category, which includes:
- CVE detection scripts
- Common vulnerability checks
- Security misconfigurations
- Default credential checks

## 🚨 **Permissions & Limitations**

### Root Privileges Required For:
- OS detection (`-O` flag)
- Some advanced scan techniques
- Raw packet manipulation
- ICMP scans

### Non-Root Limitations:
- TCP Connect scans only (no SYN scans)
- No OS fingerprinting
- Limited timing accuracy
- Some NSE scripts may not work

### Network Limitations:
- Firewalls may block scans
- Rate limiting by target systems
- IDS/IPS detection and blocking
- Network segmentation restrictions

## 🛠️ **Troubleshooting**

### Common Issues

**Nmap Not Found**
```bash
# Install nmap first
brew install nmap  # macOS
sudo apt install nmap  # Linux
```

**Permission Denied**
```bash
# Run with sudo for full features
sudo python nmap_network_scanner.py target --os-detection
```

**Scan Timeouts**
```bash
# Use faster scan types for large networks
python nmap_network_scanner.py network --scan-type quick
```

**No Results**
- Check target is reachable: `ping target`
- Verify network connectivity
- Check firewall rules
- Try different scan types

### Error Messages

**"TCP/IP fingerprinting requires root privileges"**
- Solution: Run with `sudo` or disable OS detection

**"Scan timed out"**
- Solution: Use faster scan type or smaller target range

**"Permission denied"**
- Solution: Check network access and target permissions

## 🔒 **Security Considerations**

### Ethical Usage
- Always get written authorization
- Document scan activities
- Follow responsible disclosure
- Respect rate limits and system resources

### Detection Avoidance
- Use stealth timing (`--scan-type stealth`)
- Spread scans across time
- Use different source IPs (advanced)
- Randomize scan order

### Legal Compliance
- Check local laws and regulations
- Review terms of service
- Maintain scan logs for auditing
- Get proper authorization documentation

## 📈 **Advanced Usage**

### Automated Scanning
```bash
# Schedule regular network audits
0 2 * * 0 /path/to/python /path/to/nmap_network_scanner.py network --all --output weekly_scan.json
```

### Integration with Other Tools
```bash
# Parse results with jq
cat scan_results.json | jq '.host_discovery.live_hosts[]'

# Convert to CSV for reporting
python -c "import json; data=json.load(open('results.json')); print('\\n'.join(data['host_discovery']['live_hosts']))"
```

### Custom NSE Scripts
```bash
# Add custom script execution
nmap --script custom-script.nse target
```

## 🎓 **Learning Resources**

- **Nmap Official Documentation**: https://nmap.org/docs.html
- **NSE Script Documentation**: https://nmap.org/nsedoc/
- **Network Security Scanning**: https://nmap.org/book/
- **Legal Guidelines**: https://nmap.org/book/legal-issues.html

## 📝 **License & Disclaimer**

This tool is provided for educational and authorized security testing purposes only. Users are responsible for ensuring compliance with all applicable laws and regulations. The authors are not responsible for any misuse or damage caused by this tool.

**Use responsibly and ethically!** 🛡️