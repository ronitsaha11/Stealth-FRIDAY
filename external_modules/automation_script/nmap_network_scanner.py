#!/usr/bin/env python3
"""
Comprehensive Network Scanner using Nmap
A Python wrapper for Nmap with detailed reporting and analysis.

IMPORTANT: Only use this script on networks you own or have explicit permission to scan.
Unauthorized network scanning may be illegal and violate terms of service.
"""

import subprocess
import json
import xml.etree.ElementTree as ET
import os
import sys
import argparse
from datetime import datetime
import socket
import ipaddress

class NetworkScanner:
    def __init__(self):
        self.scan_results = {}
        self.start_time = datetime.now()
        
    def check_nmap_installation(self):
        """Check if Nmap is installed on the system."""
        try:
            result = subprocess.run(['nmap', '--version'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                version_info = result.stdout.split('\n')[0]
                print(f"✅ Nmap found: {version_info}")
                return True
            else:
                return False
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def install_nmap_instructions(self):
        """Provide installation instructions for Nmap."""
        print("\n❌ Nmap not found. Please install Nmap first:")
        print("\n📦 Installation Instructions:")
        print("  macOS (Homebrew): brew install nmap")
        print("  macOS (MacPorts): sudo port install nmap")
        print("  Ubuntu/Debian: sudo apt-get install nmap")
        print("  CentOS/RHEL: sudo yum install nmap")
        print("  Windows: Download from https://nmap.org/download.html")
        print("\n🔗 Official website: https://nmap.org/")
        
    def get_local_network_info(self):
        """Get information about the local network."""
        print(f"\n{'='*60}")
        print("LOCAL NETWORK INFORMATION")
        print('='*60)
        
        try:
            # Get hostname and local IP
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
            print(f"Hostname: {hostname}")
            print(f"Local IP: {local_ip}")
            
            # Try to get more accurate local IP
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(("8.8.8.8", 80))
                actual_local_ip = s.getsockname()[0]
                if actual_local_ip != local_ip:
                    print(f"Actual Local IP: {actual_local_ip}")
                    local_ip = actual_local_ip
            
            # Calculate network range
            try:
                network = ipaddress.IPv4Network(f"{local_ip}/24", strict=False)
                print(f"Network Range: {network}")
                return str(network)
            except:
                return f"{'.'.join(local_ip.split('.')[:-1])}.0/24"
                
        except Exception as e:
            print(f"Error getting network info: {e}")
            return "192.168.1.0/24"  # Default fallback
    
    def basic_host_discovery(self, target):
        """Perform basic host discovery scan."""
        print(f"\n🔍 BASIC HOST DISCOVERY")
        print("-" * 40)
        print(f"Target: {target}")
        
        try:
            cmd = ['nmap', '-sn', target]
            print(f"Command: {' '.join(cmd)}")
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                print("\n📋 Results:")
                print(result.stdout)
                
                # Parse results for live hosts
                lines = result.stdout.split('\n')
                live_hosts = []
                for line in lines:
                    if 'Nmap scan report for' in line:
                        host = line.split('for ')[1].strip()
                        if '(' in host:
                            host = host.split('(')[1].rstrip(')')
                        live_hosts.append(host)
                
                self.scan_results['host_discovery'] = {
                    'live_hosts': live_hosts,
                    'host_count': len(live_hosts),
                    'raw_output': result.stdout
                }
                
                print(f"\n✅ Found {len(live_hosts)} live hosts")
                return live_hosts
            else:
                print(f"❌ Scan failed: {result.stderr}")
                return []
                
        except subprocess.TimeoutExpired:
            print("⏱️ Scan timed out")
            return []
        except Exception as e:
            print(f"❌ Error during host discovery: {e}")
            return []
    
    def port_scan(self, target, scan_type='quick'):
        """Perform port scanning on target."""
        print(f"\n🔍 PORT SCANNING")
        print("-" * 40)
        print(f"Target: {target}")
        print(f"Scan Type: {scan_type}")
        
        # Define scan parameters
        scan_configs = {
            'quick': ['-T4', '--top-ports', '1000'],
            'common': ['-T4', '--top-ports', '2000'],
            'comprehensive': ['-T4', '-p-'],
            'stealth': ['-sS', '-T2', '--top-ports', '1000'],
            'udp': ['-sU', '--top-ports', '100']
        }
        
        if scan_type not in scan_configs:
            scan_type = 'quick'
            
        try:
            # Check if running as root for OS detection
            import os
            if os.geteuid() == 0:
                cmd = ['nmap'] + scan_configs[scan_type] + ['-sV', '-O', target]
            else:
                cmd = ['nmap'] + scan_configs[scan_type] + ['-sV', target]
                print("ℹ️  Running without OS detection (requires root privileges)")
            
            print(f"Command: {' '.join(cmd)}")
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            
            if result.returncode == 0:
                print("\n📋 Results:")
                print(result.stdout)
                
                self.scan_results['port_scan'] = {
                    'target': target,
                    'scan_type': scan_type,
                    'raw_output': result.stdout
                }
                
                # Parse open ports
                open_ports = []
                lines = result.stdout.split('\n')
                for line in lines:
                    if '/tcp' in line and 'open' in line:
                        port_info = line.strip()
                        open_ports.append(port_info)
                
                self.scan_results['port_scan']['open_ports'] = open_ports
                print(f"\n✅ Found {len(open_ports)} open ports")
                
            else:
                print(f"❌ Port scan failed: {result.stderr}")
                
        except subprocess.TimeoutExpired:
            print("⏱️ Port scan timed out")
        except Exception as e:
            print(f"❌ Error during port scan: {e}")
    
    def service_version_detection(self, target):
        """Perform service version detection."""
        print(f"\n🔍 SERVICE VERSION DETECTION")
        print("-" * 40)
        
        try:
            cmd = ['nmap', '-sV', '-sC', '--version-all', target]
            print(f"Command: {' '.join(cmd)}")
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            
            if result.returncode == 0:
                print("\n📋 Results:")
                print(result.stdout)
                
                self.scan_results['service_detection'] = {
                    'target': target,
                    'raw_output': result.stdout
                }
                
            else:
                print(f"❌ Service detection failed: {result.stderr}")
                
        except subprocess.TimeoutExpired:
            print("⏱️ Service detection timed out")
        except Exception as e:
            print(f"❌ Error during service detection: {e}")
    
    def os_detection(self, target):
        """Perform OS detection."""
        print(f"\n🔍 OS DETECTION")
        print("-" * 40)
        
        try:
            cmd = ['nmap', '-O', '--osscan-guess', target]
            print(f"Command: {' '.join(cmd)}")
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                print("\n📋 Results:")
                print(result.stdout)
                
                self.scan_results['os_detection'] = {
                    'target': target,
                    'raw_output': result.stdout
                }
                
            else:
                print(f"❌ OS detection failed: {result.stderr}")
                print("Note: OS detection requires root privileges and may not work on all targets")
                
        except subprocess.TimeoutExpired:
            print("⏱️ OS detection timed out")
        except Exception as e:
            print(f"❌ Error during OS detection: {e}")
    
    def vulnerability_scan(self, target):
        """Perform basic vulnerability scanning using NSE scripts."""
        print(f"\n🔍 VULNERABILITY SCANNING")
        print("-" * 40)
        
        try:
            cmd = ['nmap', '--script', 'vuln', target]
            print(f"Command: {' '.join(cmd)}")
            print("⚠️  This may take several minutes...")
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=900)
            
            if result.returncode == 0:
                print("\n📋 Results:")
                print(result.stdout)
                
                self.scan_results['vulnerability_scan'] = {
                    'target': target,
                    'raw_output': result.stdout
                }
                
            else:
                print(f"❌ Vulnerability scan failed: {result.stderr}")
                
        except subprocess.TimeoutExpired:
            print("⏱️ Vulnerability scan timed out")
        except Exception as e:
            print(f"❌ Error during vulnerability scan: {e}")
    
    def save_results(self, filename=None):
        """Save scan results to a file."""
        if not filename:
            timestamp = self.start_time.strftime("%Y%m%d_%H%M%S")
            filename = f"nmap_scan_results_{timestamp}.json"
        
        try:
            with open(filename, 'w') as f:
                json.dump(self.scan_results, f, indent=2, default=str)
            
            print(f"\n💾 Results saved to: {filename}")
            return filename
            
        except Exception as e:
            print(f"❌ Error saving results: {e}")
            return None
    
    def generate_summary(self):
        """Generate a summary of scan results."""
        print(f"\n{'='*60}")
        print("SCAN SUMMARY")
        print('='*60)
        
        end_time = datetime.now()
        duration = end_time - self.start_time
        
        print(f"Scan Duration: {duration}")
        print(f"Start Time: {self.start_time}")
        print(f"End Time: {end_time}")
        
        if 'host_discovery' in self.scan_results:
            host_count = self.scan_results['host_discovery']['host_count']
            print(f"Live Hosts Found: {host_count}")
            
        if 'port_scan' in self.scan_results:
            open_ports = len(self.scan_results['port_scan'].get('open_ports', []))
            print(f"Open Ports Found: {open_ports}")
        
        print(f"\nScans Performed:")
        for scan_type in self.scan_results.keys():
            print(f"  ✅ {scan_type.replace('_', ' ').title()}")

def main():
    parser = argparse.ArgumentParser(description='Comprehensive Network Scanner using Nmap')
    parser.add_argument('target', nargs='?', help='Target IP, hostname, or network range')
    parser.add_argument('--scan-type', choices=['quick', 'common', 'comprehensive', 'stealth', 'udp'], 
                        default='quick', help='Type of port scan to perform')
    parser.add_argument('--host-discovery', action='store_true', help='Perform host discovery only')
    parser.add_argument('--port-scan', action='store_true', help='Perform port scanning')
    parser.add_argument('--service-detection', action='store_true', help='Perform service version detection')
    parser.add_argument('--os-detection', action='store_true', help='Perform OS detection')
    parser.add_argument('--vulnerability-scan', action='store_true', help='Perform vulnerability scanning')
    parser.add_argument('--all', action='store_true', help='Perform all scan types')
    parser.add_argument('--output', help='Output file for results')
    
    args = parser.parse_args()
    
    # Display banner and warnings
    print(f"\n{'='*60}")
    print("🛡️  COMPREHENSIVE NETWORK SCANNER")
    print('='*60)
    print("⚠️  IMPORTANT LEGAL NOTICE:")
    print("   Only use this tool on networks you own or have explicit permission to scan.")
    print("   Unauthorized scanning may be illegal and violate terms of service.")
    print('='*60)
    
    scanner = NetworkScanner()
    
    # Check if Nmap is installed
    if not scanner.check_nmap_installation():
        scanner.install_nmap_instructions()
        sys.exit(1)
    
    # Get target
    if not args.target:
        network_range = scanner.get_local_network_info()
        print(f"\n🎯 No target specified. Using local network: {network_range}")
        target = network_range
        
        # Ask for confirmation
        response = input("\nProceed with local network scan? (y/N): ").lower()
        if response != 'y':
            print("Scan cancelled.")
            sys.exit(0)
    else:
        target = args.target
    
    print(f"\n🎯 Target: {target}")
    
    # Determine which scans to perform
    if args.all:
        perform_host_discovery = True
        perform_port_scan = True
        perform_service_detection = True
        perform_os_detection = True
        perform_vulnerability_scan = True
    else:
        perform_host_discovery = args.host_discovery
        perform_port_scan = args.port_scan
        perform_service_detection = args.service_detection
        perform_os_detection = args.os_detection
        perform_vulnerability_scan = args.vulnerability_scan
        
        # If no specific scans selected, do basic scans
        if not any([perform_host_discovery, perform_port_scan, perform_service_detection, 
                   perform_os_detection, perform_vulnerability_scan]):
            perform_host_discovery = True
            perform_port_scan = True
    
    # Perform scans
    try:
        if perform_host_discovery:
            live_hosts = scanner.basic_host_discovery(target)
            
            # If scanning a network range, ask which hosts to scan further
            if '/' in target and len(live_hosts) > 1 and (perform_port_scan or perform_service_detection):
                print(f"\nFound {len(live_hosts)} live hosts:")
                for i, host in enumerate(live_hosts):
                    print(f"  {i+1}. {host}")
                
                choice = input("\nEnter host number for detailed scan (or 'all' for all hosts): ").lower()
                if choice == 'all':
                    selected_hosts = live_hosts
                elif choice.isdigit() and 1 <= int(choice) <= len(live_hosts):
                    selected_hosts = [live_hosts[int(choice)-1]]
                else:
                    print("Invalid choice. Scanning first host only.")
                    selected_hosts = [live_hosts[0]] if live_hosts else []
            else:
                selected_hosts = [target]
        else:
            selected_hosts = [target]
        
        # Perform detailed scans on selected hosts
        for host in selected_hosts:
            if perform_port_scan:
                scanner.port_scan(host, args.scan_type)
            
            if perform_service_detection:
                scanner.service_version_detection(host)
            
            if perform_os_detection:
                scanner.os_detection(host)
            
            if perform_vulnerability_scan:
                scanner.vulnerability_scan(host)
        
        # Generate summary and save results
        scanner.generate_summary()
        
        if args.output:
            scanner.save_results(args.output)
        else:
            scanner.save_results()
            
    except KeyboardInterrupt:
        print("\n\n⚡ Scan interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")

if __name__ == "__main__":
    main()