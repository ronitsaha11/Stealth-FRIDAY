import sys
import os

# Add external_modules to path to allow direct importing
current_dir = os.path.dirname(os.path.abspath(__file__))
repo_root = os.path.abspath(os.path.join(current_dir, "../../../"))
external_dir = os.path.join(repo_root, "external_modules", "automation_script")

if external_dir not in sys.path:
    sys.path.append(external_dir)

from url_opener_vpn_advanced import (
    get_current_ip,
    open_urls_in_chrome,
    close_chrome_tabs,
    inject_fingerprint_randomization,
    comprehensive_session_rotation
)

def get_public_ip() -> dict:
    """
    Returns the current public IP address.
    """
    try:
        ip = get_current_ip()
        if ip:
            return {"status": "success", "source": "automation_engine_browser", "ip": ip}
        return {"status": "error", "source": "automation_engine_browser", "error_message": "Could not determine public IP"}
    except Exception as e:
        return {"status": "error", "source": "automation_engine_browser", "error_message": str(e)}

def rotate_browser_session() -> dict:
    """
    Clears Chrome data, changes fingerprints, rotates session, and checks IP change.
    Patches input() to avoid hanging the agent on manual VPN prompts.
    """
    import builtins
    original_input = builtins.input
    builtins.input = lambda prompt: 'y' # auto-confirm VPN activation prompts
    
    try:
        new_ip = comprehensive_session_rotation()
        if new_ip:
            return {
                "status": "success",
                "source": "automation_engine_browser",
                "message": "Session rotated.",
                "current_ip": str(new_ip)
            }
        return {
            "status": "warning",
            "source": "automation_engine_browser",
            "message": "Session rotation failed or IP did not change."
        }
    except Exception as e:
        return {"status": "error", "source": "automation_engine_browser", "error_message": str(e)}
    finally:
        builtins.input = original_input

def open_urls(urls: list) -> dict:
    """
    Opens a list of URLs in Google Chrome.
    """
    try:
        open_urls_in_chrome(urls)
        return {"status": "success", "source": "automation_engine_browser", "message": f"Opened {len(urls)} URLs."}
    except Exception as e:
        return {"status": "error", "source": "automation_engine_browser", "error_message": str(e)}

def close_tabs() -> dict:
    """
    Closes specific automation tabs.
    """
    try:
        close_chrome_tabs()
        return {"status": "success", "source": "automation_engine_browser", "message": "Closed matching tabs."}
    except Exception as e:
        return {"status": "error", "source": "automation_engine_browser", "error_message": str(e)}

def inject_fingerprint() -> dict:
    """
    Injects JS to randomize browser fingerprints.
    """
    try:
        success = inject_fingerprint_randomization()
        if success:
            return {"status": "success", "source": "automation_engine_browser", "message": "Injected random fingerprint."}
        return {"status": "error", "source": "automation_engine_browser", "error_message": "Failed to inject fingerprint."}
    except Exception as e:
        return {"status": "error", "source": "automation_engine_browser", "error_message": str(e)}
