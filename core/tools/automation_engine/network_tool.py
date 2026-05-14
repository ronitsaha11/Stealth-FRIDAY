import sys
import os

# Add external_modules to path to allow direct importing
current_dir = os.path.dirname(os.path.abspath(__file__))
repo_root = os.path.abspath(os.path.join(current_dir, "../../../"))
external_dir = os.path.join(repo_root, "external_modules", "automation_script")

if external_dir not in sys.path:
    sys.path.append(external_dir)

from nmap_network_scanner import NetworkScanner

def scan_network(target: str = None, scan_types: list = None) -> dict:
    """
    Programmatically utilizes NetworkScanner from the external automation script 
    to scan a target network/IP and return structured JSON results.
    
    Args:
        target (str, optional): The IP, range, or hostname to scan. If None, it attempts local network.
        scan_types (list, optional): Types of scans to perform. 
                                     Valid options: 'host_discovery', 'port_scan', 
                                     'service_detection', 'os_detection', 'vulnerability_scan'.
                                     Defaults to ['host_discovery', 'port_scan'].
    
    Returns:
        dict: A structured dictionary of the scan results.
    """
    try:
        scanner = NetworkScanner()
        
        # Ensure Nmap is installed
        if not scanner.check_nmap_installation():
            return {
                "status": "error",
                "source": "automation_engine_network",
                "error_message": "Nmap is not installed or not found in system PATH."
            }
            
        # Determine target
        if not target:
            target = scanner.get_local_network_info()
            
        if not scan_types:
            scan_types = ['host_discovery', 'port_scan']
            
        # Execute selected scans programmatically (avoids interactive prompts)
        if 'host_discovery' in scan_types:
            scanner.basic_host_discovery(target)
            
        if 'port_scan' in scan_types:
            scanner.port_scan(target, scan_type='quick')
            
        if 'service_detection' in scan_types:
            scanner.service_version_detection(target)
            
        if 'os_detection' in scan_types:
            scanner.os_detection(target)
            
        if 'vulnerability_scan' in scan_types:
            scanner.vulnerability_scan(target)
            
        return {
            "status": "success",
            "source": "automation_engine_network",
            "target": target,
            "data": scanner.scan_results
        }
        
    except Exception as e:
        return {
            "status": "error",
            "source": "automation_engine_network",
            "target": target,
            "error_message": str(e)
        }
