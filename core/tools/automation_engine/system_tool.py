import sys
import os
import subprocess

# Add external_modules to path to allow importing if needed in the future
current_dir = os.path.dirname(os.path.abspath(__file__))
repo_root = os.path.abspath(os.path.join(current_dir, "../../../"))
external_dir = os.path.join(repo_root, "external_modules", "automation_script")

if external_dir not in sys.path:
    sys.path.append(external_dir)

def get_system_info() -> dict:
    """
    Executes the external system_info script, captures its output, 
    and returns a structured JSON-serializable dictionary.
    
    Returns:
        dict: A dictionary containing the execution status and raw system info.
    """
    script_path = os.path.join(external_dir, "system_info.py")
    
    try:
        # We run this in a subprocess to avoid cluttering stdout with its prints
        # and safely capture everything.
        result = subprocess.run(
            [sys.executable, script_path],
            capture_output=True,
            text=True,
            check=True
        )
        
        return {
            "status": "success",
            "source": "automation_engine_system_info",
            "raw_output": result.stdout
        }
    except subprocess.CalledProcessError as e:
        return {
            "status": "error",
            "source": "automation_engine_system_info",
            "error_message": str(e),
            "raw_output": e.stdout,
            "raw_error": e.stderr
        }
    except Exception as e:
        return {
            "status": "error",
            "source": "automation_engine_system_info",
            "error_message": str(e)
        }
