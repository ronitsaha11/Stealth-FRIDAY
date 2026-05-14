# System Information Script

A comprehensive Python script that displays detailed device, system, and network information in an organized format.

## Features

The script provides information about:

### 📱 Device Information
- Computer name and platform details
- Operating system (macOS, Windows, Linux)
- System architecture and processor info
- macOS-specific version details

### 🖥️ CPU Information
- Physical and logical core count
- Real-time CPU usage per core
- CPU frequency information (max, min, current)

### 💾 Memory Information
- RAM usage (total, available, used, percentage)
- Swap memory statistics

### 💿 Disk Information
- All mounted partitions and drives
- Storage capacity and usage for each drive
- File system types

### 🌐 Network Information
- All network interfaces with IP addresses (IPv4/IPv6)
- MAC addresses for physical interfaces
- Network usage statistics (bytes sent/received)
- Interface status and specifications
- External IP address and location (requires internet)

### 🔋 Battery Information
- Battery percentage and charging status
- Estimated time remaining (when available)

### 👤 User Information
- Current user and directories
- Python version and executable path
- System boot time and current time

### ⚡ Process Information
- Top 10 processes by CPU usage
- Process details (PID, name, CPU%, memory%)

## Requirements

```bash
pip install psutil requests
```

Or install from requirements.txt:
```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage
```bash
python system_info.py
```

### With Virtual Environment
```bash
# If you have a virtual environment activated
./system_info.py
```

### Full Path (if not in PATH)
```bash
/path/to/python system_info.py
```

## Sample Output

```
************************************************************
COMPREHENSIVE SYSTEM INFORMATION REPORT
Generated on: 2025-10-11 00:03:03
************************************************************

============================================================
DEVICE INFORMATION
============================================================
Computer Name: Arnavs-MacBook-Air-2.local
Platform: macOS-15.6.1-arm64-arm-64bit-Mach-O
System: Darwin
Release: 24.6.0
...

============================================================
CPU INFORMATION
============================================================
Physical Cores: 8
Total Cores: 8
CPU Usage Overall: 59.1%
CPU Usage per Core:
  Core 0: 100.0%
  Core 1: 100.0%
...
```

## Features by Platform

### macOS
- ✅ Complete system information via `sw_vers`
- ✅ Battery information
- ✅ Network interface details
- ✅ All core features supported

### Windows
- ✅ Windows-specific system information
- ✅ Battery information (laptops)
- ✅ Network interface details
- ✅ All core features supported

### Linux
- ✅ Linux distribution information
- ⚠️ Battery info (depends on system)
- ✅ Network interface details
- ✅ All core features supported

## Error Handling

The script includes comprehensive error handling:
- Graceful handling of missing permissions
- Timeout handling for network requests
- Platform-specific feature detection
- Continues execution even if some sections fail

## Privacy and Security

- **Local Execution**: All system information is gathered locally
- **External Requests**: Only makes requests to `httpbin.org` and `ipinfo.io` for external IP
- **No Data Storage**: No information is stored or transmitted beyond display
- **Read-Only**: Script only reads system information, makes no changes

## Customization

You can modify the script to:
- Add more system information sections
- Change the output format
- Add export functionality (JSON, CSV, etc.)
- Customize which sections to display

## Troubleshooting

### Permission Errors
Some disk partitions may show "Permission denied" - this is normal for system partitions.

### Network Timeout
If external IP lookup fails, check your internet connection. The script will continue without external IP information.

### Missing Dependencies
Install required packages:
```bash
pip install psutil requests
```

### Python Version
Requires Python 3.6+ for best compatibility.

## License

This script is provided as-is for educational and system administration purposes.