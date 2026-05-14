#!/usr/bin/env python3
"""
System Information Script
Displays comprehensive device, system, and network details in an organized format.
"""

import platform
import psutil
import socket
import subprocess
import json
import os
import sys
from datetime import datetime
import getpass

def get_separator(char='=', length=60):
    """Create a separator line."""
    return char * length

def get_device_info():
    """Get basic device information."""
    print(f"\n{get_separator()}")
    print("DEVICE INFORMATION")
    print(get_separator())
    
    try:
        print(f"Computer Name: {platform.node()}")
        print(f"Platform: {platform.platform()}")
        print(f"System: {platform.system()}")
        print(f"Release: {platform.release()}")
        print(f"Version: {platform.version()}")
        print(f"Machine: {platform.machine()}")
        print(f"Processor: {platform.processor()}")
        print(f"Architecture: {platform.architecture()[0]}")
        
        # Get macOS specific info if available
        if platform.system() == "Darwin":
            try:
                result = subprocess.run(['sw_vers'], capture_output=True, text=True)
                if result.returncode == 0:
                    print("\nmacOS Details:")
                    for line in result.stdout.strip().split('\n'):
                        if ':' in line:
                            key, value = line.split(':', 1)
                            print(f"  {key.strip()}: {value.strip()}")
            except:
                pass
                
    except Exception as e:
        print(f"Error getting device info: {e}")

def get_cpu_info():
    """Get CPU information."""
    print(f"\n{get_separator()}")
    print("CPU INFORMATION")
    print(get_separator())
    
    try:
        print(f"Physical Cores: {psutil.cpu_count(logical=False)}")
        print(f"Total Cores: {psutil.cpu_count(logical=True)}")
        
        # CPU usage per core
        cpu_usage = psutil.cpu_percent(interval=1, percpu=True)
        print(f"CPU Usage Overall: {psutil.cpu_percent(interval=1):.1f}%")
        print("CPU Usage per Core:")
        for i, usage in enumerate(cpu_usage):
            print(f"  Core {i}: {usage:.1f}%")
            
        # CPU frequency
        cpu_freq = psutil.cpu_freq()
        if cpu_freq:
            print(f"Max Frequency: {cpu_freq.max:.2f} MHz")
            print(f"Min Frequency: {cpu_freq.min:.2f} MHz")
            print(f"Current Frequency: {cpu_freq.current:.2f} MHz")
            
    except Exception as e:
        print(f"Error getting CPU info: {e}")

def get_memory_info():
    """Get memory information."""
    print(f"\n{get_separator()}")
    print("MEMORY INFORMATION")
    print(get_separator())
    
    try:
        # Virtual memory
        memory = psutil.virtual_memory()
        print(f"Total RAM: {memory.total / (1024**3):.2f} GB")
        print(f"Available RAM: {memory.available / (1024**3):.2f} GB")
        print(f"Used RAM: {memory.used / (1024**3):.2f} GB")
        print(f"RAM Usage: {memory.percent:.1f}%")
        
        # Swap memory
        swap = psutil.swap_memory()
        print(f"Total Swap: {swap.total / (1024**3):.2f} GB")
        print(f"Used Swap: {swap.used / (1024**3):.2f} GB")
        print(f"Swap Usage: {swap.percent:.1f}%")
        
    except Exception as e:
        print(f"Error getting memory info: {e}")

def get_disk_info():
    """Get disk information."""
    print(f"\n{get_separator()}")
    print("DISK INFORMATION")
    print(get_separator())
    
    try:
        partitions = psutil.disk_partitions()
        for partition in partitions:
            print(f"\nDevice: {partition.device}")
            print(f"Mountpoint: {partition.mountpoint}")
            print(f"File System: {partition.fstype}")
            
            try:
                partition_usage = psutil.disk_usage(partition.mountpoint)
                print(f"  Total Size: {partition_usage.total / (1024**3):.2f} GB")
                print(f"  Used: {partition_usage.used / (1024**3):.2f} GB")
                print(f"  Free: {partition_usage.free / (1024**3):.2f} GB")
                print(f"  Usage: {(partition_usage.used / partition_usage.total) * 100:.1f}%")
            except PermissionError:
                print("  Permission denied")
                
    except Exception as e:
        print(f"Error getting disk info: {e}")

def get_network_info():
    """Get network information."""
    print(f"\n{get_separator()}")
    print("NETWORK INFORMATION")
    print(get_separator())
    
    try:
        # Network interfaces
        print("Network Interfaces:")
        for interface_name, interface_addresses in psutil.net_if_addrs().items():
            has_addresses = False
            interface_info = []
            
            for address in interface_addresses:
                if address.family == socket.AF_INET:  # IPv4
                    interface_info.append(f"  IPv4: {address.address}")
                    if address.netmask:
                        interface_info.append(f"    Netmask: {address.netmask}")
                    if address.broadcast:
                        interface_info.append(f"    Broadcast: {address.broadcast}")
                    has_addresses = True
                elif address.family == socket.AF_INET6:  # IPv6
                    interface_info.append(f"  IPv6: {address.address}")
                    has_addresses = True
                elif hasattr(socket, 'AF_LINK') and address.family == socket.AF_LINK:  # MAC Address
                    if address.address and address.address != '00:00:00:00:00:00':
                        interface_info.append(f"  MAC: {address.address}")
                        has_addresses = True
            
            if has_addresses:
                print(f"\n{interface_name}:")
                for info in interface_info:
                    print(info)
        
        # Network statistics
        net_io = psutil.net_io_counters()
        print(f"\nNetwork Statistics:")
        print(f"Bytes Sent: {net_io.bytes_sent / (1024**2):.2f} MB")
        print(f"Bytes Received: {net_io.bytes_recv / (1024**2):.2f} MB")
        print(f"Packets Sent: {net_io.packets_sent}")
        print(f"Packets Received: {net_io.packets_recv}")
        
        # Network interface statistics
        net_if_stats = psutil.net_if_stats()
        print(f"\nInterface Statistics:")
        for interface, stats in net_if_stats.items():
            if stats.isup:
                print(f"{interface}: UP (Speed: {stats.speed} Mbps, MTU: {stats.mtu})")
        
    except Exception as e:
        print(f"Error getting network info: {e}")

def get_external_ip():
    """Get external IP address."""
    print(f"\n{get_separator('-')}")
    print("EXTERNAL NETWORK INFORMATION")
    print(get_separator('-'))
    
    try:
        import requests
        
        # Get external IP
        response = requests.get('https://httpbin.org/ip', timeout=10)
        if response.status_code == 200:
            ip_data = response.json()
            print(f"External IP Address: {ip_data['origin']}")
        
        # Get location info
        response = requests.get('https://ipinfo.io/json', timeout=10)
        if response.status_code == 200:
            location_data = response.json()
            print(f"Location: {location_data.get('city', 'Unknown')}, {location_data.get('region', 'Unknown')}, {location_data.get('country', 'Unknown')}")
            print(f"ISP: {location_data.get('org', 'Unknown')}")
            print(f"Timezone: {location_data.get('timezone', 'Unknown')}")
            
    except ImportError:
        print("Install 'requests' library for external IP info: pip install requests")
    except Exception as e:
        print(f"Error getting external IP: {e}")

def get_running_processes():
    """Get top running processes."""
    print(f"\n{get_separator()}")
    print("TOP 10 PROCESSES (by CPU usage)")
    print(get_separator())
    
    try:
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
            try:
                processes.append(proc.info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        # Sort by CPU usage
        processes.sort(key=lambda x: x['cpu_percent'] or 0, reverse=True)
        
        print(f"{'PID':<8} {'Name':<25} {'CPU %':<8} {'Memory %':<10}")
        print("-" * 60)
        
        for proc in processes[:10]:
            cpu_percent = proc['cpu_percent'] or 0
            memory_percent = proc['memory_percent'] or 0
            name = proc['name'][:24] if proc['name'] else 'Unknown'
            print(f"{proc['pid']:<8} {name:<25} {cpu_percent:<8.1f} {memory_percent:<10.1f}")
            
    except Exception as e:
        print(f"Error getting process info: {e}")

def get_user_info():
    """Get user and session information."""
    print(f"\n{get_separator()}")
    print("USER INFORMATION")
    print(get_separator())
    
    try:
        print(f"Username: {getpass.getuser()}")
        print(f"Home Directory: {os.path.expanduser('~')}")
        print(f"Current Working Directory: {os.getcwd()}")
        print(f"Python Version: {sys.version}")
        print(f"Python Executable: {sys.executable}")
        
        # Boot time
        boot_time = psutil.boot_time()
        boot_time_formatted = datetime.fromtimestamp(boot_time).strftime("%Y-%m-%d %H:%M:%S")
        print(f"System Boot Time: {boot_time_formatted}")
        
        # Current time
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"Current Time: {current_time}")
        
    except Exception as e:
        print(f"Error getting user info: {e}")

def get_battery_info():
    """Get battery information (if available)."""
    try:
        battery = psutil.sensors_battery()
        if battery:
            print(f"\n{get_separator()}")
            print("BATTERY INFORMATION")
            print(get_separator())
            
            print(f"Battery Percentage: {battery.percent:.1f}%")
            print(f"Power Plugged: {'Yes' if battery.power_plugged else 'No'}")
            
            if battery.secsleft != psutil.POWER_TIME_UNLIMITED:
                hours, remainder = divmod(battery.secsleft, 3600)
                minutes, _ = divmod(remainder, 60)
                print(f"Time Left: {int(hours)}h {int(minutes)}m")
                
    except Exception as e:
        pass  # Battery info not available on all systems

def main():
    """Main function to display all system information."""
    print(f"\n{get_separator('*')}")
    print("COMPREHENSIVE SYSTEM INFORMATION REPORT")
    print(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(get_separator('*'))
    
    # Get all information
    get_device_info()
    get_cpu_info()
    get_memory_info()
    get_disk_info()
    get_network_info()
    get_external_ip()
    get_battery_info()
    get_user_info()
    get_running_processes()
    
    print(f"\n{get_separator('*')}")
    print("REPORT COMPLETE")
    print(get_separator('*'))

if __name__ == "__main__":
    main()